import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_views_requerem_login(client):
    for name, args, method in [
        ("caca_links:escolher_tema", [], "get"),
        ("caca_links:jogar", [1], "get"),
        ("caca_links:concluir_nivel", [1], "post"),
    ]:
        url = reverse(name, args=args)
        resp = getattr(client, method)(url)
        assert resp.status_code in (302, 301)
        assert "login" in resp.headers.get("Location", "")
