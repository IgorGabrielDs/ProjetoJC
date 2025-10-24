from django.apps import AppConfig
from django.conf import settings
import logging
import sys
import os 

logger = logging.getLogger(__name__)

class SudokuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sudoku'

    def ready(self):
        is_running_server = 'runserver' in sys.argv
        
        is_reloader_process = os.environ.get('RUN_MAIN') != 'true'
        if is_running_server and not is_reloader_process:
            
            from .tasks import start_scheduler 

            if settings.DEBUG:
                logger.info("APSScheduler: Iniciando no processo principal (Modo DEBUG).")
            
            try:
                start_scheduler()
            except Exception as e:
                logger.error(f"Falha CRÍTICA ao iniciar o APScheduler: {e}")
        else:
            logger.info("APSScheduler: Não iniciado (Processo de recarregamento ou comando de gerenciamento).")