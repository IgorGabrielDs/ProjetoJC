# sudoku/scheduler.py
import sys
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .tasks import generate_daily_puzzles

scheduler = BackgroundScheduler(timezone=pytz.UTC)
scheduler.add_jobstore(DjangoJobStore(), "default")


def start():
    """Inicia o scheduler ao subir o servidor, se não estiver em modo de teste."""
    if scheduler.running:
        print("⏳ Scheduler já está em execução.")
        return

    if 'test' in sys.argv:
        print("🧪 Scheduler não será iniciado em modo de teste.")
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
        print(f"⚠️ Erro ao iniciar o scheduler: {e}")
        scheduler.remove_job('daily_sudoku_job', 'default')
