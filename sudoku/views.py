from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import SudokuPuzzle, UserSudokuProgress
import json
import datetime
from datetime import timedelta

def is_solution_valid(board_str):
    if len(board_str) != 81 or not board_str.isdigit():
        return False

    board = []
    try:
        for i in range(0, 81, 9):
            row = [int(c) for c in board_str[i:i+9]]
            if 0 in row: 
                return False
            board.append(row)
    except ValueError:
        return False

    def has_duplicates(block):
        return len(set(block)) != 9

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
    today = timezone.now().date()
    
    progress, created = UserSudokuProgress.objects.get_or_create(user=request.user)
    
    progress.check_and_reset_progress()

    if difficulty == 'medium' and not progress.completed_easy:
        return redirect('sudoku:play_sudoku', difficulty='easy') 
    
    if difficulty == 'difficult' and not (progress.completed_easy and progress.completed_medium):
        if not progress.completed_easy:
            return redirect('sudoku:play_sudoku', difficulty='easy') 
        else:
            return redirect('sudoku:play_sudoku', difficulty='medium') 
 
    try:
        puzzle = SudokuPuzzle.objects.get(date=today, difficulty=difficulty)
    except SudokuPuzzle.DoesNotExist:
        return render(request, 'sudoku/sudoku_error.html', {'message': 'O puzzle de hoje ainda não foi gerado. Avise a administração.'})
    
    context = {
        'puzzle': puzzle,
        'problem_board_json': puzzle.problem_board, 
        'difficulty': difficulty,
        'progress': progress,
    }
    return render(request, 'sudoku/sudoku.html', context)

@login_required
@require_POST
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
            progress.check_and_reset_progress() 
            
            next_level = None
            completion_time = None
            
            if elapsed_seconds is not None:
                try:
                    completion_time = datetime.timedelta(seconds=int(elapsed_seconds))
                except ValueError:
                    pass

            difficulty = puzzle.difficulty
            completed_attr = f'completed_{difficulty}'
            time_attr = f'{difficulty}_completion_time'

            if not getattr(progress, completed_attr):
            
                setattr(progress, completed_attr, True)
            
                if completion_time:
                    setattr(progress, time_attr, completion_time)
                
                if difficulty == 'easy':
                    next_level = 'medium'
                elif difficulty == 'medium':
                    next_level = 'difficult'
                
                progress.save()
                
                return JsonResponse({'success': True, 'next_level': next_level})
            else:
                return JsonResponse({'success': False, 'message': 'Puzzle já completado hoje.'})
        else:
            return JsonResponse({'success': False, 'message': 'Solução incorreta pelas regras do Sudoku.'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro interno: {str(e)}'}, status=500)