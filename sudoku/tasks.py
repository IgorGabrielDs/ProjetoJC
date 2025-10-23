from django.utils import timezone
from django.db import IntegrityError
from .models import SudokuPuzzle
from .sudoku_generator import generate_puzzle
import logging

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