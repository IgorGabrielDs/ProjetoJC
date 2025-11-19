from datetime import timedelta
import json
import logging

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import (
    Sum,
    Exists,
    OuterRef,
    Value,
    BooleanField,
    F,
    Q,
    Count,
)
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

# Imports da Enquete adicionados
from .models import (
    Noticia,
    Voto,
    Assunto,
    Salvo,
    Enquete,
    OpcaoEnquete,
    VotoEnquete,
)

logger = logging.getLogger(__name__)

# =======================
# FUNÇÕES AUXILIARES
# =======================
def _annotate_is_saved(qs, user):
    """Anota se o usuário salvou a notícia."""
    if user.is_authenticated:
        return qs.annotate(
            is_saved=Exists(
                Salvo.objects.filter(usuario=user, noticia=OuterRef("pk"))
            )
        )
    return qs.annotate(is_saved=Value(False, output_field=BooleanField()))


def _split_full_name(full_name: str):
    parts = [p for p in (full_name or "").strip().split() if p]
    if not parts:
        return "", ""
    first = parts[0]
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first, last


def _perfil_model_or_none():
    """
    Retorna o model Perfil se existir (em 'noticias', 'usuarios' ou 'accounts'),
    senão retorna None. Evita import circular.
    """
    for label in ("noticias.Perfil", "usuarios.Perfil", "accounts.Perfil"):
        try:
            app_label, model_name = label.split(".")
            return apps.get_model(app_label, model_name)
        except Exception:
            continue
    return None


def _persistir_preferencias_no_perfil(user, identificacao, assuntos_ids):
    """
    Persiste escolhas do onboarding no Perfil se possível,
    mas sem quebrar caso os campos não existam.
    - identificacao: 'anonimo' | 'nome'
    - assuntos_ids: lista[str|int] de IDs de Assunto
    """
    Perfil = _perfil_model_or_none()
    if not Perfil:
        logger.info("Onboarding: Perfil não encontrado; preferências não persistidas em model.")
        return

    perfil, _ = Perfil.objects.get_or_create(user=user)

    # Flag de identificação pública (se existir)
    # exemplos de nomes de campo comuns: mostrar_nome_publico / identificacao_publica / publico
    for campo in ("mostrar_nome_publico", "identificacao_publica", "publico"):
        if hasattr(perfil, campo):
            try:
                setattr(perfil, campo, bool(identificacao == "nome"))
            except Exception:
                pass

    # Campo JSON de preferências (se existir)
    if hasattr(perfil, "preferencias"):
        try:
            prefs = perfil.preferencias or {}
            if not isinstance(prefs, dict):
                # caso prefs venha como str
                try:
                    prefs = json.loads(prefs)
                except Exception:
                    prefs = {}
            prefs["assuntos_ids"] = [int(x) for x in assuntos_ids]
            prefs["identificacao"] = identificacao
            perfil.preferencias = prefs
        except Exception as e:
            logger.warning("Falha ao gravar em perfil.preferencias: %s", e)

    # M2M direta com Assunto (se existir)
    if hasattr(perfil, "assuntos"):
        try:
            qs = Assunto.objects.filter(id__in=assuntos_ids)
            perfil.assuntos.set(qs)
        except Exception as e:
            logger.warning("Falha ao setar perfil.assuntos: %s", e)

    # Fallback para CSV (se existir)
    if hasattr(perfil, "assuntos_ids_csv"):
        try:
            csv_val = ",".join(str(i) for i in assuntos_ids)
            setattr(perfil, "assuntos_ids_csv", csv_val)
        except Exception as e:
            logger.warning("Falha ao setar perfil.assuntos_ids_csv: %s", e)

    try:
        perfil.save()
    except Exception as e:
        logger.warning("Falha ao salvar Perfil no onboarding: %s", e)


