import pytest

pytestmark = pytest.mark.django_db

def test_progresso_unico_por_usuario_e_tema(user, assunto):
    from caca_links.models import ProgressoJogador
    ProgressoJogador.objects.create(usuario=user, tema=assunto)
    with pytest.raises(Exception):
        ProgressoJogador.objects.create(usuario=user, tema=assunto)
