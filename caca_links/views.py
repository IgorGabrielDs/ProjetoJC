from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
import unicodedata
import re

from noticias.models import Assunto, Noticia
from .models import CacaPalavra
from .utils import gerar_palavras_chave, gerar_grade, remover_acentos


# =========================================================
# DESTACAR PALAVRAS — versão FINAL (sem bug)
# =========================================================
def destacar_palavras(texto_original, palavras_chave):

    def normalizar(txt):
        return ''.join(
            c for c in unicodedata.normalize('NFD', txt)
            if unicodedata.category(c) != 'Mn'
        ).lower()

    palavras_norm = [normalizar(p) for p in palavras_chave]

    # divide texto mantendo espaços e pontuações separadas
    tokens = re.findall(r'\w+|[^\w\s]|\s+', texto_original, flags=re.UNICODE)

    resultado = []

    for token in tokens:

        if token.isspace():
            resultado.append(token)
            continue

        token_norm = normalizar(token)

        foi_marcado = False

        for palavra, palavra_norm in zip(palavras_chave, palavras_norm):

            if token_norm == palavra_norm:
                resultado.append(
                    f'<span class="highlight-word" data-word="{palavra_norm.upper()}">{token}</span>'
                )
                foi_marcado = True
                break

        if not foi_marcado:
            resultado.append(token)

    return "".join(resultado)


# =========================================================
# ESCOLHER TEMA
# =========================================================
def escolher_tema(request):
    temas = Assunto.objects.all().order_by("nome")
    return render(request, "cacalinks/escolher_tema.html", {"temas": temas})


# =========================================================
# JOGO
# =========================================================
def jogo(request, tema_id):
    tema = get_object_or_404(Assunto, id=tema_id)

    nivel = int(request.GET.get("nivel", 1))
    diff_map = {1: "facil", 2: "medio", 3: "dificil"}
    dificuldade = diff_map[nivel]

    hoje = timezone.now().date()

    caca = (
        CacaPalavra.objects.filter(tema=tema, dificuldade=dificuldade, data=hoje)
        .first()
    )

    if not caca:

        noticia = Noticia.objects.filter(assuntos=tema).order_by("-criado_em").first()

        if not noticia:
            return render(request, "cacalinks/jogo.html", {
                "erro": "Nenhuma notícia disponível.",
                "tema": tema
            })

        palavras = gerar_palavras_chave(noticia.conteudo, dificuldade)
        grade = gerar_grade(palavras, dificuldade)

        caca = CacaPalavra.objects.create(
            tema=tema,
            noticia=noticia,
            dificuldade=dificuldade,
            palavras_chave=palavras,
            grade=grade,
            data=hoje,
        )

    # Destaca corretamente
    texto_destacado = destacar_palavras(
        caca.noticia.conteudo,
        caca.palavras_chave
    )

    return render(request, "cacalinks/jogo.html", {
        "tema": tema,
        "nivel": nivel,
        "caca": caca,
        "texto_da_noticia_formatado": texto_destacado,
    })


# =========================================================
# PRÓXIMO NÍVEL
# =========================================================
def proximo_nivel(request, tema_id, nivel_atual):
    n = nivel_atual + 1
    if n > 3:
        return redirect("caca_links:escolher_tema")
    return redirect(f"/caca-links/jogo/{tema_id}/?nivel={n}")


# =========================================================
# TELA DE CONCLUSÃO
# =========================================================
def nivel_concluido(request, id):
    caca = get_object_or_404(CacaPalavra, id=id)
    return render(request, "cacalinks/nivel_concluido.html", {"caca": caca})
