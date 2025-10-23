# sudoku/apps.py

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class SudokuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sudoku'

    def ready(self):
        from django_apscheduler.jobstores import DjangoJobStore
        from django_apscheduler import util
        from apscheduler.schedulers.background import BackgroundScheduler
        from .tasks import gerar_sudokus_diarios
        from django.conf import settings

        if settings.DEBUG:
            
            logger.info("APSScheduler desabilitado em modo DEBUG.")
            return 
        
        try:
            scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
            scheduler.add_jobstore(DjangoJobStore(), "default")
            
            scheduler.add_job(
                gerar_sudokus_diarios,
                trigger="cron",
                hour=0,
                minute=0,
                id="sudoku_geracao_diaria",  
                max_instances=1, 
                replace_existing=True,
                misfire_grace_time=3600 
            )
            scheduler.start()
            logger.info("APSScheduler iniciado e Sudoku job agendado.")

        except Exception as e:
            logger.error(f"Erro ao iniciar o APScheduler: {e}")