# =======================
# HOME (A VIEW PRINCIPAL)
# =======================
def index(request):
    noticias = Noticia.objects.all()
    assuntos = Assunto.objects.all()

    selecionados = request.GET.getlist("assunto")
    periodo = request.GET.get("periodo")
    sort = request.GET.get("sort", "recentes")

    # filtros/ordenação da listagem principal
    if selecionados:
        noticias = noticias.filter(assuntos__slug__in=selecionados).distinct()

    if periodo in {"24h", "7d", "30d"}:
        dias = {"24h": 1, "7d": 7, "30d": 30}[periodo]
        since = timezone.now() - timedelta(days=dias)
        noticias = noticias.filter(criado_em__gte=since)

    if sort == "populares":
        noticias = noticias.annotate(
            score=Coalesce(Sum("votos__valor"), Value(0))
        ).order_by("-score", "-criado_em")
    else:
        noticias = noticias.order_by("-criado_em")

    noticias = _annotate_is_saved(noticias, request.user)

    # seções independentes da lista
    all_qs = Noticia.objects.all().select_related().prefetch_related("assuntos")

    # 1) Destaques (com fallback caso não haja imagem)
    destaques_qs = (
        all_qs.filter(imagem__isnull=False)
        .annotate(
            score_calculado=Coalesce(Sum("votos__valor"), Value(0))
            + (F("visualizacoes") * Value(0.01))
        )
        .order_by("-score_calculado", "-criado_em")
    )
    destaques = _annotate_is_saved(destaques_qs, request.user)[:3]
    if not destaques.exists():
        destaques = _annotate_is_saved(
            all_qs.order_by("-criado_em"),
            request.user
        )[:3]
    destaques_ids = list(destaques.values_list("id", flat=True))

    # ===================================================================
    # 2) Para você (LÓGICA DE RECOMENDAÇÃO ATUALIZADA)
    # ===================================================================
    ids_para_excluir = set(destaques_ids)
    titulo_para_voce = "Populares do momento"

    if request.user.is_authenticated:
        noticias_votadas_ids = Voto.objects.filter(
            usuario=request.user
        ).values_list("noticia__id", flat=True)

        noticias_salvas_ids = Salvo.objects.filter(
            usuario=request.user
        ).values_list("noticia__id", flat=True)

        ids_para_excluir.update(noticias_votadas_ids)
        ids_para_excluir.update(noticias_salvas_ids)

        assuntos_interesse = Assunto.objects.filter(
            noticias__votos__usuario=request.user,
            noticias__votos__valor=1
        ).values_list("pk", flat=True).distinct()

        assuntos_salvos = Assunto.objects.filter(
            noticias__salvo__usuario=request.user
        ).values_list("pk", flat=True).distinct()

        assuntos_ids = set(list(assuntos_interesse) + list(assuntos_salvos))

        if assuntos_ids:
            titulo_para_voce = "Recomendações para você"
            pv_qs = all_qs.filter(
                assuntos__id__in=assuntos_ids
            ).exclude(
                id__in=ids_para_excluir
            ).annotate(
                matches_assunto=Count("assuntos", filter=Q(assuntos__id__in=assuntos_ids)),
                score=Coalesce(Sum("votos__valor"), Value(0))
            ).distinct().order_by(
                "-matches_assunto",
                "-score",
                "-criado_em",
            )
        else:
            titulo_para_voce = "Populares do momento"
            pv_qs = all_qs.exclude(
                id__in=ids_para_excluir
            ).annotate(
                score=Coalesce(Sum("votos__valor"), Value(0))
            ).order_by("-score", "-criado_em")
    else:
        titulo_para_voce = "Populares do momento"
        pv_qs = all_qs.exclude(
            id__in=ids_para_excluir
        ).annotate(
            score=Coalesce(Sum("votos__valor"), Value(0))
        ).order_by("-score", "-criado_em")

    para_voce = _annotate_is_saved(pv_qs, request.user)[:6]
    if not para_voce.exists():
        para_voce = _annotate_is_saved(
            all_qs.exclude(id__in=ids_para_excluir).order_by("-criado_em"),
            request.user
        )[:6]
        titulo_para_voce = "Destaques recentes"

    # 3) Mais lidas (7 dias, com fallback)
    since_7 = timezone.now() - timedelta(days=7)
    ml_qs = all_qs.filter(criado_em__gte=since_7).order_by("-visualizacoes", "-criado_em")
    mais_lidas = _annotate_is_saved(ml_qs, request.user)[:2]
    if not mais_lidas.exists():
        mais_lidas = _annotate_is_saved(all_qs.order_by("-criado_em"), request.user)[:2]

    # 4) JC360 (com fallbacks encadeados)
    try:
        jc360_assunto = Assunto.objects.get(slug="jc360")
        jc360_qs = all_qs.filter(assuntos=jc360_assunto)
    except Assunto.DoesNotExist:
        jc360_qs = all_qs.filter(assuntos__nome__iexact="jc360")

    jc360 = _annotate_is_saved(jc360_qs.order_by("-criado_em"), request.user)[:4]
    if not jc360.exists():
        jc360 = _annotate_is_saved(all_qs.exclude(id__in=destaques_ids).order_by("-criado_em"), request.user)[:4]
    if not jc360.exists():
        jc360 = _annotate_is_saved(all_qs.order_by("-criado_em"), request.user)[:4]

    # 5) Vídeos (com fallback)
    try:
        videos_assunto = Assunto.objects.get(slug="videos")
        videos_qs = all_qs.filter(assuntos=videos_assunto)
    except Assunto.DoesNotExist:
        videos_qs = all_qs.filter(assuntos__nome__iexact="videos")

    videos = _annotate_is_saved(videos_qs.order_by("-criado_em"), request.user)[:2]
    if not videos.exists():
        videos = _annotate_is_saved(all_qs.order_by("-criado_em"), request.user)[:2]

    # 6) Pernambuco (destaque único com fallback)
    try:
        pe_assunto = Assunto.objects.get(slug="pernambuco")
        pernambuco = all_qs.filter(assuntos=pe_assunto).order_by("-criado_em").first()
    except Assunto.DoesNotExist:
        pernambuco = all_qs.filter(assuntos__nome__iexact="pernambuco").order_by("-criado_em").first()
    if not pernambuco:
        pernambuco = all_qs.order_by("-criado_em").first()

    # 7) Top 3 da semana (cache)
    top3 = cache.get("top3_semana_final")
    if top3 is None:
        hoje = timezone.now().date()
        inicio = hoje - timedelta(days=6)
        top3_qs = (
            Noticia.objects.filter(criado_em__date__gte=inicio)
            .annotate(
                score_calculado=Coalesce(Sum("votos__valor"), Value(0))
                + (F("visualizacoes") * Value(0.01))
            )
            .order_by("-score_calculado", "-criado_em")[:3]
        )
        top3 = list(top3_qs)
        cache.set("top3_semana_final", top3, 300)

    # ===== Modal de boas-vindas (pós-cadastro) =====
    show_welcome = bool(request.session.pop("show_welcome", False))
    welcome_name = request.session.pop("welcome_name", None)
    welcome_next = request.session.pop("welcome_next", reverse("login"))

    ctx = {
        "noticias": noticias,
        "assuntos": assuntos,
        "selecionados": selecionados,
        "periodo": periodo or "",
        "sort": sort,
        "destaques": destaques,
        "para_voce": para_voce,
        "titulo_para_voce": titulo_para_voce,
        "mais_lidas": mais_lidas,
        "jc360": jc360,
        "videos": videos,
        "pernambuco": pernambuco,
        "top3": top3,
        "show_welcome": show_welcome,
        "welcome_name": welcome_name,
        "welcome_next": welcome_next,
    }
    return render(request, "noticias/index.html", ctx)


