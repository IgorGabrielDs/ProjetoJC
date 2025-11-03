import json
import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

User = get_user_model()
pytestmark = pytest.mark.django_db

# Importa modelos e views do seu app
models = pytest.importorskip("sudoku.models", reason="sudoku.models não encontrado")
views = pytest.importorskip("sudoku.views", reason="sudoku.views não encontrado")

SudokuPuzzle = getattr(models, "SudokuPuzzle")
UserSudokuProgress = getattr(models, "UserSudokuProgress")

# Solução válida (mesma usada nos testes puros)
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

def _today():
    # a view usa timezone.localdate()
    return timezone.localdate()

def _make_puzzle(date=None, difficulty="easy", problem_board=None):
    if date is None:
        date = _today()
    if problem_board is None:
        # usa zeros (vazio) para simplificar
        problem_board = "0" * 81
    return SudokuPuzzle.objects.create(
        date=date,
        difficulty=difficulty,
        problem_board=problem_board,
    )

def _url_or_skip(name, **kwargs):
    try:
        return reverse(name, kwargs=kwargs)
    except NoReverseMatch:
        pytest.skip(f"Rota '{name}' não encontrada.")

def test_play_sudoku_redirects_when_progress_not_sufficient(client):
    # usuário e progresso sem completar nada
    user = User.objects.create_user(username="u1", password="x")
    client.force_login(user)

    # cria puzzle de hoje apenas para easy (para evitar erro de "não existe")
    _make_puzzle(date=_today(), difficulty="easy")

    # medium deve redirecionar para easy
    url = _url_or_skip("sudoku:play_sudoku", difficulty="medium")
    resp = client.get(url)
    assert resp.status_code in (301, 302)
    assert "/sudoku/" in resp.url or "play_sudoku" in resp.url

    # hard deve redirecionar para easy (já que nada concluído)
    url = _url_or_skip("sudoku:play_sudoku", difficulty="hard")
    resp = client.get(url)
    assert resp.status_code in (301, 302)

def test_play_sudoku_renders_when_requirements_met(client):
    user = User.objects.create_user(username="u2", password="x")
    client.force_login(user)

    # progresso: easy e medium concluídos
    progress = UserSudokuProgress.objects.create(
        user=user,
        completed_easy=True,
        completed_medium=True,
        completed_hard=False,
    )

    # precisa existir puzzle do dia na dificuldade pedida
    _make_puzzle(date=_today(), difficulty="hard")

    url = _url_or_skip("sudoku:play_sudoku", difficulty="hard")
    resp = client.get(url)
    # deve renderizar a página (200)
    assert resp.status_code == 200
    # garante que contexto inclui "puzzle" e "progress"
    assert "puzzle" in resp.context
    assert "progress" in resp.context

def test_play_sudoku_when_puzzle_missing_shows_error_page(client):
    user = User.objects.create_user(username="u3", password="x")
    client.force_login(user)

    url = _url_or_skip("sudoku:play_sudoku", difficulty="easy")
    resp = client.get(url)
    assert resp.status_code == 200

    content = (resp.content or b"").decode("utf-8", errors="ignore").lower()

    # 1) Verifica se o template de erro foi usado
    used_error_template = False
    if hasattr(resp, "templates") and resp.templates:
        for t in resp.templates:
            # t.name pode ser None em templates herdados
            if getattr(t, "name", "") and "sudoku/sudoku_error.html" in t.name:
                used_error_template = True
                break

    # 2) Verifica se existe a chave 'message' no contexto
    has_message_in_context = False
    if hasattr(resp, "context") and resp.context:
        # resp.context é um ContextList; percorremos os dicts internos
        try:
            for ctx in resp.context:
                if isinstance(ctx, dict) and "message" in ctx:
                    has_message_in_context = True
                    break
        except TypeError:
            # Algumas versões retornam um objeto único
            has_message_in_context = isinstance(resp.context, dict) and "message" in resp.context

    # 3) Verifica o conteúdo da resposta
    has_error_text = ("ainda não foi gerado" in content) or ("sudoku_error" in content)

    assert used_error_template or has_message_in_context or has_error_text, (
        "Esperava template 'sudoku/sudoku_error.html', ou contexto com 'message', "
        "ou conteúdo contendo a mensagem de erro."
    )

def test_check_solution_success_easy_sets_progress_and_next_level(client):
    user = User.objects.create_user(username="u4", password="x")
    client.force_login(user)

    # progresso inicial vazio
    progress = UserSudokuProgress.objects.create(user=user)

    # cria puzzle do dia (easy)
    puzzle = _make_puzzle(date=_today(), difficulty="easy")

    url = _url_or_skip("sudoku:check_solution")
    payload = {
        "puzzle_id": puzzle.id,
        "solution": SOLUTION_STR,
        "elapsed_seconds": 75,
    }
    resp = client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert resp.status_code == 200
    data = json.loads(resp.content.decode("utf-8"))
    assert data.get("success") is True
    assert data.get("next_level") == "medium"

    # re-carrega progresso
    progress.refresh_from_db()
    assert progress.completed_easy is True
    # tempo deve ter sido registrado
    assert progress.easy_completion_time == timedelta(seconds=75)

def test_check_solution_invalid_returns_message(client):
    user = User.objects.create_user(username="u5", password="x")
    client.force_login(user)

    puzzle = _make_puzzle(date=_today(), difficulty="medium")

    url = _url_or_skip("sudoku:check_solution")
    bad_payload = {
        "puzzle_id": puzzle.id,
        "solution": "0" * 81,  # contém zeros -> inválido
    }
    resp = client.post(
        url,
        data=json.dumps(bad_payload),
        content_type="application/json",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert resp.status_code == 200
    data = json.loads(resp.content.decode("utf-8"))
    assert data.get("success") is False
    assert "Solução incorreta" in data.get("message", "")

def test_check_solution_bad_contract_returns_400(client):
    user = User.objects.create_user(username="u6", password="x")
    client.force_login(user)

    url = _url_or_skip("sudoku:check_solution")
    # faltando campos essenciais (puzzle_id ou solution)
    resp = client.post(
        url,
        data=json.dumps({"solution": SOLUTION_STR}),
        content_type="application/json",
    )
    assert resp.status_code == 400
