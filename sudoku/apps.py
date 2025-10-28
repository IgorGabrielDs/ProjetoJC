# sudoku/apps.py
import sys
import os
from django.apps import AppConfig

class SudokuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sudoku'

    def ready(self):
        try:
            # Só inicia em runserver/gunicorn e no processo principal
            is_server = any(cmd in sys.argv for cmd in ['runserver', 'gunicorn'])
            is_main = os.environ.get("RUN_MAIN") == "true" or 'gunicorn' in " ".join(sys.argv)
            if is_server and is_main:
                from .scheduler import start
                start()
        except Exception as e:
            print(f"Erro ao iniciar scheduler: {e}")