# =======================
# DETALHE
# =======================
def noticia_detalhe(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)

    noticia.visualizacoes = (noticia.visualizacoes or 0) + 1
    noticia.save(update_fields=["visualizacoes"])

    assuntos_ids = list(noticia.assuntos.values_list("id", flat=True))
    if assuntos_ids:
        relacionadas = (
            Noticia.objects
            .filter(assuntos__in=assuntos_ids)
            .exclude(pk=noticia.pk)
            .distinct()
            .order_by("-criado_em")[:2]
        )
    else:
        relacionadas = (
            Noticia.objects
            .exclude(pk=noticia.pk)
            .order_by("-criado_em")[:2]
        )

    votos_agregados = noticia.votos.aggregate(
        score_total=Coalesce(Sum("valor"), Value(0)),
        up_total=Count("id", filter=Q(valor=1)),
        down_total=Count("id", filter=Q(valor=-1)),
    )

    voto_usuario = None
    is_saved = False # Definido como False por padrão
    if request.user.is_authenticated:
        voto_usuario = Voto.objects.filter(noticia=noticia, usuario=request.user).first()
        is_saved = noticia.salvos.filter(pk=request.user.pk).exists()

    # --- LÓGICA DA ENQUETE (INÍCIO) ---
    enquete_data = None
    try:
        # noticia.enquete usa o 'related_name' que definimos no models.py
        enquete = noticia.enquete #type: ignore
        
        # Só processa se a enquete tiver sido configurada (tiver um título)
        if enquete and enquete.titulo:
            opcoes = enquete.opcoes.all()
            total_votos_enquete = VotoEnquete.objects.filter(enquete=enquete).count()
            
            usuario_ja_votou_enquete = False
            voto_usuario_enquete_id = None

            # Verifica se o usuário logado já votou
            if request.user.is_authenticated:
                # Usamos o método que criamos no models.py
                usuario_ja_votou_enquete = enquete.ja_votou(request.user)
                if usuario_ja_votou_enquete:
                    voto_obj = VotoEnquete.objects.filter(enquete=enquete, usuario=request.user).first()
                    voto_usuario_enquete_id = voto_obj.opcao_selecionada.id if voto_obj else None

            # Prepara os dados das opções com percentuais
            opcoes_com_percentual = []
            for op in opcoes:
                votos_da_opcao = op.total_votos # Usa a @property do models
                percentual = (votos_da_opcao / total_votos_enquete * 100) if total_votos_enquete > 0 else 0
                opcoes_com_percentual.append({
                    "id": op.id,
                    "texto": op.texto,
                    "votos": votos_da_opcao,
                    "percentual": round(percentual, 1) # Arredonda para 1 casa decimal
                })

            # Monta o dicionário final para o template
            enquete_data = {
                "obj": enquete, # O objeto Enquete (para o form action)
                "opcoes": opcoes_com_percentual,
                "total_votos": total_votos_enquete,
                "usuario_ja_votou": usuario_ja_votou_enquete,
                "voto_usuario_id": voto_usuario_enquete_id, # Para destacar a opção votada
            }
            
    except Enquete.DoesNotExist:
        enquete_data = None # Não há enquete para esta notícia
    except Exception as e:
        logger.error(f"Erro ao processar enquete para notícia {pk}: {e}")
        enquete_data = None # Falha segura, não quebra a página
    # --- LÓGICA DA ENQUETE (FIM) ---

    ctx = {
        "noticia": noticia,
        "score": votos_agregados["score_total"],
        "up": votos_agregados["up_total"],
        "down": votos_agregados["down_total"],
        "voto_usuario": voto_usuario.valor if voto_usuario else 0,
        "relacionadas": relacionadas,
        "is_saved": is_saved,
        "enquete_data": enquete_data, # <- NOVO DADO ADICIONADO AO CONTEXTO
    }
    return render(request, "noticias/detalhe.html", ctx)


