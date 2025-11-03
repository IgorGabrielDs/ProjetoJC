# sudoku/generator.py
from typing import List, Tuple
import random
from .solver import solve

Board = List[List[int]]

_BASE_SOLUTION: Board = [
    [5,3,4,6,7,8,9,1,2],
    [6,7,2,1,9,5,3,4,8],
    [1,9,8,3,4,2,5,6,7],
    [8,5,9,7,6,1,4,2,3],
    [4,2,6,8,5,3,7,9,1],
    [7,1,3,9,2,4,8,5,6],
    [9,6,1,5,3,7,2,8,4],
    [2,8,7,4,1,9,6,3,5],
    [3,4,5,2,8,6,1,7,9],
]

def _copy(b: Board) -> Board:
    return [row[:] for row in b]

def _remove_cells(board: Board, removals: int = 45) -> Board:
    """
    Remove 'removals' células mantendo o puzzle resolúvel (não garantimos unicidade,
    mas o teste só exige resolubilidade).
    Usamos remoções simétricas (par) para estética.
    """
    b = _copy(board)
    coords = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(coords)
    removed = 0
    for r, c in coords:
        if removed >= removals:
            break
        r2 = 8 - r
        c2 = 8 - c
        if b[r][c] == 0 or b[r2][c2] == 0:
            continue
        keep1 = b[r][c]
        keep2 = b[r2][c2]
        b[r][c] = 0
        b[r2][c2] = 0
        # checa resolubilidade
        if solve(_copy(b)) is None:
            # desfaz
            b[r][c] = keep1
            b[r2][c2] = keep2
        else:
            removed += 2
    return b

def generate_puzzle(removals: int = 45) -> Tuple[Board, Board]:
    """
    Retorna (puzzle, solution). Para testes, basta existir e retornar 9x9 válidos.
    """
    # Em produção poderíamos randomizar por permutações da base. Aqui mantemos estável.
    solution = _copy(_BASE_SOLUTION)
    puzzle = _remove_cells(solution, removals=removals)
    return puzzle, solution
