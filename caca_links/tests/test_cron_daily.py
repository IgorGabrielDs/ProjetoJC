import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db

def test_cron_diario_cria_registros(monkeypatch, assunto, noticia):
    cron = pytest.importorskip("caca_links.cron")
    models = pytest.importorskip("caca_links.models")
    CacaPalavras = models.CacaPalavras

    # fakes
    def fake_top3():
        return {assunto: [noticia, noticia, noticia]}

    def fake_palavras(*args, **kwargs):
        return ["AA", "BB", "CC", "DD", "EE", "FF"]

    def fake_grade(*args, **kwargs):
        return [["A"] * 10 for _ in range(10)]

    # monkeypatch direto no módulo cron
    monkeypatch.setattr(cron, "get_top3_noticias_por_tema", fake_top3)
    monkeypatch.setattr(cron, "gerar_palavras_chave", fake_palavras)
    monkeypatch.setattr(cron, "gerar_grade", fake_grade)

    # act
    cron.gerar_caca_links_diario()

    # assert
    hoje = timezone.now().date()
    qs = CacaPalavras.objects.all()
    assert qs.count() >= 1
    if "data" in {f.name for f in CacaPalavras._meta.get_fields()}:
        assert qs.filter(data=hoje).exists()
