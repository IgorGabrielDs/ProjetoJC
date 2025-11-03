# caca_links/tests/conftest.py
import pytest
from django.utils import timezone


@pytest.fixture(autouse=True)
def minimal_templates(settings, tmp_path):
    """
    Templates mínimos para evitar TemplateDoesNotExist
    em TODAS as views do caça-links durante os testes.
    """
    root = tmp_path / "templates"
    base_dir = root / "cacalinks"
    base_dir.mkdir(parents=True)

    (base_dir / "base.html").write_text(
        "{% block content %}{% endblock %}",
        encoding="utf-8",
    )
    (base_dir / "escolher_tema.html").write_text(
        "{% block content %}OK escolher_tema{% endblock %}",
        encoding="utf-8",
    )
    (base_dir / "jogo.html").write_text(
        "{% block content %}OK jogo{% endblock %}",
        encoding="utf-8",
    )
    (base_dir / "concluir.html").write_text(
        "{% block content %}OK concluir{% endblock %}",
        encoding="utf-8",
    )

    dirs = list(settings.TEMPLATES[0].get("DIRS", []))
    root_str = str(root)
    if root_str not in dirs:
        settings.TEMPLATES[0]["DIRS"] = [root_str, *dirs]


def _has_field(Model, name: str) -> bool:
    return name in {f.name for f in Model._meta.get_fields()}


# ---------- FIXTURES DE MODELOS BÁSICOS ----------

@pytest.fixture
def assunto(db):
    """Assunto mínimo, tolerante ao schema."""
    from noticias.models import Assunto as AssuntoModel
    data = {}
    if _has_field(AssuntoModel, "nome"):
        data["nome"] = "Tema de Teste"
    if _has_field(AssuntoModel, "slug"):
        # usar um dos slugs que a view filtra
        data["slug"] = "economia"
    return AssuntoModel.objects.create(**data)


@pytest.fixture
def noticia(db, assunto):
    """Noticia mínima ligada ao assunto, tolerante ao schema."""
    from noticias.models import Noticia as NoticiaModel
    fields = {f.name: f for f in NoticiaModel._meta.get_fields()}

    payload = {}
    if "titulo" in fields:
        payload["titulo"] = "Notícia de Teste"
    if "slug" in fields:
        payload["slug"] = "noticia-de-teste"
    if "assunto" in fields:
        payload["assunto"] = assunto
    if "conteudo" in fields:
        payload["conteudo"] = "Conteúdo de teste."
    elif "corpo" in fields:
        payload["corpo"] = "Conteúdo de teste."
    elif "texto" in fields:
        payload["texto"] = "Conteúdo de teste."
    if "publicado_em" in fields:
        payload["publicado_em"] = timezone.now()
    if "data_publicacao" in fields:
        payload["data_publicacao"] = timezone.localdate()
    if "resumo" in fields:
        payload["resumo"] = "Resumo de teste."

    return NoticiaModel.objects.create(**payload)


# ---------- FIXTURES DE AUTENTICAÇÃO ----------

@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="tester_caca",
        email="tester@example.com",
        password="pass1234",
    )


@pytest.fixture
def login(client, user):
    """Retorna o client já autenticado."""
    logged = client.login(username="tester_caca", password="pass1234")
    assert logged, "Falha ao autenticar usuário de teste"
    return client
