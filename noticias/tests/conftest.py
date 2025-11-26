import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from noticias.models import Assunto, Noticia


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="alice", email="alice@example.com", password="123456")


@pytest.fixture
def client_logged(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def assunto_factory(db):
    def make(nome="Política", slug="politica"):
        # MUDANÇA AQUI: De .create() para .get_or_create()
        # get_or_create retorna uma tupla (objeto, criado), pegamos o [0]
        assunto, _ = Assunto.objects.get_or_create(
            slug=slug, 
            defaults={'nome': nome}
        )
        return assunto
    return make


@pytest.fixture
def noticia_factory(db):
    """
    Cria Noticia com campos reais do seu modelo.
    - Não usa 'categoria' nem 'destaque', pois não existem no model.
    - Permite setar 'assuntos' e 'criado_em' (ajusta via update).
    """
    def make(
        titulo="Título de teste",
        conteudo="Corpo da notícia de teste. " * 20,
        autor="JC",
        assuntos=None,
        criado_em=None,
    ):
        n = Noticia.objects.create(
            titulo=titulo,
            conteudo=conteudo,
            autor=autor,
        )
        if assuntos:
            for a in assuntos:
                n.assuntos.add(a)
        if criado_em:
            Noticia.objects.filter(pk=n.pk).update(criado_em=criado_em)
            n.refresh_from_db()
        return n
    return make
