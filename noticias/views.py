# noticias/views.py

from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.cache import cache
from django.db.models import (Sum, Exists, OuterRef, Value, BooleanField, F, Q)
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Noticia, Voto, Assunto, Salvo
from django.conf import settings
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
import google.generativeai as genai
import os

# =======================
# FUNÇÃO AUXILIAR
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

# =======================
# HOME
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
        noticias = noticias.annotate(score=Sum("votos__valor")).order_by("-score", "-criado_em")
    else:
        noticias = noticias.order_by("-criado_em")

    noticias = _annotate_is_saved(noticias, request.user)

    # seções independentes da lista
    all_qs = Noticia.objects.all().select_related().prefetch_related("assuntos")

    # 1) Destaques
    destaques_qs = (
        all_qs.filter(imagem__isnull=False)
        .annotate(score_calculado=Sum("votos__valor", default=0) + (F("visualizacoes") * 0.01))
        .order_by("-score_calculado", "-criado_em")
    )
    destaques = _annotate_is_saved(destaques_qs, request.user)[:3]
    destaques_ids = list(destaques.values_list("id", flat=True))

    # 2) Para você
    if request.user.is_authenticated:
        assuntos_interesse = Assunto.objects.filter(
            noticias__votos__usuario=request.user
        ).values_list("pk", flat=True).distinct()
        assuntos_salvos = Assunto.objects.filter(
            noticias__salvo__usuario=request.user
        ).values_list("pk", flat=True).distinct()
        assuntos_ids = set(list(assuntos_interesse) + list(assuntos_salvos))
        if assuntos_ids:
            pv_qs = all_qs.filter(assuntos__in=assuntos_ids).exclude(id__in=destaques_ids).distinct()
        else:
            pv_qs = all_qs.exclude(id__in=destaques_ids)
    else:
        pv_qs = all_qs.exclude(id__in=destaques_ids)

    para_voce = _annotate_is_saved(pv_qs.order_by("-criado_em"), request.user)[:6]
    if not para_voce.exists():
        para_voce = _annotate_is_saved(all_qs.order_by("-criado_em"), request.user)[:6]

    # 3) Mais lidas (7 dias)
    since_7 = timezone.now() - timedelta(days=7)
    ml_qs = all_qs.filter(criado_em__gte=since_7).order_by("-visualizacoes", "-criado_em")
    mais_lidas = _annotate_is_saved(ml_qs, request.user)[:2]
    if not mais_lidas.exists():
        mais_lidas = _annotate_is_saved(all_qs.order_by("-criado_em"), request.user)[:2]

    # 4) JC360 (slug/nome) + fallbacks
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

    # 5) Vídeos (slug/nome) + fallback
    try:
        videos_assunto = Assunto.objects.get(slug="videos")
        videos_qs = all_qs.filter(assuntos=videos_assunto)
    except Assunto.DoesNotExist:
        videos_qs = all_qs.filter(assuntos__nome__iexact="videos")

    videos = _annotate_is_saved(videos_qs.order_by("-criado_em"), request.user)[:2]
    if not videos.exists():
        videos = _annotate_is_saved(all_qs.order_by("-criado_em"), request.user)[:2]

    # 6) Pernambuco (destaque único)
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
            .annotate(score_calculado=Sum("votos__valor", default=0) + (F("visualizacoes") * 0.01))
            .order_by("-score_calculado", "-criado_em")[:3]
        )
        top3 = list(top3_qs)
        cache.set("top3_semana_final", top3, 300)

    # <<< NOVO: sinal do modal de boas-vindas >>>
    show_welcome = bool(request.session.pop('show_welcome', False))

    ctx = {
        "noticias": noticias,
        "assuntos": assuntos,
        "selecionados": selecionados,
        "periodo": periodo or "",
        "sort": sort,
        "destaques": destaques,
        "para_voce": para_voce,
        "mais_lidas": mais_lidas,
        "jc360": jc360,
        "videos": videos,
        "pernambuco": pernambuco,
        "top3": top3,
        "show_welcome": show_welcome,  # <<< NOVO
    }
    return render(request, "noticias/index.html", ctx)

# =======================
# DETALHE
# =======================