# =======================
# VOTO (AJAX) - (Voto da Notícia, Up/Down)
# =======================
@login_required
@require_http_methods(["POST"])
def votar(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)

    try:
        valor = int(request.POST.get("valor", 0))
        assert valor in (1, -1)
    except Exception:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            votos_agregados = noticia.votos.aggregate(
                score_total=Coalesce(Sum("valor"), Value(0)),
                up_total=Count("id", filter=Q(valor=1)),
                down_total=Count("id", filter=Q(valor=-1)),
            )
            return JsonResponse(
                {
                    "error": "Voto inválido.",
                    "up": votos_agregados["up_total"],
                    "down": votos_agregados["down_total"],
                    "score": votos_agregados["score_total"],
                    "voto_usuario": 0,
                },
                status=200,
            )
        messages.error(request, "Voto inválido.")
        return redirect("noticias:noticia_detalhe", pk=pk)

    voto, created = Voto.objects.get_or_create(
        noticia=noticia, usuario=request.user, defaults={"valor": valor}
    )

    if created:
        current = valor
    else:
        if voto.valor == valor:
            voto.delete()
            current = 0
        else:
            voto.valor = valor
            voto.save()
            current = valor

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        votos_agregados = noticia.votos.aggregate(
            score_total=Coalesce(Sum("valor"), Value(0)),
            up_total=Count("id", filter=Q(valor=1)),
            down_total=Count("id", filter=Q(valor=-1)),
        )
        return JsonResponse(
            {
                "up": votos_agregados["up_total"],
                "down": votos_agregados["down_total"],
                "score": votos_agregados["score_total"],
                "voto_usuario": current,
            }
        )

    return redirect("noticias:noticia_detalhe", pk=pk)


# =======================
# SALVOS
# =======================
@login_required
def minhas_salvas(request):
    noticias = (
        Noticia.objects.filter(salvo__usuario=request.user)
        .order_by("-salvo__criado_em")
        .distinct()
    )
    return render(request, "noticias/noticias_salvas.html", {"noticias": noticias})


