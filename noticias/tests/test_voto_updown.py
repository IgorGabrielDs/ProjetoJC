import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_voto_up_e_toggle_down_ajax(client_logged, noticia_factory):
    """
    Verifica ciclo completo:
    upvote → troca para downvote → repete downvote (remove voto)
    """
    n = noticia_factory(titulo="Votável")
    url = reverse("noticias:votar", args=[n.pk])

    # 1️⃣ Upvote
    r = client_logged.post(url, {"valor": "1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r.status_code == 200
    data = r.json()
    assert data["up"] >= 1
    assert data["down"] == 0
    assert data["voto_usuario"] == 1

    # 2️⃣ Trocar para downvote
    r2 = client_logged.post(url, {"valor": "-1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["down"] >= 1
    assert data2["up"] == 0
    assert data2["voto_usuario"] == -1

    # 3️⃣ Repetir mesmo valor → remove voto
    r3 = client_logged.post(url, {"valor": "-1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["up"] == 0
    assert data3["down"] == 0
    assert data3["voto_usuario"] == 0

    # 🔄 Reforço: repetir upvote deve voltar a funcionar normalmente
    r4 = client_logged.post(url, {"valor": "1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r4.status_code == 200
    data4 = r4.json()
    assert data4["voto_usuario"] == 1
    assert data4["up"] >= 1


def test_voto_requer_login(client, noticia_factory):
    """
    Segurança: usuários anônimos não devem conseguir votar.
    """
    n = noticia_factory(titulo="Anonimo Teste")
    url = reverse("noticias:votar", args=[n.pk])
    r = client.post(url, {"valor": "1"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    # Pode redirecionar para login ou devolver 401/403 conforme a view
    assert r.status_code in (302, 401, 403)
    if r.status_code == 302:
        assert "/login" in r["Location"]


def test_voto_sem_header_ajax(client_logged, noticia_factory):
    """
    Robustez: view deve tolerar requisições sem o header AJAX.
    (Aceita JSON ou redirecionamento, mas não deve quebrar.)
    """
    n = noticia_factory(titulo="Sem Header")
    url = reverse("noticias:votar", args=[n.pk])
    r = client_logged.post(url, {"valor": "1"})  # sem HTTP_X_REQUESTED_WITH
    assert r.status_code in (200, 302)


def test_voto_valor_invalido(client_logged, noticia_factory):
    """
    Caso-limite: valores inválidos (ex: 'abc', '0') devem ser tratados com segurança.
    """
    n = noticia_factory(titulo="Invalido")
    url = reverse("noticias:votar", args=[n.pk])
    r = client_logged.post(url, {"valor": "abc"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r.status_code in (400, 200)  # aceita erro ou retorno neutro
    data = r.json()
    assert "voto_usuario" in data
    # nunca deve causar incremento incorreto
    assert data["up"] >= 0 and data["down"] >= 0
