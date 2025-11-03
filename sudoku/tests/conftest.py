import importlib
import types
import pytest

# ---- Utilidades comuns para os testes ----

PUZZLE_KNOWN = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

SOLUTION_KNOWN = [
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

def try_import(module_candidates):
    """
    Tenta importar um dos módulos candidatos e retorna o primeiro que existir.
    """
    for name in module_candidates:
        try:
            return importlib.import_module(name)
        except Exception:
            continue
    return None

def find_first_attr(mod: types.ModuleType, names):
    """
    Procura, no módulo dado, o primeiro atributo com um dos 'names'.
    Retorna (callable, name) ou (None, None).
    """
    if not mod:
        return None, None
    for nm in names:
        fn = getattr(mod, nm, None)
        if callable(fn):
            return fn, nm
    return None, None

@pytest.fixture(scope="session")
def sudoku_modules():
    """
    Descobre módulos prováveis do app sudoku:
    - views (para URLs)
    - solver/utils/core (para solve/is_valid)
    - generator (para gerar puzzle)
    """
    views_mod = try_import(["sudoku.views"])
    solver_mod = try_import(["sudoku.solver", "sudoku.core", "sudoku.utils", "sudoku.logic"])
    gen_mod    = try_import(["sudoku.generator", "sudoku.generate", "sudoku.core", "sudoku.utils"])
    return {"views": views_mod, "solver": solver_mod, "gen": gen_mod}

# Validações de Sudoku (puras, para reutilizar nos testes)
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
            for r in range(br, br+3):
                for c in range(bc, bc+3):
                    v = board[r][c]
                    if v == 0:
                        continue
                    if v < 1 or v > 9 or v in seen:
                        return False
                    seen.add(v)
    return True

def is_complete(board):
    return all(board[r][c] != 0 for r in range(9) for c in range(9))

@pytest.fixture
def known_puzzle():
    # Deep copy simples
    return [row[:] for row in PUZZLE_KNOWN]

@pytest.fixture
def known_solution():
    return [row[:] for row in SOLUTION_KNOWN]
