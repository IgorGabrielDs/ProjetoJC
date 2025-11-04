# noticias/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging

logger = logging.getLogger(__name__)

# A FUNÇÃO É DEFINIDA AQUI FORA
def popular_assuntos(sender, **kwargs):
    from .models import Assunto
    TEMAS_PADRAO = [
        ("Política", "politica"),
        ("Blog do Torcedor", "blog-do-torcedor"),
        ("Social1", "social1"),
        ("Cultura", "cultura"),
        ("Receita da Boa", "receita-da-boa"),
        ("Brasil", "brasil"),
        ("Economia", "economia"),
        ("Internacional", "internacional"),
    ]
    logger.info("Verificando/adicionando assuntos (temas) padrão...")
    criados = 0
    for nome, slug in TEMAS_PADRAO:
        assunto, created = Assunto.objects.get_or_create(
            nome=nome,
            defaults={"slug": slug}
        )
        if created:
            criados += 1
    if criados > 0:
        logger.info(f"Adicionados {criados} novos assuntos.")
    else:
        logger.info("Assuntos padrão já estavam no banco.")


class NoticiasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'noticias'

    # 'ready' está DENTRO da classe
    def ready(self):
        post_migrate.connect(popular_assuntos, sender=self)