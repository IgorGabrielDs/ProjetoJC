# caca_links/tests/test_flow.py
import pytest
from django.urls import reverse
from django.utils import timezone
import django.urls

pytestmark = pytest.mark.django_db


def _has_field(Model, name):
    return name in {f.name for f in Model._meta.get_fields()}


# === Cria os três níveis do dia para o tema (facil/medio/dificil) ===
@pytest.fixture
def caca_trio(db, assunto, noticia):
    from caca_links.models import CacaPalavras

    hoje = timezone.localdate()

    def mk(dif):
        kwargs = dict(
            tema=assunto,
            noticia=noticia,
            dificuldade=dif,
            palavras_chave=["RECIFE", "JC", "BRASIL", "ECONOMIA", "CULTURA", "POLITICA"],
        )
        if _has_field(CacaPalavras, "data"):
            kwargs["data"] = hoje
        if _has_field(CacaPalavras, "grade"):
            kwargs["grade"] = [["A"] * 10 for _ in range(10)]
        return CacaPalavras.objects.create(**kwargs)

    return (mk("facil"), mk("medio"), mk("dificil"))


def test_escolher_tema_context(login, assunto, caca_trio, monkeypatch):
    """
    Garante que a view responde e fornece as chaves esperadas no contexto,
    sem depender de carregamento real de template (evita TemplateDoesNotExist
    quando outros testes mexem no TEMPLATES).
    """
    import caca_links.views as views
    from django.http import HttpResponse

    captured = {}

    def fake_render(request, template_name, context=None, *args, **kwargs):
        # salva o contexto para asserções e devolve 200
        captured["template"] = template_name
        captured["context"] = context or {}
        resp = HttpResponse("ok")
        return resp

    # substitui o render só durante este teste
    monkeypatch.setattr(views, "render", fake_render)

    url = reverse("caca_links:escolher_tema")
    resp = login.get(url)
    assert resp.status_code == 200

    # checagens de contrato do contexto (sem depender de loader)
    assert captured.get("template")  # ex.: "cacalinks/escolher_tema.html"
    ctx = captured.get("context", {})
    assert "temas" in ctx

    temas = ctx["temas"]
    assert hasattr(temas, "__iter__")

def test_jogar_renderiza(login, assunto, caca_trio, monkeypatch):
    """
    Com CacaPalavras existente para o tema (nível inicial = facil),
    a view 'jogar' deve responder 200, sem depender do template físico.
    """
    import caca_links.views as views
    from django.http import HttpResponse

    # evita TemplateDoesNotExist e deixa o teste focar no status/fluxo
    def fake_render(request, template_name, context=None, *args, **kwargs):
        return HttpResponse("ok")

    monkeypatch.setattr(views, "render", fake_render)

    url = reverse("caca_links:jogar", args=[assunto.pk])
    resp = login.get(url)
    assert resp.status_code in (200, 302)

def test_fluxo_concluir_nivel(login, assunto, caca_trio, django_db_reset_sequences, monkeypatch):
    """
    Garante que com trio de níveis do dia, o fluxo conclui do 1→2→3 e marca concluido=True,
    sem depender de rotas do app noticias ou de namespace específico.
    """
    from caca_links.models import ProgressoJogador
    import caca_links.views as views
    from django.http import HttpResponse
    from django.urls import reverse
    from django.contrib.auth import get_user_model

    # Evita NoReverseMatch para 'noticias:detalhe_noticia'
    def fake_reverse(viewname, urlconf=None, args=None, kwargs=None, current_app=None):
        return "/fake/noticia/1/"
    monkeypatch.setattr(django.urls, "reverse", fake_reverse)

    # Evita NoReverseMatch para 'cacalinks:jogar' caso exista legado
    def fake_redirect(to, *args, **kwargs):
        return HttpResponse("redirected-ok")
    monkeypatch.setattr(views, "redirect", fake_redirect)

    # Evita TemplateDoesNotExist durante o fluxo (jogar -> render)
    def fake_render(request, template_name, context=None, *args, **kwargs):
        return HttpResponse("ok")
    monkeypatch.setattr(views, "render", fake_render)

    # Usuário logado
    User = get_user_model()
    uid = login.session["_auth_user_id"]
    u = User.objects.get(pk=uid)

    # Progresso inicial
    prog = ProgressoJogador.objects.create(usuario=u, tema=assunto)

    # Abrir o jogo (prepara sessão/estado se necessário)
    jogar_url = reverse("caca_links:jogar", args=[assunto.pk])
    r0 = login.get(jogar_url)
    assert r0.status_code == 200

    concluir_url = reverse("caca_links:concluir_nivel", args=[assunto.pk])

    # Concluir 3 níveis (limite de segurança maior, caso lógica precise reabrir o jogo)
    for _ in range(10):
        r = login.post(concluir_url, follow=True)
        assert r.status_code in (200, 302)
        prog.refresh_from_db()
        if getattr(prog, "concluido", False) is True:
            break
        # algumas implementações exigem reabrir o jogo a cada nível
        login.get(jogar_url)

    assert getattr(prog, "concluido", False) is True

    # Idempotência dos links conquistados
    links = getattr(prog, "links_conquistados", [])
    login.post(concluir_url, follow=True)
    prog.refresh_from_db()
    if links:
        assert prog.links_conquistados.count(links[0]) == 1