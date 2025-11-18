import random
import string
import unicodedata


def remover_acentos(txt):
    return ''.join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    )


def gerar_palavras_chave(texto, dificuldade):
    """Extrai palavras para o jogo com base no texto."""
    palavras = [
        p.strip('.,!?()[]:;"\'').lower()
        for p in texto.split()
    ]

    palavras = [p for p in palavras if len(p) > 4]
    palavras = list(set(palavras))

    qtd = {"facil": 5, "medio": 8, "dificil": 10}
    return random.sample(palavras, min(qtd[dificuldade], len(palavras)))


def gerar_grade(palavras, dificuldade="facil"):
    """Gera matriz e INSERE TODAS as palavras corretamente."""

    tamanho_map = {"facil": 12, "medio": 14, "dificil": 16}
    tamanho = tamanho_map.get(dificuldade, 12)

    grid = [['' for _ in range(tamanho)] for _ in range(tamanho)]

    direcoes = [
        (0, 1), (1, 0), (1, 1), (-1, 1)
    ]

    def pode_colocar(palavra, linha, coluna, d_linha, d_coluna):
        for i, letra in enumerate(palavra):
            r = linha + i * d_linha
            c = coluna + i * d_coluna

            if not (0 <= r < tamanho and 0 <= c < tamanho):
                return False

            if grid[r][c] not in ('', letra):
                return False

        return True

    def colocar_palavra(palavra):
        palavra = remover_acentos(palavra).upper()

        for _ in range(200):

            d = random.choice(direcoes)
            linha = random.randint(0, tamanho - 1)
            coluna = random.randint(0, tamanho - 1)

            if pode_colocar(palavra, linha, coluna, *d):
                for i, letra in enumerate(palavra):
                    grid[linha + i * d[0]][coluna + i * d[1]] = letra
                return True

        return False

    # Garante que TODAS entram
    for palavra in palavras:
        if not colocar_palavra(palavra):
            print("⚠ Palavra não coube. Aumentando grade...")
            return gerar_grade(palavras, dificuldade)

    # Completa com letras aleatórias
    letras = string.ascii_uppercase
    for r in range(tamanho):
        for c in range(tamanho):
            if grid[r][c] == '':
                grid[r][c] = random.choice(letras)

    return grid
