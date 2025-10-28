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

logger = logging.getLogger(__name__)


def generate_daily_puzzles():
    """Gera automaticamente os Sudokus do dia (easy, medium, difficult)."""
    data_hoje = timezone.localdate()
    niveis = ['easy', 'medium', 'hard']

    logger.info(f"Iniciando geração dos Sudokus para o dia {data_hoje}...")

    for dificuldade in niveis:
        if SudokuPuzzle.objects.filter(date=data_hoje, difficulty=dificuldade).exists():
            logger.info(f"Sudoku '{dificuldade}' já existe para hoje. Pulando.")
            continue

        logger.info(f"Gerando Sudoku nível {dificuldade.upper()}...")
        try:
            problem_board_str, solution_board_str = generate_puzzle(dificuldade)

            SudokuPuzzle.objects.create(
                date=data_hoje,
                difficulty=dificuldade,
                problem_board=problem_board_str,
                solution_board=solution_board_str
            )
            logger.info(f"✅ Sudoku '{dificuldade}' criado e salvo com sucesso.")

        except Exception as e:
            logger.error(f"❌ Erro ao gerar Sudoku '{dificuldade}': {e}")


# Scheduler global
scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
scheduler.add_jobstore(DjangoJobStore(), "default")


def start_scheduler():
    """Inicia o scheduler e agenda o job diário de geração de Sudoku."""
    if scheduler.running:
        logger.info("Scheduler já está em execução.")
        return

    try:
        # Limpa execuções antigas
        sete_dias_atras = timezone.now() - timedelta(days=7)
        DjangoJobExecution.objects.filter(created__lt=sete_dias_atras).delete()
        logger.info("🧹 Execuções antigas removidas.")

        # Adiciona o job diário
        scheduler.add_job(
            generate_daily_puzzles,
            trigger="cron",
            hour=0,
            minute=1,
            id="sudoku_geracao_diaria",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=86400  # tolerância de 24h caso o servidor caia
        )

        scheduler.start()
        logger.info("🚀 APScheduler iniciado com sucesso e job agendado.")

    except Exception as e:
        logger.error(f"🔥 Falha ao iniciar o APScheduler: {e}")
