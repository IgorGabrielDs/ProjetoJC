# sudoku/management/commands/generate_daily_sudoku.py
import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# ajuste o import conforme seu projeto
from ...sudoku_generator import generate_puzzle
from ...models import SudokuPuzzle


def _set_board_fields(obj, puzzle_str, solution_str):
    """
    Permite compatibilidade com esquemas diferentes:
    - board / solution
    - problem_board / solution_board
    """
    if hasattr(obj, "board") and hasattr(obj, "solution"):
        obj.board = puzzle_str
        obj.solution = solution_str
    elif hasattr(obj, "problem_board") and hasattr(obj, "solution_board"):
        obj.problem_board = puzzle_str
        obj.solution_board = solution_str
    else:
        raise AttributeError(
            "Modelo SudokuPuzzle não possui campos esperados "
            "(board/solution OU problem_board/solution_board)."
        )


def _validate_grid(s: str):
    if not isinstance(s, str) or len(s) != 81 or any(c not in "0123456789" for c in s):
        raise ValueError("string do tabuleiro deve ter 81 dígitos (0–9).")


class Command(BaseCommand):
    help = "Gera e salva os puzzles de Sudoku para o dia atual."

    def add_arguments(self, parser):
        parser.add_argument(
            "--difficulties",
            type=str,
            default="easy,medium,hard",
            help="Lista separada por vírgulas (ex.: easy,medium,hard)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) Data local (evita off-by-one por UTC)
        today = timezone.localdate()

        # 2) Normaliza dificuldades (aceita 'difficult' e mapeia para 'hard')
        diffs = [
            d.strip().lower().replace("difficult", "hard")
            for d in options["difficulties"].split(",")
            if d.strip()
        ]

        created_count = 0

        for diff in diffs:
            # 3) Idempotência: não recria se já existir
            exists = SudokuPuzzle.objects.filter(date=today, difficulty=diff).exists()
            if exists:
                self.stdout.write(self.style.WARNING(f"[{today}] {diff}: já existe. Pulando."))
                continue

            self.stdout.write(f"Gerando puzzle nível {diff} para {today}…")
            try:
                # 4) Geração
                puzzle_str, solution_str = generate_puzzle(diff)

                # 5) Validação mínima (81 chars 0–9)
                _validate_grid(puzzle_str)
                _validate_grid(solution_str)

                # 6) Criação compatível com campos diferentes
                sp = SudokuPuzzle(date=today, difficulty=diff)
                _set_board_fields(sp, puzzle_str, solution_str)
                sp.save()

                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✔ Criado: {today} {diff}"))
            except Exception as e:
                # rollback automático por @transaction.atomic
                self.stderr.write(self.style.ERROR(f"✖ Erro ao gerar {diff}: {e}"))
                # Mostra traceback em modo verboso
                if options.get("verbosity", 1) > 1:
                    import traceback

                    traceback.print_exc(file=sys.stderr)

        if created_count:
            self.stdout.write(self.style.SUCCESS(f"{created_count} puzzle(s) criados para {today}."))
        else:
            self.stdout.write(self.style.SUCCESS("Nenhum puzzle novo precisou ser criado."))
