from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
from datetime import timedelta
import json

from .models import SudokuPuzzle, UserSudokuProgress
from .sudoku_generator import generate_puzzle


def is_solution_valid(board_str):
    """
    Verifica se a string de 81 caracteres (submetida pelo usuário) é uma solução válida.
    """
    if len(board_str) != 81 or not board_str.isdigit():
        return False

    # 1) Não pode haver zeros (células vazias) numa solução final.
    if "0" in board_str:
        return False

    board = []
    try:
        for i in range(0, 81, 9):
            row = [int(c) for c in board_str[i:i+9]]
            board.append(row)
    except ValueError:
        return False

    def has_duplicates(block):
        return len(set(block)) != 9

    # 2) Linhas
    for r in range(9):
        if has_duplicates(board[r]):
            return False

    # 3) Colunas
    for c in range(9):
        col = [board[r][c] for r in range(9)]
        if has_duplicates(col):
            return False

    # 4) Blocos 3x3
    for br in range(3):
        for bc in range(3):
            block = []
            for r in range(br*3, br*3+3):
                for c in range(bc*3, bc*3+3):
                    block.append(board[r][c])
            if has_duplicates(block):
                return False

    return True


def _get_boards(p):
    """Retorna (problem_str, solution_str) independente do esquema do modelo."""
    if hasattr(p, "problem_board") and hasattr(p, "solution_board"):
        return p.problem_board, p.solution_board
    if hasattr(p, "board") and hasattr(p, "solution"):
        return p.board, p.solution
    raise AttributeError("SudokuPuzzle não possui campos esperados de tabuleiro.")


def _set_boards(p, problem_str, solution_str):
    """Seta os campos corretos conforme o esquema do modelo."""
    if hasattr(p, "problem_board") and hasattr(p, "solution_board"):
        p.problem_board = problem_str
        p.solution_board = solution_str
        return
    if hasattr(p, "board") and hasattr(p, "solution"):
        p.board = problem_str
        p.solution = solution_str
        return
    raise AttributeError("SudokuPuzzle não possui campos esperados de tabuleiro.")


@login_required
def play_sudoku(request, difficulty):
    print(f"🔹 Entrou na view play_sudoku (dificuldade={difficulty})")

    difficulty_map = {
        "easy": "easy", "medium": "medium", "hard": "hard",
        "fácil": "easy", "médio": "medium", "difícil": "hard",
    }
    dnorm = difficulty_map.get(str(difficulty).lower(), "easy")

    today = timezone.localdate()

    # progresso do usuário
    progress, _ = UserSudokuProgress.objects.get_or_create(user=request.user)
    print("🟢 Progresso carregado:", progress)
    progress.check_and_reset_progress()

    # bloqueios por progresso
    if dnorm == "medium" and not progress.completed_easy:
        return redirect("sudoku:play_sudoku", difficulty="easy")
    if dnorm == "hard" and not (progress.completed_easy and progress.completed_medium):
        return redirect("sudoku:play_sudoku", difficulty="medium" if progress.completed_easy else "easy")

    # busca ou gera o puzzle do dia
    puzzle = SudokuPuzzle.objects.filter(date=today, difficulty=dnorm).first()
    if puzzle is None:
        print("❌ Puzzle de hoje não existe. Gerando on-demand…")
        problem_str, solution_str = generate_puzzle(dnorm)
        with transaction.atomic():
            puzzle = SudokuPuzzle(date=today, difficulty=dnorm)
            _set_boards(puzzle, problem_str, solution_str)
            puzzle.save()
        print("✔ Puzzle gerado e salvo:", puzzle)
    else:
        print("🧩 Puzzle encontrado:", puzzle)

    problem_board_string, _ = _get_boards(puzzle)

    # 👇 O HTML usa json_script com o id "problem-board"
    #    Enviamos JSON mesmo (string de 81 chars) para casar com o template.
    context = {
        "puzzle": puzzle,
        "difficulty": dnorm,
        "progress": progress,
        "problem_board_json": json.dumps(problem_board_string),  # <- chave certa para o template
    }

    print("🔹 Tentando renderizar sudoku/sudoku.html")
    return render(request, "sudoku/sudoku.html", context)


@login_required
@require_POST
def check_solution(request):
    try:
        data = json.loads(request.body)
        puzzle_id = data.get("puzzle_id")
        user_solution_str = data.get("solution")
        elapsed_seconds = data.get("elapsed_seconds")

        if not puzzle_id or not user_solution_str or len(user_solution_str) != 81:
            return HttpResponseBadRequest("Dados inválidos.")

        # a página só permite envio se todas as células foram preenchidas
        # e o JS monta string com dígitos 1-9 (sem '.')
        puzzle = get_object_or_404(SudokuPuzzle, id=puzzle_id)

        if is_solution_valid(user_solution_str):
            progress = UserSudokuProgress.objects.get(user=request.user)
            next_level = None
            completion_time = None

            if elapsed_seconds is not None:
                try:
                    completion_time = timedelta(seconds=int(elapsed_seconds))
                except ValueError:
                    completion_time = None

            if puzzle.difficulty == "easy" and not progress.completed_easy:
                progress.completed_easy = True
                if completion_time:
                    progress.easy_completion_time = completion_time
                next_level = "medium"

            elif puzzle.difficulty == "medium" and not progress.completed_medium:
                progress.completed_medium = True
                if completion_time:
                    progress.medium_completion_time = completion_time
                next_level = "hard"

            elif puzzle.difficulty == "hard" and not progress.completed_hard:
                progress.completed_hard = True
                if completion_time:
                    progress.hard_completion_time = completion_time

            progress.save()
            return JsonResponse({"success": True, "next_level": next_level})
        else:
            return JsonResponse({"success": False, "message": "Solução incorreta pelas regras do Sudoku."})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
