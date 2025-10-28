# sudoku/tasks.py
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

from .models import SudokuPuzzle
from .sudoku_generator import generate_puzzle
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

logger = logging.getLogger(__name__)  # <-- correção

def generate_daily_puzzles():
    """Gera automaticamente os Sudokus do dia (easy, medium, hard)."""
    data_hoje = timezone.localdate()
    niveis = ['easy', 'medium', 'hard']

    logger.info(f"Iniciando geração dos Sudokus para o dia {data_hoje}...")

    for dificuldade in niveis:
        try:
            # Geração de tabuleiros
            problem_board_str, solution_board_str = generate_puzzle(dificuldade)

            # Idempotente — evita erro de unique_together
            obj, created = SudokuPuzzle.objects.update_or_create(
                date=data_hoje,
                difficulty=dificuldade,
                defaults={
                    "problem_board": problem_board_str,
                    "solution_board": solution_board_str,
                },
            )
            if created:
                logger.info(f"✅ Sudoku '{dificuldade}' criado.")
            else:
                logger.info(f"♻ Sudoku '{dificuldade}' já existia — atualizado.")
        except Exception as e:
            logger.error(f"❌ Erro ao gerar Sudoku '{dificuldade}': {e}")

# (se quiser manter um scheduler aqui, tudo bem — mas evite dois "starts" no projeto)
scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
scheduler.add_jobstore(DjangoJobStore(), "default")

def start_scheduler():
    if scheduler.running:
        logger.info("Scheduler já está em execução.")
        return

    try:
        sete_dias_atras = timezone.now() - timedelta(days=7)
        DjangoJobExecution.objects.filter(created__lt=sete_dias_atras).delete()
        logger.info("🧹 Execuções antigas removidas.")

        scheduler.add_job(
            generate_daily_puzzles,
            trigger="cron",
            hour=0,
            minute=1,
            id="sudoku_geracao_diaria",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=86400,
        )
        scheduler.start()
        logger.info("🚀 APScheduler iniciado com sucesso e job agendado.")
    except Exception as e:
        logger.error(f"🔥 Falha ao iniciar o APScheduler: {e}")
