from django.utils import timezone
from django.db import IntegrityError
from django.conf import settings
from datetime import timedelta
import logging
from .models import SudokuPuzzle
from .sudoku_generator import generate_puzzle 
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution, DjangoJob


logger = logging.getLogger(__name__)


def gerar_sudokus_diarios():
    data_hoje = timezone.localdate() 
    niveis_e_parametros = ['easy', 'medium', 'difficult']

    logger.info(f"Iniciando a geração de Sudokus para o dia {data_hoje}...")

    for dificuldade in niveis_e_parametros:
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
            logger.info(f"Sudoku {dificuldade.capitalize()} salvo com sucesso.")
        
        except IntegrityError:
            logger.warning(f"IntegrityError: Sudoku {dificuldade} já existia no momento da criação. Ignorando.")
        except Exception as e:
            logger.error(f"Falha crítica ao gerar/salvar Sudoku {dificuldade}: {e}")


scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
scheduler.add_jobstore(DjangoJobStore(), "default")


def start_scheduler():
    if scheduler.running:
        return

    DjangoJobExecution.objects.delete_old_job_executions(max_age=timedelta(days=7))

    try:
        try:
            job_to_delete = DjangoJob.objects.get(id='sudoku_geracao_diaria')
            job_to_delete.delete()
        except DjangoJob.DoesNotExist:
            pass
        
        scheduler.add_job(
            gerar_sudokus_diarios,
            trigger="cron",
            hour=0,      
            minute=5,    
            id="sudoku_geracao_diaria",  
            max_instances=1, 
            replace_existing=True,
            misfire_grace_time=86400 
        )
        scheduler.start()
        logger.info("APSScheduler iniciado com sucesso e job agendado.")

    except Exception as e:
        logger.error(f"Falha CRÍTICA ao iniciar o APScheduler: {e}")