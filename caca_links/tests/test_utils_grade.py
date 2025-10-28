import pytest
import inspect
import random

pytestmark = pytest.mark.django_db


def test_gerar_grade_formato_basico():
    mod = pytest.importorskip("caca_links.utils")
    assert hasattr(mod, "gerar_grade")

    fn = mod.gerar_grade
    sig = inspect.signature(fn)
    params = sig.parameters

    random.seed(123)
    palavras = ["RECIFE", "JC", "BRASIL", "ECONOMIA", "CULTURA", "POLITICA"]

    # Chamada tolerante: se aceitar 'dificuldade', passamos "facil".
    # Caso contrário, tentamos sem e, se ainda assim der erro, caímos no fallback com kwargs.
    if "dificuldade" in params:
        grade = fn(palavras, "facil")
    else:
        try:
            grade = fn(palavras)
        except TypeError:
            # Último fallback: pode haver assinatura com kwargs ou args variáveis
            try:
                grade = fn(palavras, dificuldade="facil")
            except TypeError:
                grade = fn(palavras)

    assert isinstance(grade, list)
    n = len(grade)
    assert n >= 8  # grade mínima razoável
    assert all(isinstance(l, list) and len(l) == n for l in grade)
    assert all(isinstance(c, str) and len(c) == 1 for row in grade for c in row)
