import os
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

# Imports dos Modelos (incluindo Vídeo)
from .models import (
    Noticia,
    Voto,
    Assunto,
    Salvo,
    Enquete,
    OpcaoEnquete,
    VotoEnquete,
    Video,
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
        logger.info(
            "Onboarding: Perfil não encontrado; preferências não persistidas em model."
        )
        return

    perfil, _ = Perfil.objects.get_or_create(user=user)

    # Flag de identificação pública (se existir)
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


def _build_resumo_text(noticia: Noticia) -> str:
    """
    Retorna APENAS o resumo gerado pela IA (Gemini).

    - Sempre delega para `gerar_resumo_automatico`, que:
      * usa o campo `noticia.resumo` como cache do resumo da IA;
      * chama a API apenas se ainda não houver resumo salvo.
    - Se não for possível gerar (erro de API, quota, etc.), retorna string vazia.
    """
    try:
        resumo = gerar_resumo_automatico(noticia)
    except Exception:
        logger.exception(
            "Erro ao tentar gerar resumo automático via Gemini para notícia %s",
            noticia.pk,
        )
        resumo = None

    return (resumo or "").strip()


# =======================
# HOME (VIEW PRINCIPAL)
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

    # 1) Destaques
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
            request.user,
        )[:3]
    destaques_ids = list(destaques.values_list("id", flat=True))

    # 2) Para você (recomendações)
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

        assuntos_interesse = (
            Assunto.objects.filter(
                noticias__votos__usuario=request.user,
                noticias__votos__valor=1,
            )
            .values_list("pk", flat=True)
            .distinct()
        )

        assuntos_salvos = (
            Assunto.objects.filter(
                noticias__salvo__usuario=request.user,
            )
            .values_list("pk", flat=True)
            .distinct()
        )

        assuntos_ids = set(list(assuntos_interesse) + list(assuntos_salvos))

        if assuntos_ids:
            titulo_para_voce = "Recomendações para você"
            pv_qs = (
                all_qs.filter(assuntos__id__in=assuntos_ids)
                .exclude(id__in=ids_para_excluir)
                .annotate(
                    matches_assunto=Count(
                        "assuntos",
                        filter=Q(assuntos__id__in=assuntos_ids),
                    ),
                    score=Coalesce(Sum("votos__valor"), Value(0)),
                )
                .distinct()
                .order_by(
                    "-matches_assunto",
                    "-score",
                    "-criado_em",
                )
            )
        else:
            titulo_para_voce = "Populares do momento"
            pv_qs = (
                all_qs.exclude(id__in=ids_para_excluir)
                .annotate(score=Coalesce(Sum("votos__valor"), Value(0)))
                .order_by("-score", "-criado_em")
            )
    else:
        titulo_para_voce = "Populares do momento"
        pv_qs = (
            all_qs.exclude(id__in=ids_para_excluir)
            .annotate(score=Coalesce(Sum("votos__valor"), Value(0)))
            .order_by("-score", "-criado_em")
        )

    para_voce = _annotate_is_saved(pv_qs, request.user)[:6]
    if not para_voce.exists():
        # fallback mais permissivo: não exclui destaques/votadas/salvas
        para_voce = _annotate_is_saved(
            all_qs.order_by("-criado_em"),
            request.user,
        )[:6]
        titulo_para_voce = "Destaques recentes"

    # 3) Mais lidas (7 dias, com fallback) – usando 3 itens
    since_7 = timezone.now() - timedelta(days=7)
    ml_qs = all_qs.filter(criado_em__gte=since_7).order_by(
        "-visualizacoes", "-criado_em"
    )
    mais_lidas = _annotate_is_saved(ml_qs, request.user)[:3]
    if not mais_lidas.exists():
        mais_lidas = _annotate_is_saved(
            all_qs.order_by("-criado_em"),
            request.user,
        )[:3]

    # 4) JC360
    try:
        jc360_assunto = Assunto.objects.get(slug="jc360")
        jc360_qs = all_qs.filter(assuntos=jc360_assunto)
    except Assunto.DoesNotExist:
        jc360_qs = all_qs.filter(assuntos__nome__iexact="jc360")

    jc360 = _annotate_is_saved(
        jc360_qs.order_by("-criado_em"),
        request.user,
    )[:4]
    if not jc360.exists():
        jc360 = _annotate_is_saved(
            all_qs.exclude(id__in=destaques_ids).order_by("-criado_em"),
            request.user,
        )[:4]
    if not jc360.exists():
        jc360 = _annotate_is_saved(
            all_qs.order_by("-criado_em"),
            request.user,
        )[:4]

    # 5) Vídeos (TV JC)
    # 5a) Compatibilidade antiga: notícias com assunto "videos"
    try:
        videos_assunto = Assunto.objects.get(slug="videos")
        videos_qs = all_qs.filter(assuntos=videos_assunto)
    except Assunto.DoesNotExist:
        videos_qs = all_qs.filter(assuntos__nome__iexact="videos")

    videos_noticias = _annotate_is_saved(
        videos_qs.order_by("-criado_em"),
        request.user,
    )[:4]
    if not videos_noticias.exists():
        videos_noticias = _annotate_is_saved(
            all_qs.order_by("-criado_em"),
            request.user,
        )[:4]

    # 5b) NOVO: vídeos independentes do model Video (preferencial)
    videos_tv = list(Video.objects.filter(ativo=True).order_by("-criado_em")[:4])
    if not videos_tv:
        # fallback para as notícias "videos" se não houver Video cadastrado
        videos_tv = list(videos_noticias)

    # 6) PUBLICIDADE LEGAL
    try:
        pub_assunto = Assunto.objects.get(slug="publicidade-legal")
        publicidade_qs = all_qs.filter(assuntos=pub_assunto)
    except Assunto.DoesNotExist:
        publicidade_qs = all_qs.filter(
            assuntos__nome__iexact="publicidade legal",
        )

    publicidade_legal = _annotate_is_saved(
        publicidade_qs.order_by("-criado_em"),
        request.user,
    )[:2]
    if not publicidade_legal.exists():
        publicidade_legal = _annotate_is_saved(
            all_qs.order_by("-criado_em"),
            request.user,
        )[:2]

    # 7) Pernambuco (principal + lista)
    try:
        pe_assunto = Assunto.objects.get(slug="pernambuco")
        pernambuco_qs = all_qs.filter(
            assuntos=pe_assunto,
        ).order_by("-criado_em")
    except Assunto.DoesNotExist:
        pernambuco_qs = all_qs.filter(
            assuntos__nome__iexact="pernambuco",
        ).order_by("-criado_em")

    if not pernambuco_qs.exists():
        pernambuco_qs = all_qs.order_by("-criado_em")

    pernambuco_qs = _annotate_is_saved(pernambuco_qs, request.user)
    pernambuco = pernambuco_qs.first()
    pernambuco_mais = pernambuco_qs[1:]

    # 8) Últimas notícias
    ultimas = _annotate_is_saved(
        all_qs.order_by("-criado_em"),
        request.user,
    )[:8]

    # 9) Blog do Torcedor
    try:
        blog_assunto = Assunto.objects.get(slug="blog-do-torcedor")
        blog_qs = all_qs.filter(assuntos=blog_assunto)
    except Assunto.DoesNotExist:
        blog_qs = all_qs.filter(
            assuntos__nome__iexact="blog do torcedor",
        )

    blog_torcedor = _annotate_is_saved(
        blog_qs.order_by("-criado_em"),
        request.user,
    )[:5]

    # 10) Recortes
    try:
        recortes_assunto = Assunto.objects.get(slug="recortes")
        recortes_qs = all_qs.filter(assuntos=recortes_assunto)
    except Assunto.DoesNotExist:
        recortes_qs = all_qs.filter(
            assuntos__nome__iexact="recortes",
        )

    recortes = _annotate_is_saved(
        recortes_qs.order_by("-criado_em"),
        request.user,
    )[:3]

    # 11) Receita da boa
    try:
        receita_assunto = Assunto.objects.get(slug="receita-da-boa")
        receita_qs = all_qs.filter(assuntos=receita_assunto)
    except Assunto.DoesNotExist:
        receita_qs = all_qs.filter(
            assuntos__nome__iexact="receita da boa",
        )

    receita_da_boa = _annotate_is_saved(
        receita_qs.order_by("-criado_em"),
        request.user,
    )[:4]
    if not receita_da_boa.exists():
        receita_da_boa = _annotate_is_saved(
            all_qs.order_by("-criado_em"),
            request.user,
        )[:4]

    # 12) Novela (somente notícias com assunto "Novela")
    try:
        novela_assunto = Assunto.objects.get(slug="novela")
        novela_qs = all_qs.filter(assuntos=novela_assunto)
    except Assunto.DoesNotExist:
        novela_qs = all_qs.filter(assuntos__nome__iexact="novela")

    novela = _annotate_is_saved(
        novela_qs.order_by("-criado_em"),
        request.user,
    )[:4]

    # 13) Top 3 da semana (cache)
    top3 = cache.get("top3_semana_final")
    if top3 is None:
        hoje = timezone.now().date()
        inicio = hoje - timedelta(days=6)
        top3_qs = (
            Noticia.objects.filter(criado_em__date__gte=inicio)
            .annotate(
                score_calculado=Coalesce(Sum("votos__valor"), Value(0))
                + (F("visualizacoes") * Value(0.01)),
            )
            .order_by("-score_calculado", "-criado_em")[:3]
        )
        top3 = list(top3_qs)
        cache.set("top3_semana_final", top3, 300)

    # Modal de boas-vindas
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
        "videos": videos_noticias,      # compat antigo (Noticia)
        "videos_tv": videos_tv,         # novo carrossel (Video ou fallback)
        "publicidade_legal": publicidade_legal,
        "pernambuco": pernambuco,
        "pernambuco_mais": pernambuco_mais,
        "ultimas": ultimas,
        "blog_torcedor": blog_torcedor,
        "recortes": recortes,
        "receita_da_boa": receita_da_boa,
        "novela": novela,
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

    # contabiliza visualizações
    noticia.visualizacoes = (noticia.visualizacoes or 0) + 1
    noticia.save(update_fields=["visualizacoes"])

    # resumo automático para o bloco roxo (sempre IA)
    resumo_text = _build_resumo_text(noticia)

    # relacionadas
    assuntos_ids = list(noticia.assuntos.values_list("id", flat=True))
    if assuntos_ids:
        relacionadas = (
            Noticia.objects.filter(assuntos__in=assuntos_ids)
            .exclude(pk=noticia.pk)
            .distinct()
            .order_by("-criado_em")[:2]
        )
    else:
        relacionadas = (
            Noticia.objects.exclude(pk=noticia.pk).order_by("-criado_em")[:2]
        )

    # votos
    votos_agregados = noticia.votos.aggregate(
        score_total=Coalesce(Sum("valor"), Value(0)),
        up_total=Count("id", filter=Q(valor=1)),
        down_total=Count("id", filter=Q(valor=-1)),
    )

    voto_usuario = None
    is_saved = False  # padrão
    if request.user.is_authenticated:
        voto_usuario = Voto.objects.filter(
            noticia=noticia,
            usuario=request.user,
        ).first()
        # usando o ManyToMany "salvos"
        is_saved = noticia.salvos.filter(pk=request.user.pk).exists()

    # --- LÓGICA DA ENQUETE (INÍCIO) ---
    enquete_data = None
    try:
        enquete = noticia.enquete  # type: ignore

        if enquete and enquete.titulo:
            opcoes = enquete.opcoes.all()
            total_votos_enquete = VotoEnquete.objects.filter(
                enquete=enquete,
            ).count()

            usuario_ja_votou_enquete = False
            voto_usuario_enquete_id = None

            if request.user.is_authenticated:
                usuario_ja_votou_enquete = enquete.ja_votou(request.user)
                if usuario_ja_votou_enquete:
                    voto_obj = VotoEnquete.objects.filter(
                        enquete=enquete,
                        usuario=request.user,
                    ).first()
                    voto_usuario_enquete_id = (
                        voto_obj.opcao_selecionada.id if voto_obj else None
                    )

            opcoes_com_percentual = []
            for op in opcoes:
                votos_da_opcao = op.total_votos
                percentual = (
                    votos_da_opcao / total_votos_enquete * 100
                    if total_votos_enquete > 0
                    else 0
                )
                opcoes_com_percentual.append(
                    {
                        "id": op.id,
                        "texto": op.texto,
                        "votos": votos_da_opcao,
                        "percentual": round(percentual, 1),
                    }
                )

            enquete_data = {
                "obj": enquete,
                "opcoes": opcoes_com_percentual,
                "total_votos": total_votos_enquete,
                "usuario_ja_votou": usuario_ja_votou_enquete,
                "voto_usuario_id": voto_usuario_enquete_id,
            }

    except Enquete.DoesNotExist:
        enquete_data = None
    except Exception as e:
        logger.error(f"Erro ao processar enquete para notícia {pk}: {e}")
        enquete_data = None
    # --- LÓGICA DA ENQUETE (FIM) ---

    ctx = {
        "noticia": noticia,
        "score": votos_agregados["score_total"],
        "up": votos_agregados["up_total"],
        "down": votos_agregados["down_total"],
        "voto_usuario": voto_usuario.valor if voto_usuario else 0,
        "relacionadas": relacionadas,
        "is_saved": is_saved,
        "enquete_data": enquete_data,
        "resumo_text": resumo_text,
    }
    return render(request, "noticias/detalhe.html", ctx)


