from django.apps import AppConfig


class NoticiasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'noticias'
    
def ready(self):
    from .models import Assunto
    temas = [
        ("Política", "politica"),
        ("Blog do Torcedor", "blog-do-torcedor"),
        ("Social1", "social1"),
        ("Cultura", "cultura"),
        ("Receita da Boa", "receita-da-boa"),
        ("Brasil", "brasil"),
        ("Economia", "economia"),
        ("Internacional", "internacional"),
    ]
    for nome, slug in temas:
        Assunto.objects.get_or_create(nome=nome, slug=slug)
