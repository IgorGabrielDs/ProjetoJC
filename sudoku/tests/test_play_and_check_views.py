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

def test_play_sudoku_when_puzzle_missing_generates_on_demand(client):
    """
    Se o puzzle não existir, a view deve gerar um 'on-demand' e exibir o jogo
    em vez de mostrar erro.
    """
    # Cria usuário e loga
    # Nota: Se 'User' não estiver importado, use get_user_model() ou mantenha como está se já funcionar
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.create_user(username="u_demand", password="123")
    client.force_login(user)

    # Garante URL (pula se não existir reversão)
    url = _url_or_skip("sudoku:play_sudoku", difficulty="easy")
    
    # Executa requisição
    resp = client.get(url)
    
    # Agora esperamos SUCESSO (200), não erro.
    assert resp.status_code == 200
    
    # Verifica se carregou o template do JOGO (sudoku.html), não o de erro
    # A lista de templates pode vir vazia dependendo do setup, então protegemos a checagem
    templates_names = [t.name for t in resp.templates if t.name]
    
    # Se sua view usa 'sudoku/sudoku.html', validamos isso. 
    # Se for outro nome, ajuste aqui, mas geralmente é esse.
    assert any("sudoku.html" in t for t in templates_names), f"Templates usados: {templates_names}"
    
    # Opcional: Verifica se o conteúdo parece ser o jogo (tabuleiro)
    content = resp.content.decode("utf-8").lower()
    # Verifica termos comuns de um tabuleiro de sudoku
    assert "grid" in content or "tabuleiro" in content or "sudoku-board" in content

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
