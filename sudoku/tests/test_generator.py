import pytest

pytestmark = pytest.mark.django_db

def _pick_generator(gen_mod):
    for name in ["generate_puzzle", "gerar_puzzle", "generate", "gerar", "create_puzzle"]:
        fn = getattr(gen_mod, name, None)
        if callable(fn):
            return fn, name
    return None, None

def _coerce_result_to_tuple(result):
    """
    Aceita diferentes formatos retornados pelo gerador:
    - (puzzle, solution)
    - {"puzzle": ..., "solution": ...}
    - apenas puzzle (quando solução é interna): nesse caso retornamos (puzzle, None)
    """
    puzzle, solution = None, None
    if isinstance(result, (list, tuple)):
        if len(result) == 2:
            puzzle, solution = result
        else:
            puzzle = result
    elif isinstance(result, dict):
        puzzle = result.get("puzzle")
        solution = result.get("solution")
    else:
        puzzle = result
    return puzzle, solution

# --- helpers locais para validar regras ---
def _valid_rows(board):
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

def _valid_cols(board):
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

def _valid_boxes(board):
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

def _is_complete(board):
    return all(board[r][c] != 0 for r in range(9) for c in range(9))


def test_generator_returns_valid_grid_structure(sudoku_modules):
    gen_mod = sudoku_modules["gen"]
    if gen_mod is None:
        pytest.skip("Módulo de gerador não encontrado (sudoku.generator/generate/core/utils).")

    gen_fn, gen_name = _pick_generator(gen_mod)
    if gen_fn is None:
        pytest.skip("Função geradora não encontrada (generate_puzzle/gerar_puzzle/...).")

    res = gen_fn()
    puzzle, solution = _coerce_result_to_tuple(res)

    assert puzzle is not None, f"{gen_name} não retornou puzzle"
    assert isinstance(puzzle, list) and len(puzzle) == 9
    assert all(isinstance(row, list) and len(row) == 9 for row in puzzle)

    flat = [v for row in puzzle for v in row]
    assert all(isinstance(v, int) for v in flat)
    assert all((v == 0) or (1 <= v <= 9) for v in flat)


def test_generator_puzzle_is_solvable_if_solver_exists(sudoku_modules):
    gen_mod = sudoku_modules["gen"]
    solver_mod = sudoku_modules["solver"]

    if gen_mod is None:
        pytest.skip("Módulo de gerador não encontrado.")
    if solver_mod is None:
        pytest.skip("Módulo de solver não encontrado — não é possível verificar resolubilidade.")

    gen_fn, _ = _pick_generator(gen_mod)
    if gen_fn is None:
        pytest.skip("Função geradora não encontrada.")

    solver_fn = None
    for name in ["solve", "resolver", "solve_puzzle", "solve_grid"]:
        fn = getattr(solver_mod, name, None)
        if callable(fn):
            solver_fn = fn
            break
    if solver_fn is None:
        pytest.skip("Função de solver não encontrada.")

    puzzle, solution = _coerce_result_to_tuple(gen_fn())
    assert puzzle is not None

    solved = solver_fn([row[:] for row in puzzle])
    assert solved is not None, "Gerou puzzle insolúvel"

    # Confere regras na solução
    assert _valid_rows(solved)
    assert _valid_cols(solved)
    assert _valid_boxes(solved)
    assert _is_complete(solved)