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
#  FUNÇÃO USADA NOS SEUS TESTES
# ----------------------------------------------------------------------
def is_solution_valid(solutionStr):
    """
    Valida uma solução de Sudoku 9x9 no formato string (81 chars).
    - Deve ter exatamente 81 dígitos.
    - Todos caracteres devem ser números 1-9 (sem zeros).
    - Não pode ter duplicações em linhas, colunas ou boxes 3x3.
    """
    # Tamanho correto?
    if not isinstance(solutionStr, str) or len(solutionStr) != 81:
        return False

    # Todos dígitos 1..9?
    if any(c not in "123456789" for c in solutionStr):
        return False

    # Checar linhas
    for r in range(9):
        row = solutionStr[r * 9:(r + 1) * 9]
        if len(set(row)) != 9:
            return False

    # Checar colunas
    for c in range(9):
        col = solutionStr[c:81:9]
        if len(set(col)) != 9:
            return False

    # Checar boxes 3x3
    for br in range(3):
        for bc in range(3):
            box = []
            start = br * 27 + bc * 3
            box += solutionStr[start:start + 3]
            box += solutionStr[start + 9:start + 12]
            box += solutionStr[start + 18:start + 21]

            if len(set(box)) != 9:
                return False

    return True


# ----------------------------------------------------------------------
#  PADRONIZA acesso a campos do puzzle
# ----------------------------------------------------------------------
def _get_boards(p):
    """Retorna (problemStr, solutionStr) independente do modelo."""
    if hasattr(p, "problem_board") and hasattr(p, "solution_board"):
        return p.problem_board, p.solution_board

    if hasattr(p, "board") and hasattr(p, "solution"):
        return p.board, p.solution

    raise AttributeError("SudokuPuzzle não possui campos esperados.")


def _set_boards(p, problemStr, solutionStr):
    """Salva boards independente do modelo."""
    if hasattr(p, "problem_board") and hasattr(p, "solution_board"):
        p.problem_board = problemStr
        p.solution_board = solutionStr
        return

    if hasattr(p, "board") and hasattr(p, "solution"):
        p.board = problemStr
        p.solution = solutionStr
        return

    raise AttributeError("SudokuPuzzle não possui campos esperados.")


# ----------------------------------------------------------------------
#  VIEW PRINCIPAL DO JOGO
# ----------------------------------------------------------------------
@login_required
def play_sudoku(request, difficulty):

    difficultyMap = {
        "easy": "easy", "medium": "medium", "hard": "hard",
        "fácil": "easy", "médio": "medium", "difícil": "hard",
    }
    norm = difficultyMap.get(str(difficulty).lower(), "easy")

    today = timezone.localdate()

    # Progresso
    progress, _ = UserSudokuProgress.objects.get_or_create(user=request.user)
    progress.check_and_reset_progress()

    # Bloqueios
    if norm == "medium" and not progress.completed_easy:
        return redirect("sudoku:play_sudoku", difficulty="easy")

    if norm == "hard" and not (progress.completed_easy and progress.completed_medium):
        return redirect(
            "sudoku:play_sudoku",
            difficulty="medium" if progress.completed_easy else "easy"
        )

    # Puzzle do dia
    puzzle = SudokuPuzzle.objects.filter(date=today, difficulty=norm).first()

    if puzzle is None:
        problemStr, solutionStr = generate_puzzle(norm)

        with transaction.atomic():
            puzzle = SudokuPuzzle(date=today, difficulty=norm)
            _set_boards(puzzle, problemStr, solutionStr)
            puzzle.save()

    problemStr, _ = _get_boards(puzzle)

    context = {
        "puzzle": puzzle,
        "difficulty": norm,
        "progress": progress,
        "problem_board_json": json.dumps(problemStr),
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

        if not puzzleId or not userSolutionStr or len(userSolutionStr) != 81:
            return HttpResponseBadRequest("Dados inválidos.")

        puzzle = get_object_or_404(SudokuPuzzle, id=puzzleId)

        # Carrega solução oficial
        _, solutionStr = _get_boards(puzzle)
        solutionStr = ''.join(c for c in solutionStr if c.isdigit())

        if len(solutionStr) != 81:
            return JsonResponse(
                {"success": False, "message": "Erro interno: solução inválida no banco."},
                status=500
            )

        # >>>> AQUI GARANTIMOS QUE A SOLUÇÃO DO USUÁRIO TAMBÉM É VÁLIDA <<<<
        if not is_solution_valid(userSolutionStr):
            return JsonResponse({"success": False, "message": "Solução inválida."})

        # Comparação final
        if userSolutionStr == solutionStr:

            progress = UserSudokuProgress.objects.get(user=request.user)
            nextLevel = None

            completionTime = None
            if elapsedSeconds is not None:
                try:
                    completionTime = timedelta(seconds=int(elapsedSeconds))
                except ValueError:
                    pass

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

        return JsonResponse({"success": False, "message": "Solução incorreta."})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
