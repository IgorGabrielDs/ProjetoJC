import sys
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
import pytz

from .tasks import generate_daily_puzzles

scheduler = BackgroundScheduler(timezone=pytz.UTC)
scheduler.add_jobstore(DjangoJobStore(), "default")

def start():
    """
    Starts the scheduler and adds the daily puzzle generation job.
    This function should only be called when the server is ready.
    """
    if scheduler.running:
        print("Scheduler is already running.")
        return

    if 'test' in sys.argv:
        print("Scheduler not started in test environment.")
        return

    scheduler.add_job(
        generate_daily_puzzles,
        trigger='cron',
        hour=0,
        minute=1, 
        id='daily_sudoku_job',
        replace_existing=True,
    )
    
    try:
        scheduler.start()
        print("🕒 Scheduler do Sudoku iniciado com sucesso.")
    except Exception as e:
        print(f"Erro ao iniciar o scheduler: {e}")
        scheduler.remove_job('daily_sudoku_job', 'default')