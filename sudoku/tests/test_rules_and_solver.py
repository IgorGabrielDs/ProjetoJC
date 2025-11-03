import pytest

pytestmark = pytest.mark.django_db

# --- Helpers locais (cópia das validações) ---
def valid_rows(board):
    for r in range(9):
        seen = set()
        for c in range(9):
            v = board[r][c]
            if v == 0:
                continue
            if v < 1 or v > 9 or v in seen:
                return False
            seen.add(v)
    return True

def valid_cols(board):
    for c in range(9):
        seen = set()
        for r in range(9):
            v = board[r][c]
            if v == 0:
                continue
            if v < 1 or v > 9 or v in seen:
                return False
            seen.add(v)
    return True

def valid_boxes(board):
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            seen = set()
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    v = board[r][c]
                    if v == 0:
                        continue
                    if v < 1 or v > 9 or v in seen:
                        return False
                    seen.add(v)
    return True

def is_complete(board):
    return all(board[r][c] != 0 for r in range(9) for c in range(9))

# --- Tests ---
def test_known_solution_obeys_rules(known_solution):
    assert valid_rows(known_solution)
    assert valid_cols(known_solution)
    assert valid_boxes(known_solution)
    assert is_complete(known_solution)

def test_known_puzzle_is_consistent(known_puzzle):
    assert valid_rows(known_puzzle)
    assert valid_cols(known_puzzle)
    assert valid_boxes(known_puzzle)

def test_solver_solves_known_puzzle(sudoku_modules, known_puzzle, known_solution):
    solver_mod = sudoku_modules["solver"]
    if solver_mod is None:
        pytest.skip("Módulo de solver não encontrado (sudoku.solver/core/utils/logic).")

    solver_fn = None
    used_name = None
    for candidate in ("solve", "resolver", "solve_puzzle", "solve_grid"):
        fn = getattr(solver_mod, candidate, None)
        if callable(fn):
            solver_fn = fn
            used_name = candidate
            break

    if solver_fn is None:
        pytest.skip("Nenhuma função pública de solver encontrada (solve/resolver/...).")

    board_in = [row[:] for row in known_puzzle]
    solved = solver_fn(board_in)

    assert solved is not None, f"{used_name} retornou None"
    assert solved == known_solution, f"{used_name} não obteve a solução esperada"

    assert valid_rows(solved)
    assert valid_cols(solved)
    assert valid_boxes(solved)
    assert is_complete(solved)
