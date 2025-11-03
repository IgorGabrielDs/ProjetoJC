import pytest

pytestmark = pytest.mark.django_db

# Copiamos a função para importar do módulo real:
views = pytest.importorskip("sudoku.views", reason="sudoku.views não encontrado")
is_solution_valid = views.is_solution_valid

# Solução canônica 9x9 "achatada" (81 dígitos) — válida
SOLUTION_STR = (
    "534678912"
    "672195348"
    "198342567"
    "859761423"
    "426853791"
    "713924856"
    "961537284"
    "287419635"
    "345286179"
)

def test_is_solution_valid_accepts_perfect_solution():
    assert is_solution_valid(SOLUTION_STR) is True

def test_is_solution_valid_rejects_zeros():
    s = list(SOLUTION_STR)
    s[0] = "0"
    assert is_solution_valid("".join(s)) is False

def test_is_solution_valid_wrong_length():
    assert is_solution_valid(SOLUTION_STR[:-1]) is False
    assert is_solution_valid(SOLUTION_STR + "1") is False

def test_is_solution_valid_nondigits():
    s = list(SOLUTION_STR)
    s[10] = "x"
    assert is_solution_valid("".join(s)) is False

def test_is_solution_valid_duplicate_in_row():
    # duplica o primeiro dígito da linha 1
    s = list(SOLUTION_STR)
    s[1] = s[0]
    assert is_solution_valid("".join(s)) is False

def test_is_solution_valid_duplicate_in_col():
    # duplica o dígito da mesma coluna (col 0: índices 0,9,18,...)
    s = list(SOLUTION_STR)
    s[9] = s[0]
    assert is_solution_valid("".join(s)) is False

def test_is_solution_valid_duplicate_in_box():
    # altera dentro do primeiro bloco 3x3 (linhas 0..2, cols 0..2)
    s = list(SOLUTION_STR)
    s[1] = s[0]  # mesma box
    assert is_solution_valid("".join(s)) is False
