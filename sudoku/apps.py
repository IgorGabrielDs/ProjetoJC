import os
import sys
from django.apps import AppConfig

class SudokuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sudoku'

    def ready(self):
        """Inicializa o scheduler apenas quando o servidor está realmente rodando."""
        if os.environ.get('RUN_MAIN') != 'true':
            return

        is_running_server = any(cmd in sys.argv for cmd in ['runserver', 'gunicorn'])
        if is_running_server:
            from .scheduler import start
            start()
