# caca_links/tests/helpers.py
from django.utils import timezone

def build_defaults_for_model(Model):
    """
    Gera defaults 'inteligentes' a partir dos nomes de campos,
    para reduzir a chance de IntegrityError quando o schema variar.
    """
    names = {f.name for f in Model._meta.get_fields() if hasattr(f, "attname")}
    d = {}
    if "nome" in names:
        d["nome"] = "Assunto de Teste"
    if "slug" in names:
        d["slug"] = "assunto-teste"
    if "titulo" in names:
        d["titulo"] = "Título de Teste"
    if "conteudo" in names:
        d["conteudo"] = "Corpo da notícia para gerar palavras."
    if "publicado_em" in names:
        d["publicado_em"] = timezone.now()
    if "autor" in names:
        d["autor"] = "Sistema de Teste"
    if "ativo" in names:
        d["ativo"] = True
    return d


def create_assunto(Assunto, **overrides):
    data = build_defaults_for_model(Assunto)
    data.update(overrides)
    return Assunto.objects.create(**data)


def create_noticia(Noticia, assunto, **overrides):
    data = build_defaults_for_model(Noticia)
    # tenta adivinhar FKs comuns
    if "assunto" in {f.name for f in Noticia._meta.get_fields()}:
        data["assunto"] = assunto
    data.update(overrides)
    return Noticia.objects.create(**data)
