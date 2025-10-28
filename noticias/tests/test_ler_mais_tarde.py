from django.urls import reverse


def test_toggle_salvo_e_minhas_salvas(client_logged, noticia_factory):
    n = noticia_factory(titulo="Salvar 1")
    toggle_url = reverse("noticias:toggle_salvo", args=[n.pk])

    # Adicionar à lista
    r = client_logged.post(toggle_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r.status_code == 200
    data = r.json()
    assert data["saved"] is True

    # Página de salvos contém a notícia
    salvos_url = reverse("noticias:minhas_salvas")
    r2 = client_logged.get(salvos_url)
    assert r2.status_code == 200
    html = r2.content.decode("utf-8")
    assert "Salvar 1" in html

    # Remover da lista
    r3 = client_logged.post(toggle_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["saved"] is False

    # A página de salvos NÃO deve mais conter a notícia
    r4 = client_logged.get(salvos_url)
    assert r4.status_code == 200
    html2 = r4.content.decode("utf-8")
    assert "Salvar 1" not in html2


def test_toggle_salvo_duplo_na_mesma_sessao(client_logged, noticia_factory):
    """
    Reforço: garante que o toggle é idempotente dentro da mesma sessão
    (adiciona -> remove -> adiciona novamente sem erros).
    """
    n = noticia_factory(titulo="Salvar X")
    url = reverse("noticias:toggle_salvo", args=[n.pk])

    # 1º clique -> salva
    r1 = client_logged.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r1.status_code == 200 and r1.json()["saved"] is True

    # 2º clique -> remove
    r2 = client_logged.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r2.status_code == 200 and r2.json()["saved"] is False

    # 3º clique -> salva novamente
    r3 = client_logged.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r3.status_code == 200 and r3.json()["saved"] is True


def test_toggle_salvo_requer_login(client, noticia_factory):
    """
    Segurança: sem login, a rota deve negar ou redirecionar para /login/?next=...
    """
    n = noticia_factory(titulo="Privado")
    url = reverse("noticias:toggle_salvo", args=[n.pk])

    r = client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert r.status_code in (302, 401, 403)
    if r.status_code == 302:
        assert "/login/" in r["Location"]
        assert "next=" in r["Location"]


def test_toggle_salvo_sem_header_ajax(client_logged, noticia_factory):
    """
    Robustez: chamada sem o header AJAX não deve quebrar.
    (Se sua view responde com HTML ou redireciona, o teste aceita ambos.)
    """
    n = noticia_factory(titulo="Sem AJAX")
    url = reverse("noticias:toggle_salvo", args=[n.pk])

    r = client_logged.post(url)  # sem HTTP_X_REQUESTED_WITH
    # Aceita JSON 200 ou um redirect/HTML 302/200, dependendo da sua implementação
    assert r.status_code in (200, 302)
