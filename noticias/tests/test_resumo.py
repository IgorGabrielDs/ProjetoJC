import pytest
from django.urls import reverse
import sys
import types

# ✅ garante acesso ao banco para todos os testes deste arquivo
pytestmark = pytest.mark.django_db


class DummyResp:
    def __init__(self, text):
        self.text = text


class DummyModel:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def generate_content(self, prompt):
        if self.should_fail:
            raise RuntimeError("timeout")
        return DummyResp("Resumo gerado com sucesso.")


def test_resumo_sucesso(monkeypatch, settings, client_logged, noticia_factory):
    n = noticia_factory(titulo="Com Resumo")
    settings.GEMINI_API_KEY = "fake-key"

    fake_mod = types.SimpleNamespace()
    fake_mod.configure = lambda api_key=None: None

    def fake_ctor(name):
        assert name == "gemini-flash-latest"
        return DummyModel(should_fail=False)

    monkeypatch.setitem(sys.modules, "google.generativeai", fake_mod)
    monkeypatch.setattr(fake_mod, "GenerativeModel", fake_ctor, raising=False)

    url = reverse("noticias:resumir_noticia", args=[n.pk])
    r = client_logged.post(url)
    assert r.status_code == 200
    data = r.json()
    assert "Resumo gerado" in data["resumo"]

    # 🔒 reforço: garante que o resumo foi persistido no modelo
    # (protege contra regressões que retornam JSON mas não salvam no banco)
    from noticias.models import Noticia
    n_db = Noticia.objects.get(pk=n.pk)
    assert n_db.resumo
    assert "Resumo gerado" in n_db.resumo


def test_resumo_erro_provider(monkeypatch, settings, client_logged, noticia_factory):
    n = noticia_factory(titulo="Com Resumo")
    settings.GEMINI_API_KEY = "fake-key"

    fake_mod = types.SimpleNamespace()
    fake_mod.configure = lambda api_key=None: None

    def fake_ctor(name):
        return DummyModel(should_fail=True)

    monkeypatch.setitem(sys.modules, "google.generativeai", fake_mod)
    monkeypatch.setattr(fake_mod, "GenerativeModel", fake_ctor, raising=False)

    url = reverse("noticias:resumir_noticia", args=[n.pk])
    r = client_logged.post(url)
    assert r.status_code == 500
    data = r.json()
    assert "Erro ao conectar" in data["error"]


def test_resumo_texto_curto_desabilita_botao_ou_mensagem(client, noticia_factory):
    """
    Cenário BDD: notícia com <300 palavras deve desabilitar o botão 'Resumir'
    OU exibir mensagem/tooltip indicando que o texto é curto.
    Mantemos a checagem flexível para não acoplar ao HTML.
    """
    n = noticia_factory(titulo="Curta", conteudo="curto demais")
    r = client.get(reverse("noticias:noticia_detalhe", args=[n.pk]))
    assert r.status_code == 200
    html = r.content.decode("utf-8").lower()

    sinalizou_curto = (
        "texto curto demais para resumir" in html  # tooltip/mensagem
        or ("disabled" in html and "resum" in html)  # botão desabilitado contendo 'resum'
    )
    assert sinalizou_curto
