import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
# Importe o seu gerador e o seu modelo
from ...sudoku_generator import generate_puzzle
from ...models import SudokuPuzzle

class Command(BaseCommand):
    help = 'Gera e salva os puzzles de Sudoku para o dia atual.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        difficulties = ['easy', 'medium', 'difficult']
        
        created_count = 0
        
        for diff in difficulties:
            # Verifica se o puzzle para este dia e dificuldade JÁ EXISTE
            exists = SudokuPuzzle.objects.filter(date=today, difficulty=diff).exists()
            
            if not exists:
                self.stdout.write(f'Gerando puzzle nível {diff} para {today}...')
                try:
                    # Gera o puzzle usando sua função
                    problem_str, solution_str = generate_puzzle(diff)
                    
                    # Salva no banco de dados
                    SudokuPuzzle.objects.create(
                        date=today,
                        difficulty=diff,
                        problem_board=problem_str,
                        solution_board=solution_str
                    )
                    created_count += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Erro ao gerar puzzle {diff}: {e}'))
            else:
                self.stdout.write(self.style.WARNING(f'Puzzle nível {diff} para {today} já existe. Pulando.'))

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'{created_count} puzzle(s) criados com sucesso para {today}.'))
        else:
            self.stdout.write(self.style.SUCCESS('Nenhum puzzle novo precisou ser criado.'))