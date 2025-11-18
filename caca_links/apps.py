from django.apps import AppConfig

class CacaLinksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caca_links'

    def ready(self):
        from .cron import iniciar_cron_caca_links
        iniciar_cron_caca_links()
