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


# ----------------------------------------------------------------------
#  PADRONIZA acesso a campos do puzzle
# ----------------------------------------------------------------------
def _get_boards(p):
    """Retorna (problem_str, solution_str) independente do modelo."""
    if hasattr(p, "problem_board") and hasattr(p, "solution_board"):
        return p.problem_board, p.solution_board

    if hasattr(p, "board") and hasattr(p, "solution"):
        return p.board, p.solution

    raise AttributeError("SudokuPuzzle não possui os campos esperados.")


def _set_boards(p, problem_str, solution_str):
    """Salva os boards independente do modelo."""
    if hasattr(p, "problem_board") and hasattr(p, "solution_board"):
        p.problem_board = problem_str
        p.solution_board = solution_str
        return

    if hasattr(p, "board") and hasattr(p, "solution"):
        p.board = problem_str
        p.solution = solution_str
        return

    raise AttributeError("SudokuPuzzle não possui os campos esperados.")


# ----------------------------------------------------------------------
#  VIEW PRINCIPAL DO JOGO
# ----------------------------------------------------------------------
@login_required
def play_sudoku(request, difficulty):

    # Normalização de entrada
    difficulty_map = {
        "easy": "easy", "medium": "medium", "hard": "hard",
        "fácil": "easy", "médio": "medium", "difícil": "hard",
    }
    dnorm = difficulty_map.get(str(difficulty).lower(), "easy")

    today = timezone.localdate()

    # Progresso do usuário
    progress, _ = UserSudokuProgress.objects.get_or_create(user=request.user)
    progress.check_and_reset_progress()

    # BLOQUEIOS DE ACESSO
    if dnorm == "medium" and not progress.completed_easy:
        return redirect("sudoku:play_sudoku", difficulty="easy")

    if dnorm == "hard" and not (progress.completed_easy and progress.completed_medium):
        return redirect("sudoku:play_sudoku",
                        difficulty="medium" if progress.completed_easy else "easy")

    # BUSCA PUZZLE DO DIA
    puzzle = SudokuPuzzle.objects.filter(date=today, difficulty=dnorm).first()

    # Se não existe, gera um novo
    if puzzle is None:
        problem_str, solution_str = generate_puzzle(dnorm)

        with transaction.atomic():
            puzzle = SudokuPuzzle(date=today, difficulty=dnorm)
            _set_boards(puzzle, problem_str, solution_str)
            puzzle.save()

    problem_board_string, _ = _get_boards(puzzle)

    context = {
        "puzzle": puzzle,
        "difficulty": dnorm,
        "progress": progress,
        "problem_board_json": json.dumps(problem_board_string),
    }

    return render(request, "sudoku/sudoku.html", context)


# ----------------------------------------------------------------------
#  VERIFICAÇÃO DA SOLUÇÃO DO USUÁRIO
# ----------------------------------------------------------------------
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

        puzzle = get_object_or_404(SudokuPuzzle, id=puzzle_id)

        # Carrega solução oficial
        _, solution_str = _get_boards(puzzle)

        solution_str = ''.join(c for c in solution_str if c.isdigit())
        if len(solution_str) != 81:
            return JsonResponse({
                "success": False,
                "message": "Erro interno: solução inválida no banco."
            }, status=500)

        # ---------------------------------------------------------------------------------
        # COMPARA SOLUÇÃO
        # ---------------------------------------------------------------------------------
        if user_solution_str == solution_str:

            progress = UserSudokuProgress.objects.get(user=request.user)
            next_level = None

            # tempo
            completion_time = None
            if elapsed_seconds is not None:
                try:
                    completion_time = timedelta(seconds=int(elapsed_seconds))
                except ValueError:
                    pass

            # MARCA PROGRESSO
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

        # Se ERROU:
        return JsonResponse({"success": False, "message": "Solução incorreta."})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)