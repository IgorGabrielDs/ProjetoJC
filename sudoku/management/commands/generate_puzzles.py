from django.core.management.base import BaseCommand
from django.utils import timezone
from sudoku.models import SudokuPuzzle
from sudoku.sudoku_generator import generate_puzzle
import random

class Command(BaseCommand):
    help = 'Gera os 3 Sudokus diários (fácil, médio, difícil)'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        
        for diff in ['easy', 'medium', 'difficult']:
            if SudokuPuzzle.objects.filter(date=today, difficulty=diff).exists():
                self.stdout.write(self.style.WARNING(f'Sudoku {diff} para {today} já existe. Pulando.'))
                continue

            self.stdout.write(f'Gerando Sudoku {diff} para {today}...')
        
            problem_board, solution_board = generate_puzzle(diff)
            
            SudokuPuzzle.objects.create(
                date=today,
                difficulty=diff,
                problem_board=problem_board,
                solution_board=solution_board
            )
            
            self.stdout.write(self.style.SUCCESS(f'Sudoku {diff} para {today} criado com sucesso.'))