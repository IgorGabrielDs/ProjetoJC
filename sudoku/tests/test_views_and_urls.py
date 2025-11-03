import json
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

pytestmark = pytest.mark.django_db
User = get_user_model()

# Rotas reais do seu projeto
INDEX_CANDIDATES = [
    "sudoku:sudoku_start",  # raiz do app -> play_sudoku com difficulty='easy'
]
VALIDATE_CANDIDATES = [
    "sudoku:check_solution",  # seu endpoint real (POST JSON com puzzle_id + solution)
]

# Solução canônica 9x9 "achatada" (81 dígitos) — válida para nosso payload
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


def _first_existing_url(candidates):
    for name in candidates:
        try:
            return reverse(name), name
        except NoReverseMatch:
            continue
    return None, None


def test_index_route_if_exists(client):
    url, name = _first_existing_url(INDEX_CANDIDATES)
    if not url:
        pytest.skip("Nenhuma rota de INDEX padrão encontrada no app sudoku.")
    resp = client.get(url)
    # Como a view é protegida por login, aceitamos 200 OU redirecionamento para login
    assert resp.status_code in (200, 301, 302), f"{name} deve responder 200 ou redirecionar ao login"
    if resp.status_code in (301, 302):
        assert "login" in (resp.url or "").lower()


def test_validate_route_matches_project_contract(client):
    """
    Adaptação para o contrato REAL do seu projeto:
    - POST em sudoku:check_solution
    - JSON: { puzzle_id, solution, (opcional) elapsed_seconds }
    - Retorno: JSON com { success: bool, next_level?: str, message?: str }
    """
    url, name = _first_existing_url(VALIDATE_CANDIDATES)
    if not url:
        pytest.skip("Nenhuma rota de VALIDAR encontrada.")

    # Cria usuário + login (endpoint é protegido)
    user = User.objects.create_user(username="sudoku_tester", password="x")
    client.force_login(user)

    # Importa modelos
    models = pytest.importorskip("sudoku.models", reason="sudoku.models não encontrado")
    SudokuPuzzle = getattr(models, "SudokuPuzzle")
    UserSudokuProgress = getattr(models, "UserSudokuProgress")

    # Garante que o progresso exista (sua view usa .get, não .get_or_create)
    UserSudokuProgress.objects.create(user=user)

    today = timezone.localdate()
    puzzle = SudokuPuzzle.objects.create(
        date=today,
        difficulty="easy",
        problem_board="0" * 81,
    )

    payload = {
        "puzzle_id": puzzle.id,
        "solution": SOLUTION_STR,
        "elapsed_seconds": 42,
    }

    resp = client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert resp.status_code == 200, f"{name} deve responder 200 com payload válido"
    data = json.loads(resp.content.decode("utf-8"))
    assert "success" in data
