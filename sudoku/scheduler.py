# sudoku/scheduler.py
import sys
import os
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
import pytz
from .tasks import generate_daily_puzzles

BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
scheduler = BackgroundScheduler(timezone=BRAZIL_TZ)
scheduler.add_jobstore(DjangoJobStore(), "default")

def _is_main_process():
    # Em dev: RUN_MAIN == 'true' só no processo principal do autoreload
    # Em produção (gunicorn), não existe RUN_MAIN — então deixamos passar.
    return os.environ.get("RUN_MAIN") == "true" or "gunicorn" in " ".join(sys.argv)

def start():
    if not _is_main_process():
        print("🧪 Scheduler não iniciado (processo secundário / teste / migração).")
        return

    if scheduler.running:
        print("⚙ Scheduler já está em execução.")
        return

    if any(arg in sys.argv for arg in ["test", "makemigrations", "migrate", "collectstatic"]):
        print("🧪 Scheduler não iniciado (modo de teste/migração).")
        return

    if not scheduler.get_job('daily_sudoku_job'):
        scheduler.add_job(
            generate_daily_puzzles,
            trigger='cron',
            hour=0,
            minute=1,
            id='daily_sudoku_job',
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=86400,
        )
        print("✅ Job diário do Sudoku agendado para 00:01 (horário de Brasília).")
    else:
        print("♻ Job diário já existente.")

    try:
        scheduler.start()
        print("🕒 Scheduler do Sudoku iniciado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao iniciar o scheduler: {e}")