# =======================
# VOTO (AJAX) - UP/DOWN
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
        noticia=noticia,
        usuario=request.user,
        defaults={"valor": valor},
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
        post_log = {
            k: ("***" if "password" in k else v) for k, v in post_dict.items()
        }
        logger.info("POST /signup payload: %s", post_log)

        nome = (request.POST.get("nome") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        data_nascimento = (request.POST.get("data_nascimento") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

        terms_vals = request.POST.getlist("terms")
        terms_ok = "on" in terms_vals

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
                    user=user,
                    defaults={"data_nascimento": data_nascimento or None},
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
# ONBOARDING / PERSONALIZAÇÃO
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
        identificacao = (request.POST.get("identificacao") or "").strip()
        assuntos_ids = request.POST.getlist("assuntos")
        terms_ok = request.POST.get("terms") == "on"

        errors = {}
        if identificacao not in {"anonimo", "nome"}:
            errors["identificacao"] = "Selecione como deseja ser identificado."
        if not assuntos_ids:
            errors["assuntos"] = "Selecione ao menos um assunto."
        if not terms_ok:
            errors["terms"] = "É necessário concordar com os Termos de Uso."

        if errors:
            assuntos = Assunto.objects.all().order_by("nome")[:30]
            return render(
                request,
                "noticias/onboarding_personalizacao.html",
                {
                    "assuntos": assuntos,
                    "errors": errors,
                    "selecionados": set(map(int, assuntos_ids)),
                },
            )

        _persistir_preferencias_no_perfil(
            request.user,
            identificacao,
            [int(x) for x in assuntos_ids],
        )

        messages.success(request, "Preferências salvas! Personalização concluída.")
        return redirect("noticias:index")

    assuntos = Assunto.objects.all().order_by("nome")[:30]
    return render(
        request,
        "noticias/onboarding_personalizacao.html",
        {"assuntos": assuntos},
    )


# =======================
# RESUMO (Gemini)
# =======================


def gerar_resumo_automatico(noticia: Noticia) -> str | None:
    """
    Gera um resumo automático para a notícia usando o Gemini.

    - Usa o campo `noticia.resumo` como **cache** do resumo da IA:
      * Se já houver texto, só devolve (não chama a API de novo).
      * Se estiver vazio, chama o Gemini, salva em `noticia.resumo` e retorna.
    - Em caso de erro ou falta de configuração, retorna None.
    """
    # Cache local: se já existir algum resumo salvo, apenas reutiliza.
    existente = (getattr(noticia, "resumo", "") or "").strip()
    if existente:
        return existente

    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv(
        "GEMINI_API_KEY", ""
    )
    if not api_key:
        logger.warning(
            "GEMINI_API_KEY não configurada; resumo automático não será gerado."
        )
        return None

    try:
        import google.generativeai as genai
    except Exception:
        logger.warning(
            "Biblioteca google-generativeai não instalada; resumo automático desativado."
        )
        return None

    try:
        genai.configure(api_key=api_key)  # type: ignore
        model = genai.GenerativeModel("gemini-flash-latest")  # type: ignore

        prompt = f"""
        Você é um assistente de jornalismo do Jornal do Commercio.
        Resuma a notícia abaixo de forma clara, objetiva e em português,
        em até 2 frases curtas, sem opinião.

        <noticia>
        Título: {noticia.titulo}
        Conteúdo: {noticia.conteudo}
        </noticia>
        """

        response = model.generate_content(prompt)
        resumo = (getattr(response, "text", "") or "").strip()
        if not resumo:
            return None

        noticia.resumo = resumo
        noticia.save(update_fields=["resumo"])
        return resumo
    except Exception as e:  # pragma: no cover
        logger.exception(
            "Erro ao gerar resumo automático para notícia %s: %s", noticia.pk, e
        )
        return None


@login_required
def resumir_noticia(request, pk):
    """
    Mantida por compatibilidade com o endpoint antigo de resumo via AJAX.
    Agora reutiliza o helper gerar_resumo_automatico.
    """
    noticia = get_object_or_404(Noticia, pk=pk)
    resumo = gerar_resumo_automatico(noticia)

    if not resumo:
        return JsonResponse(
            {
                "error": "Não foi possível gerar o resumo da notícia.",
            },
            status=500,
        )

    return JsonResponse({"resumo": resumo})


# ==================================================
# VOTAÇÃO DA ENQUETE
# ==================================================


@login_required
@require_http_methods(["POST"])
def votar_enquete(request, enquete_pk):
    """
    Registra o voto de um usuário em uma opção de enquete.
    """
    enquete = get_object_or_404(Enquete, pk=enquete_pk)
    noticia = enquete.noticia

    try:
        opcao_id = request.POST.get("opcao_enquete")
        if not opcao_id:
            raise Exception("Nenhuma opção selecionada.")

        opcao_selecionada = get_object_or_404(
            OpcaoEnquete,
            pk=opcao_id,
            enquete=enquete,
        )

    except Exception as e:
        logger.warning(
            f"Tentativa de voto inválida na enquete {enquete_pk} "
            f"pelo usuário {request.user.username}: {e}"
        )
        messages.error(request, "Seleção inválida. Tente novamente.")
        return redirect(noticia.get_absolute_url())

    if enquete.ja_votou(request.user):
        messages.warning(request, "Você já votou nesta enquete.")
        return redirect(noticia.get_absolute_url())

    try:
        VotoEnquete.objects.create(
            usuario=request.user,
            enquete=enquete,
            opcao_selecionada=opcao_selecionada,
        )
        messages.success(request, "Seu voto foi registrado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao salvar VotoEnquete (possível duplicata): {e}")
        messages.warning(
            request,
            "Não foi possível registrar seu voto. Você já pode ter votado.",
        )

    return redirect(noticia.get_absolute_url())


# ==================================================
# GALERIA DE VÍDEOS INDEPENDENTES
# ==================================================


def galeria_videos(request):
    """
    Exibe a lista de vídeos independentes (YouTube ou Upload),
    sem necessidade de estarem vinculados a notícias.
    """
    videos = Video.objects.filter(ativo=True).order_by("-criado_em")
    return render(request, "noticias/galeria_videos.html", {"videos_tv": videos})


def video_detail(request, pk):
    video = get_object_or_404(Video, pk=pk)
    return render(request, "noticias/video_detail.html", {"video": video})
@login_required
def editar_perfil(request):
    user = request.user
    Perfil = _perfil_model_or_none()  # usa helper já existente no seu projeto
    perfil = None

    if Perfil:
        perfil, _ = Perfil.objects.get_or_create(user=user)

    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        senha = request.POST.get("senha", "").strip()
        data_nascimento = request.POST.get("data_nascimento", "").strip()
        anonimo = request.POST.get("anonimo") == "on"

        # --- Atualiza nome ---
        if nome:
            partes = nome.split(" ", 1)
            user.first_name = partes[0]
            user.last_name = partes[1] if len(partes) > 1 else ""
            user.save()

        # --- Atualiza email (se não existir outro igual) ---
        if email and email != user.email:
            if not get_user_model().objects.filter(email=email).exclude(pk=user.pk).exists():
                user.email = email
                user.username = email  # se seu login usa email como username
                user.save()
            else:
                messages.error(request, "Este e-mail já está em uso.")
                return redirect("noticias:editar_perfil")

        # --- Atualiza senha ---
        if senha:
            if len(senha) < 8:
                messages.error(request, "A senha deve ter ao menos 8 caracteres.")
                return redirect("noticias:editar_perfil")

            user.set_password(senha)
            user.save()
            update_session_auth_hash(request, user)  # evita logout

        # --- Atualiza Perfil ---
        if perfil:
            perfil.anonimo = anonimo

            if data_nascimento:
                perfil.data_nascimento = data_nascimento

            if "foto" in request.FILES:
                perfil.foto = request.FILES["foto"]

            perfil.save()

        messages.success(request, "Seu perfil foi atualizado com sucesso!")
        return redirect("noticias:editar_perfil")

    ctx = {"perfil": perfil}
    return render(request, "noticias/editarperfil.html", ctx)