@login_required
@require_http_methods(["POST"])
def toggle_salvo(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    qs = Salvo.objects.filter(usuario=request.user, noticia=noticia)

    if qs.exists():
        qs.delete()
        saved = False
        label = "Ver mais tarde"
        msg = "Removido dos salvos."
    else:
        Salvo.objects.get_or_create(usuario=request.user, noticia=noticia)
        saved = True
        label = "Retirar de Ver mais tarde"
        msg = "Salvo para ler mais tarde."

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"saved": saved, "label": label})

    messages.success(request, msg)
    return redirect("noticias:noticia_detalhe", pk=pk)


# =======================
# SIGNUP (custom)
# =======================
@require_http_methods(["GET", "POST"])
def signup(request):
    """
    Recebe os campos do formulário customizado:
    - nome, email, data_nascimento, password1, password2, terms
    Cria usuário e, após sucesso, mostra o modal de boas-vindas na home.
    """
    User = get_user_model()
    next_url = request.GET.get("next") or request.POST.get("next") or None

    if request.method == "POST":
        post_dict = request.POST.dict()
        post_log = {k: ("***" if "password" in k else v) for k, v in post_dict.items()}
        logger.info("POST /signup payload: %s", post_log)

        nome = (request.POST.get("nome") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        data_nascimento = (request.POST.get("data_nascimento") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

        terms_vals = request.POST.getlist("terms")
        terms_ok = ("on" in terms_vals)

        errors = {}

        if not nome:
            errors["nome"] = "Informe seu nome completo."
        if not email:
            errors["email"] = "Informe seu e-mail."
        if password1 != password2:
            errors["password2"] = "As senhas não coincidem."
        if len(password1) < 8:
            errors["password1"] = "A senha deve ter pelo menos 8 caracteres."
        if not terms_ok:
            errors["terms"] = "É necessário concordar com os Termos de Uso."

        username = email
        if email and User.objects.filter(email=email).exists():
            errors["email"] = "Este e-mail já está cadastrado."
        if username and User.objects.filter(username=username).exists():
            errors["email"] = "Este e-mail já está cadastrado."

        if errors:
            logger.warning("Erros de validação no signup: %s", errors)
            ctx = {
                "errors": errors,
                "old": {
                    "nome": nome,
                    "email": email,
                    "data_nascimento": data_nascimento,
                    "terms": bool(terms_ok),
                },
                "next": next_url,
            }
            return render(request, "registration/signup.html", ctx)

        first_name, last_name = _split_full_name(nome)
        user = User.objects.create_user(  # type: ignore
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )

        Perfil = _perfil_model_or_none()
        if Perfil is not None:
            try:
                Perfil.objects.update_or_create(
                    user=user, defaults={"data_nascimento": data_nascimento or None}
                )
            except Exception as e:
                logger.warning("Falha ao atualizar/criar Perfil: %s", e)

        user = authenticate(username=username, password=password1)
        if user:
            auth_login(request, user)

        request.session["show_welcome"] = True
        request.session["welcome_name"] = first_name or email
        request.session["welcome_next"] = reverse("noticias:index")

        messages.success(request, "Conta criada com sucesso! Bem-vindo(a).")
        logger.info("Signup OK para %s — redirecionando para Home", email)
        return redirect("noticias:index")

    return render(request, "registration/signup.html", {"next": next_url})


# =======================
# ONBOARDING / PERSONALIZAÇÃO (pós-cadastro)
# =======================
@login_required
@require_http_methods(["GET", "POST"])
def onboarding_personalizacao(request):
    """
    Tela de personalização (após "Sim! Vamos lá." no pop-up).
    GET: exibe formulário.
    POST: valida, persiste preferências no Perfil (quando possível) e volta para a Home.
    """
    if request.method == "POST":
        identificacao = (request.POST.get("identificacao") or "").strip()  # 'anonimo' | 'nome'
        assuntos_ids = request.POST.getlist("assuntos")  # lista de ids (str)
        terms_ok = (request.POST.get("terms") == "on")

        errors = {}
        if identificacao not in {"anonimo", "nome"}:
            errors["identificacao"] = "Selecione como deseja ser identificado."
        if not assuntos_ids:
            errors["assuntos"] = "Selecione ao menos um assunto."
        if not terms_ok:
            errors["terms"] = "É necessário concordar com os Termos de Uso."

        if errors:
            # Recarrega a tela com erros (mantendo seleção)
            assuntos = Assunto.objects.all().order_by("nome")[:30]
            return render(
                request,
                "noticias/onboarding_personalizacao.html",
                {"assuntos": assuntos, "errors": errors, "selecionados": set(map(int, assuntos_ids))},
            )

        # Persistência resiliente no Perfil (se existir)
        _persistir_preferencias_no_perfil(request.user, identificacao, [int(x) for x in assuntos_ids])

        messages.success(request, "Preferências salvas! Personalização concluída.")
        return redirect("noticias:index")

    # GET
    assuntos = Assunto.objects.all().order_by("nome")[:30]
    return render(
        request,
        "noticias/onboarding_personalizacao.html",
        {"assuntos": assuntos},
    )


# =======================
# RESUMO (Gemini)
# =======================
@login_required
def resumir_noticia(request, pk):
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        return JsonResponse({"error": "Chave da API GEMINI_API_KEY não configurada no ambiente."}, status=500)

    noticia = get_object_or_404(Noticia, pk=pk)

    try:
        import google.generativeai as genai
    except Exception:
        return JsonResponse({"error": "Biblioteca google-generativeai não está instalada."}, status=500)

    try:
        genai.configure(api_key=api_key)  # type: ignore
        model = genai.GenerativeModel("gemini-flash-latest")  # type: ignore

        prompt = f"""
        Você é um assistente de jornalismo. Resuma a notícia abaixo de forma clara, objetiva e em português:
        <noticia>
        Título: {noticia.titulo}
        Conteúdo: {noticia.conteudo}
        </noticia>
        """

        response = model.generate_content(prompt)
        resumo = (getattr(response, "text", "") or "").strip()
        if resumo:
            noticia.resumo = resumo
            noticia.save(update_fields=["resumo"])
        return JsonResponse({"resumo": resumo})
    except Exception as e:
        logger.exception("Erro ao resumir notícia %s: %s", pk, e)
        return JsonResponse({"error": f"Erro ao conectar com a API: {e}"}, status=500)


# ==================================================
# NOVA VIEW - VOTAÇÃO DA ENQUETE
# ==================================================
@login_required # REQUER LOGIN: Garante que só usuários logados votem
@require_http_methods(["POST"]) # Só aceita requisições POST
def votar_enquete(request, enquete_pk):
    """
    Registra o voto de um usuário em uma opção de enquete.
    """
    # Garante que a enquete existe
    enquete = get_object_or_404(Enquete, pk=enquete_pk)
    noticia = enquete.noticia # Precisamos da notícia para redirecionar de volta
    
    try:
        # Pega o ID da opção enviada pelo formulário
        # O 'name' do input no HTML deverá ser "opcao_enquete"
        opcao_id = request.POST.get("opcao_enquete")
        if not opcao_id:
            # Se 'opcao_enquete' não veio no POST
            raise Exception("Nenhuma opção selecionada.")
            
        # Garante que a opção selecionada existe E pertence a esta enquete
        opcao_selecionada = get_object_or_404(OpcaoEnquete, pk=opcao_id, enquete=enquete)
    
    except Exception as e:
        logger.warning(f"Tentativa de voto inválida na enquete {enquete_pk} pelo usuário {request.user.username}: {e}")
        messages.error(request, "Seleção inválida. Tente novamente.")
        return redirect(noticia.get_absolute_url())

    # Verificação 1 (View): O usuário já votou?
    # Usamos o método 'ja_votou' que criamos no models.py
    if enquete.ja_votou(request.user):
        messages.warning(request, "Você já votou nesta enquete.")
        return redirect(noticia.get_absolute_url())
        
    # Se passou em tudo, cria o voto
    try:
        VotoEnquete.objects.create(
            usuario=request.user,
            enquete=enquete,
            opcao_selecionada=opcao_selecionada
        )
        messages.success(request, "Seu voto foi registrado com sucesso!")
        
    except Exception as e:
        # Verificação 2 (Database): Captura a falha do UniqueConstraint
        # Isso pode acontecer em uma 'condição de corrida' (race condition)
        logger.error(f"Erro ao salvar VotoEnquete (possível duplicata): {e}")
        messages.warning(request, "Não foi possível registrar seu voto. Você já pode ter votado.")

    # Redireciona o usuário de volta para a notícia
    return redirect(noticia.get_absolute_url())