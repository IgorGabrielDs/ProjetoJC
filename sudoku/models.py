from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SudokuPuzzle(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Fácil'),
        ('medium', 'Médio'),
        ('difficult', 'Difícil'),
    ]
    
    date = models.DateField(default=timezone.localdate)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
   
    problem_board = models.CharField(max_length=81)
   
    solution_board = models.CharField(max_length=81)

    class Meta:
        unique_together = ('date', 'difficulty')

    def __str__(self):
        return f"Sudoku {self.get_difficulty_display()} - {self.date}"

class UserSudokuProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="sudoku_progress")
    last_puzzle_date = models.DateField(default=timezone.localdate)
    completed_easy = models.BooleanField(default=False)
    completed_medium = models.BooleanField(default=False)
    completed_difficult = models.BooleanField(default=False)

    easy_completion_time = models.DurationField(null=True, blank=True)
    medium_completion_time = models.DurationField(null=True, blank=True)
    difficult_completion_time = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"Progresso de {self.user.username}"
    
    def check_and_reset_progress(self):
        today = timezone.now().date()
        if self.last_puzzle_date < today:
            self.last_puzzle_date = today
            self.completed_easy = False
            self.completed_medium = False
            self.completed_difficult = False
   
            self.easy_completion_time = None
            self.medium_completion_time = None
            self.difficult_completion_time = None
            
            self.save()
