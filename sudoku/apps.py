import os 
import sys
from django.apps import AppConfig
from django.conf import settings
import logging
import sys
import os 

class SudokuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sudoku'

    def ready(self):
        if os.environ.get('RUN_MAIN'):
            from . import scheduler
            
            is_running_server = any(cmd in sys.argv for cmd in ['runserver', 'gunicorn'])
            
            if is_running_server:
                scheduler.start()
