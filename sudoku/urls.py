from django.urls import path
from . import views

app_name = 'sudoku'

urlpatterns = [
    path('', views.play_sudoku, {'difficulty': 'easy'}, name='sudoku_start'),
    path('<str:difficulty>/', views.play_sudoku, name='play_sudoku'),
    path('check/', views.check_solution, name='check_solution'),
]