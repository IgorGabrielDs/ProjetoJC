# sudoku/views.py (REMOVIDO json.dumps para corrigir a aspas)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import SudokuPuzzle, UserSudokuProgress
import json
from datetime import timedelta


def is_solution_valid(board_str):
    """
    Verifica se a string de 81 caracteres (submetida pelo usuário) é uma solução válida.
    """
    if len(board_str) != 81 or not board_str.isdigit():
        return False

    # 1. Checa se há zeros (células vazias): Não pode haver para uma solução final.
    if '0' in board_str: 
        return False
             
    board = []
    try:
        for i in range(0, 81, 9):
            row = [int(c) for c in board_str[i:i+9]]
            board.append(row)
    except ValueError:
        return False

    def has_duplicates(block):
        """Verifica se há repetição em um bloco de 9 números (1-9)."""
        return len(set(block)) != 9

    # 2. Checagem de Linhas
    for r in range(9):
        if has_duplicates(board[r]):
            return False
    for c in range(9):
        col = [board[r][c] for r in range(9)]
        if has_duplicates(col):
            return False
    for br in range(3):
        for bc in range(3):
            block = []
            for r in range(br*3, br*3 + 3):
                for c in range(bc*3, bc*3 + 3):
                    block.append(board[r][c])
            if has_duplicates(block):
                return False
    return True


@login_required
def play_sudoku(request, difficulty):
    print(f"🔹 Entrou na view play_sudoku (dificuldade={difficulty})")

    today = timezone.now().date()
    progress, created = UserSudokuProgress.objects.get_or_create(user=request.user)
    print("🟢 Progresso carregado:", progress)

    progress.check_and_reset_progress()

    if difficulty == 'medium' and not progress.completed_easy:
        print("🔸 Redirecionando para easy (não completou fácil ainda)")
        return redirect('play_sudoku', difficulty='easy')

    if difficulty == 'difficult' and not (progress.completed_easy and progress.completed_medium):
        if not progress.completed_easy:
            print("🔸 Redirecionando para easy (não completou fácil ainda)")
            return redirect('sudoku:play_sudoku', difficulty='easy') 
        else:
            print("🔸 Redirecionando para medium (não completou médio ainda)")
            return redirect('play_sudoku', difficulty='medium')

    try:
        puzzle = SudokuPuzzle.objects.get(date=today, difficulty=difficulty)
        print("🧩 Puzzle encontrado:", puzzle)
    except SudokuPuzzle.DoesNotExist:
        print("❌ Puzzle de hoje não existe.")
        return render(request, 'sudoku/sudoku_error.html', {
            'message': 'O puzzle de hoje ainda não foi gerado. Avise a administração.'
        })
    
    context = {
        'puzzle': puzzle,
        'problem_board_string': puzzle.problem_board, 
        'difficulty': difficulty,
        'progress': progress,
    }

    print("🔹 Tentando renderizar sudoku/sudoku.html")
    return render(request, 'sudoku/sudoku.html', context)



@login_required
@require_POST
def check_solution(request):
    try:
        data = json.loads(request.body)
        puzzle_id = data.get('puzzle_id')
        user_solution_str = data.get('solution')
        elapsed_seconds = data.get('elapsed_seconds')

        if not puzzle_id or not user_solution_str or len(user_solution_str) != 81:
            return HttpResponseBadRequest("Dados inválidos.")

        puzzle = get_object_or_404(SudokuPuzzle, id=puzzle_id)

        if is_solution_valid(user_solution_str):
            progress = UserSudokuProgress.objects.get(user=request.user)
            next_level = None
            completion_time = None

            if elapsed_seconds is not None:
                try:
                    completion_time = timedelta(seconds=int(elapsed_seconds))
                except ValueError:
                    pass

            if puzzle.difficulty == 'easy' and not progress.completed_easy:
                progress.completed_easy = True
                if completion_time:
                    progress.easy_completion_time = completion_time
                next_level = 'medium'

            elif puzzle.difficulty == 'medium' and not progress.completed_medium:
                progress.completed_medium = True
                if completion_time:
                    progress.medium_completion_time = completion_time
                next_level = 'difficult'

            elif puzzle.difficulty == 'difficult' and not progress.completed_difficult:
                progress.completed_difficult = True
                if completion_time:
                    progress.difficult_completion_time = completion_time

            progress.save()
            return JsonResponse({'success': True, 'next_level': next_level})
        else:
            return JsonResponse({'success': False, 'message': 'Solução incorreta pelas regras do Sudoku.'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
