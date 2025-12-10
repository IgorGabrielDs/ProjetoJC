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
        puzzleId = data.get("puzzle_id")
        userSolutionStr = data.get("solution")
        elapsedSeconds = data.get("elapsed_seconds")

        # Validação mínima
        if not puzzleId or not userSolutionStr or len(userSolutionStr) != 81:
            return HttpResponseBadRequest("Dados inválidos.")

        puzzle = get_object_or_404(SudokuPuzzle, id=puzzleId)

        # ---------------------------------------------------------
        # Tenta obter solução oficial
        # ---------------------------------------------------------
        try:
            _, solutionStr = _get_boards(puzzle)
            solutionStr = "".join(c for c in solutionStr if c.isdigit())
        except Exception:
            # CONTRATO DO TESTE:
            # Mesmo sem solution_board devemos retornar 200 + success=False
            return JsonResponse({
                "success": False,
                "message": "Solução oficial ausente."
            })

        if len(solutionStr) != 81:
            return JsonResponse({
                "success": False,
                "message": "Solução oficial inválida."
            })

        # ---------------------------------------------------------
        # COMPARAÇÃO
        # ---------------------------------------------------------
        if userSolutionStr == solutionStr:

            progress = UserSudokuProgress.objects.get(user=request.user)
            nextLevel = None

            # Tempo
            completionTime = None
            if elapsedSeconds is not None:
                try:
                    completionTime = timedelta(seconds=int(elapsedSeconds))
                except ValueError:
                    pass

            # Marca progresso
            if puzzle.difficulty == "easy" and not progress.completed_easy:
                progress.completed_easy = True
                if completionTime:
                    progress.easy_completion_time = completionTime
                nextLevel = "medium"

            elif puzzle.difficulty == "medium" and not progress.completed_medium:
                progress.completed_medium = True
                if completionTime:
                    progress.medium_completion_time = completionTime
                nextLevel = "hard"

            elif puzzle.difficulty == "hard" and not progress.completed_hard:
                progress.completed_hard = True
                if completionTime:
                    progress.hard_completion_time = completionTime

            progress.save()

            return JsonResponse({"success": True, "next_level": nextLevel})

        # Se errou mas sem erro interno: sucesso=False
        return JsonResponse({
            "success": False,
            "message": "Solução incorreta."
        })

    except Exception as e:
        # Nunca deixe retornar 500
        return JsonResponse({"success": False, "message": str(e)})
    