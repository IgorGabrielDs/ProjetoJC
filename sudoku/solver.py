# sudoku/solver.py
from typing import List, Optional, Tuple

Board = List[List[int]]

def _find_empty(board: Board) -> Optional[Tuple[int, int]]:
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None

def _valid(board: Board, r: int, c: int, v: int) -> bool:
    # linha
    for x in range(9):
        if board[r][x] == v:
            return False
    # coluna
    for y in range(9):
        if board[y][c] == v:
            return False
    # box 3x3
    br = (r // 3) * 3
    bc = (c // 3) * 3
    for y in range(br, br + 3):
        for x in range(bc, bc + 3):
            if board[y][x] == v:
                return False
    return True

def _solve_inplace(board: Board) -> bool:
    empty = _find_empty(board)
    if not empty:
        return True
    r, c = empty
    # ordem determinística 1..9
    for v in range(1, 10):
        if _valid(board, r, c, v):
            board[r][c] = v
            if _solve_inplace(board):
                return True
            board[r][c] = 0
    return False

def solve(board: Board) -> Optional[Board]:
    """Resolve um tabuleiro (0 = vazio). Retorna solução ou None."""
    if not isinstance(board, list) or len(board) != 9 or any(len(row) != 9 for row in board):
        return None
    work = [row[:] for row in board]
    ok = _solve_inplace(work)
    return work if ok else None
