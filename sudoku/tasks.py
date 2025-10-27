# sudoku/scheduler.py (ou tasks.py, dependendo de onde o arquivo está)

from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

from .models import SudokuPuzzle
from .sudoku_generator import generate_puzzle 

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution # DjangoJob não é mais necessário

logger = logging.getLogger(__name__)

# A função generate_daily_puzzles() está ótima, não precisa de mudanças.
def generate_daily_puzzles():
    data_hoje = timezone.localdate() 
    niveis = ['easy', 'medium', 'difficult']

    logger.info(f"Iniciando a geração de Sudokus para o dia {data_hoje}...")

    for dificuldade in niveis:
        if SudokuPuzzle.objects.filter(date=data_hoje, difficulty=dificuldade).exists():
            logger.info(f"Sudoku {dificuldade.capitalize()} já existe para hoje. Pulando.")
            continue
            
        logger.info(f"Gerando Sudoku {dificuldade.capitalize()}...")
        
        try:
            problem_board_str, solution_board_str = generate_puzzle(dificuldade)
            
            SudokuPuzzle.objects.create(
                date=data_hoje,
                difficulty=dificuldade,
                problem_board=problem_board_str,
                solution_board=solution_board_str
            )
            logger.info(f"✅ Sudoku {dificuldade.capitalize()} salvo com sucesso.")
        
        except Exception as e:
            logger.error(f"Falha crítica ao gerar/salvar Sudoku {dificuldade}: {e}")

scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
scheduler.add_jobstore(DjangoJobStore(), "default")

def start_scheduler():
    """Inicia o scheduler, limpando execuções antigas e agendando o job diário."""
    if scheduler.running:
        return

    try:
        seven_days_ago = timezone.now() - timedelta(days=7)
        DjangoJobExecution.objects.filter(created__lt=seven_days_ago).delete()
        logger.info("Execuções antigas do scheduler foram limpas.")

        scheduler.add_job(
            generate_daily_puzzles,
            trigger="cron",
            hour=0,   
            minute=1,   
            id="sudoku_geracao_diaria", 
            max_instances=1,
            replace_existing=True,     
            misfire_grace_time=86400  
        )
        
        scheduler.start()
        logger.info("🚀 APSScheduler iniciado com sucesso e job agendado.")

    except Exception as e:
        logger.error(f"Falha CRÍTICA ao iniciar o APScheduler: {e}")