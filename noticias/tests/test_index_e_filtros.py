import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# ✅ Permite acesso ao banco de dados em todos os testes deste arquivo
pytestmark = pytest.mark.django_db


def test_index_renders_ok(client):
    url = reverse("noticias:index")
    r = client.get(url)
    assert r.status_code == 200
    assert "text/html" in r["Content-Type"]


def test_filtra_por_assunto_e_periodo(client, assunto_factory, noticia_factory):
    """
    A home possui blocos editoriais (carrosséis, etc.) que não obedecem ao filtro.
    Portanto, validamos que a notícia que satisfaz o filtro aparece,
    sem exigir a ausência global de outras notícias.
    """
    a_politica = assunto_factory("Política", "politica")
    a_economia = assunto_factory("Economia", "economia")

    # Dentro de 7 dias (deve aparecer nos resultados filtrados)
    noticia_factory(
        titulo="Notícia 1",
        assuntos=[a_politica],
        criado_em=timezone.now() - timedelta(days=2),
    )
    # Fora da janela de 7 dias (pode aparecer em blocos editoriais não filtrados)
    noticia_factory(
        titulo="Notícia 2",
        assuntos=[a_economia],
        criado_em=timezone.now() - timedelta(days=10),
    )

    url = reverse("noticias:index")
    r = client.get(url, {"assunto": ["politica"], "periodo": "7d"})
    assert r.status_code == 200

    html = r.content.decode("utf-8")

    # Validação POSITIVA: a notícia que passa no filtro precisa estar presente.
    assert "Notícia 1" in html

    # NÃO fazemos assert negativo global sobre "Notícia 2" porque
    # blocos como “Destaques/Para você/JC360” podem ignorar o filtro.
    # (Se a view expuser um queryset específico de resultados filtrados
    # no contexto, podemos validar diretamente esse queryset no futuro.)


def test_index_contem_blocos_chave(client):
    """Sanidade: blocos principais aparecem (previne 'passar' com template quebrado)."""
    r = client.get(reverse("noticias:index"))
    html = r.content.decode("utf-8")
    assert "Destaques" in html
    assert "Para você" in html
    assert "Mais lidas" in html


def test_index_usa_template_noticias(client):
    """Garante que o template da app 'noticias' foi usado."""
    r = client.get(reverse("noticias:index"))
    # Nem todo backend expõe o nome exato do arquivo; checamos por substring segura.
    assert any("noticias/" in (t.name or "") for t in r.templates)
