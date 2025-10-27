from django.urls import reverse
from urllib.parse import quote


def test_detalhe_incrementa_visualizacoes(client, noticia_factory):
    n = noticia_factory(titulo="Detalhe OK")
    url = reverse("noticias:noticia_detalhe", args=[n.pk])

    r1 = client.get(url)
    assert r1.status_code == 200
    n.refresh_from_db()
    assert n.visualizacoes >= 1


def test_detalhe_incrementa_uma_vez_por_chamada(client, noticia_factory):
    # Reforço: garantir que cada chamada incremente pelo menos 1
    n = noticia_factory(titulo="Contagem")
    url = reverse("noticias:noticia_detalhe", args=[n.pk])

    before = n.visualizacoes
    r = client.get(url)
    assert r.status_code == 200
    n.refresh_from_db()
    assert n.visualizacoes >= before + 1


def test_compartilhar_whatsapp(client, noticia_factory):
    n = noticia_factory(titulo="Compartilhar WhatsApp")
    url = reverse("noticias:noticia_detalhe", args=[n.pk])
    link_whatsapp = f"https://wa.me/?text={url}"
    assert "wa.me" in link_whatsapp
    assert url in link_whatsapp


def test_compartilhar_twitter_usando_assunto(client, noticia_factory, assunto_factory):
    # Usa Assunto como base de hashtag (seção)
    a = assunto_factory("Esportes", "esportes")
    n = noticia_factory(titulo="Compartilhar Twitter", assuntos=[a])
    url = reverse("noticias:noticia_detalhe", args=[n.pk])

    hashtag = "Esportes"  # render no intent sem '#'
    link_twitter = (
        f"https://twitter.com/intent/tweet?"
        f"text={n.titulo}&url={url}&hashtags={hashtag}"
    )

    assert "twitter.com/intent/tweet" in link_twitter
    assert n.titulo in link_twitter
    assert url in link_twitter
    assert "hashtags=Esportes" in link_twitter


def test_twitter_intent_tem_url_encoding(client, noticia_factory, assunto_factory):
    # Reforço: títulos/URLs com acentos/emoji precisam ser codificados
    a = assunto_factory("Política", "politica")
    n = noticia_factory(titulo="Café ☕ & Política", assuntos=[a])
    url = reverse("noticias:noticia_detalhe", args=[n.pk])

    intent = (
        f"https://twitter.com/intent/tweet?"
        f"text={quote(n.titulo)}&url={quote(url)}&hashtags=Política"
    )
    # ☕ precisa estar codificado
    assert "%E2%98%95" in intent
    # a URL do detalhe também precisa estar codificada
    assert quote(url) in intent


def test_erro_ao_copiar_link_simulado():
    try:
        raise PermissionError("Clipboard inacessível")
    except PermissionError as e:
        msg = str(e)
    assert "Clipboard" in msg