def noticia_detalhe(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    noticia.visualizacoes = (noticia.visualizacoes or 0) + 1
    noticia.save(update_fields=["visualizacoes"])

    voto_usuario = None
    if request.user.is_authenticated:
        voto_usuario = Voto.objects.filter(noticia=noticia, usuario=request.user).first()
        is_saved = noticia.salvos.filter(pk=request.user.pk).exists()
    else:
        is_saved = False

    ctx = {
        "noticia": noticia,
        "score": noticia.score(),
        "up": noticia.upvotes(),
        "down": noticia.downvotes(),
        "voto_usuario": voto_usuario.valor if voto_usuario else 0,
        "is_saved": is_saved,
    }
    return render(request, "noticias/detalhe.html", ctx)

# =======================
# VOTO (AJAX)
# =======================

@login_required
def votar(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)

    if request.method != "POST":
        return redirect("noticias:noticia_detalhe", pk=pk)

    try:
        valor = int(request.POST.get("valor", 0))
        assert valor in (1, -1)
    except Exception:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Voto inválido."}, status=400)
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
        return JsonResponse({
            "up": noticia.upvotes(),
            "down": noticia.downvotes(),
            "score": noticia.score(),
            "voto_usuario": current,
        })

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
def toggle_salvo(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("Método não permitido.")

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
# SIGNUP (custom p/ seu formulário)
# =======================

def signup(request):
    """
    Recebe os campos do seu formulário:
      - nome (nome completo)
      - email
      - data_nascimento (opcional para salvar num Profile futuro)
      - password1, password2
      - checkbox de termos (terms)
    Salva nome e email no User.
    """
    User = get_user_model()
    next_url = request.GET.get("next") or request.POST.get("next") or None

    if request.method == "POST":
        nome = (request.POST.get("nome") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        data_nascimento = (request.POST.get("data_nascimento") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""
        terms = request.POST.get("terms")  # "on" se marcado

        errors = {}

        # validações básicas
        if not nome:
            errors["nome"] = "Informe seu nome completo."
        if not email:
            errors["email"] = "Informe seu e-mail."
        if password1 != password2:
            errors["password2"] = "As senhas não coincidem."
        if len(password1) < 8:
            errors["password1"] = "A senha deve ter pelo menos 8 caracteres."
        if not terms:
            errors["terms"] = "É necessário concordar com os Termos de Uso."

        # unicidade por email/username
        username = email  # simples: usamos email como username
        if email and User.objects.filter(email=email).exists():
            errors["email"] = "Este e-mail já está cadastrado."
        if username and User.objects.filter(username=username).exists():
            errors["email"] = "Este e-mail já está cadastrado."

        if errors:
            ctx = {
                "errors": errors,
                "old": {
                    "nome": nome,
                    "email": email,
                    "data_nascimento": data_nascimento,
                },
                "next": next_url,
            }
            return render(request, "registration/signup.html", ctx)

        # cria usuário
        first_name, last_name = _split_full_name(nome)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )

        # opcional: salvar DOB em um Perfil (se existir)
        try:
            from .models import Perfil  # hipotético
            Perfil.objects.update_or_create(
                user=user, defaults={"data_nascimento": data_nascimento}
            )
        except Exception:
            pass

        # login automático
        user = authenticate(username=username, password=password1)
        if user:
            auth_login(request, user)

        # <<< NOVO: sinal para abrir o modal de boas-vindas na home >>>
        request.session['show_welcome'] = True

        messages.success(request, "Conta criada com sucesso! Bem-vindo(a).")
        return redirect(next_url or "noticias:index")

    # GET
    return render(request, "registration/signup.html", {"next": next_url})

# =======================
# RESUMO (Gemini)
# =======================

@login_required
def resumir_noticia(request, pk):
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        return JsonResponse({"error": "Chave da API não encontrada."}, status=500)

    import google.generativeai as genai
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-flash-latest")

    noticia = get_object_or_404(Noticia, pk=pk)
    prompt = f"""
    Você é um assistente de jornalismo. Resuma a notícia abaixo de forma clara, objetiva e em português:
    <noticia>
    Título: {noticia.titulo}
    Conteúdo: {noticia.conteudo}
    </noticia>
    """

    try:
        response = model.generate_content(prompt)
        resumo = (getattr(response, "text", "") or "").strip()
        if resumo:
            noticia.resumo = resumo
            noticia.save(update_fields=["resumo"])
        return JsonResponse({"resumo": resumo})
    except Exception as e:
        return JsonResponse({"error": f"Erro ao conectar com a API: {e}"}, status=500)
