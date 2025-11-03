# sudoku/tests/test_urls_start.py
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_start_requires_login(client):
    url = reverse("sudoku:sudoku_start")
    resp = client.get(url)
    # login_required deve redirecionar
    assert resp.status_code in (301, 302)
    assert "login" in resp.url.lower()


def test_start_logged_in_renders(client):
    user = User.objects.create_user(username="sudoku_user", password="x")
    client.force_login(user)

    # Como a rota injeta difficulty='easy', a view tentará abrir o puzzle do dia.
    # Se você não tiver o puzzle criado, a view renderiza a página de erro personalizada (200).
    url = reverse("sudoku:sudoku_start")
    resp = client.get(url)
    assert resp.status_code == 200
