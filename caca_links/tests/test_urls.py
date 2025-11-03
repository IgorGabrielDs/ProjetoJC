import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db

def test_nome_das_rotas_existe():
    # Se o path raiz do app for outro, o assert do reverse ainda garante que os names existem.
    assert reverse("caca_links:escolher_tema")
    assert resolve(reverse("caca_links:escolher_tema")).url_name == "escolher_tema"

    # Rotas parametrizadas
    assert resolve(reverse("caca_links:jogar", args=[1])).url_name == "jogar"
    assert resolve(reverse("caca_links:concluir_nivel", args=[1])).url_name == "concluir_nivel"
