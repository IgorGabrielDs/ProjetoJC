import random
import string
import re
import unicodedata
from django.conf import settings


# -------------------------------------------------------
# NORMALIZAÇÃO
# -------------------------------------------------------
def normalizar_palavra(palavra):
    if not palavra:
        return ""

    nfkd = unicodedata.normalize('NFKD', palavra)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    apenas_letras = re.sub(r"[^A-Z]", "", sem_acento.upper())

    return apenas_letras.strip()


# -------------------------------------------------------
# QUANTIDADE POR DIFICULDADE
# -------------------------------------------------------
QTD_POR_DIFICULDADE = {
    "facil": 4,
    "medio": 6,
    "dificil": 8,
}


# -------------------------------------------------------
# GERAR PALAVRAS — APENAS AS QUE EXISTEM NO TEXTO
# -------------------------------------------------------
def gerar_palavras_chave(conteudo, dificuldade):

    qtd = QTD_POR_DIFICULDADE.get(dificuldade, 6)
    palavras_brutas = []

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-flash-latest")

        prompt = f"""
        Extraia exatamente {qtd} palavras importantes do texto abaixo.
        Regras:
        - apenas substantivos ou termos relevantes
        - sem frases longas
        - responda APENAS com as palavras separadas por vírgulas

        <texto>
        {conteudo}
        </texto>
        """

        resposta = model.generate_content(prompt)
        texto = (getattr(resposta, "text", "") or "").strip()
        palavras_brutas = [p.strip() for p in texto.split(",") if p.strip()]

    except Exception:
        nfkd = unicodedata.normalize("NFKD", conteudo)
        sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
        conteudo_limpo = re.sub(r"[^A-Za-z\s]", " ", sem_acento)
        conteudo_limpo = conteudo_limpo.upper()

        palavras_brutas = list(set(re.findall(r"\b[A-Z]{5,}\b", conteudo_limpo)))
        random.shuffle(palavras_brutas)

    # -----------------------------------------
    # NOVO: FILTRAR SOMENTE AS PALAVRAS QUE EXISTEM NO TEXTO
    # -----------------------------------------
    conteudo_norm = normalizar_palavra(conteudo)
    palavras_validas = []

    for p in palavras_brutas:
        n = normalizar_palavra(p)
        if n and n in conteudo_norm:
            palavras_validas.append(n)

    # -----------------------------------------
    # Se o Gemini errou e vieram poucas, completa com palavras do próprio texto
    # -----------------------------------------
    if len(palavras_validas) < qtd:
        todas_palavras = re.findall(r"\b[\wÀ-ÿ]{4,}\b", conteudo)
        todas_norm = [normalizar_palavra(w) for w in todas_palavras]
        todas_norm = [w for w in todas_norm if len(w) >= 4]

        random.shuffle(todas_norm)

        for w in todas_norm:
            if w not in palavras_validas:
                palavras_validas.append(w)
            if len(palavras_validas) >= qtd:
                break

    # Garante exatamente a quantidade
    palavras_finais = palavras_validas[:qtd]

    return palavras_finais


# -------------------------------------------------------
# GERAR GRADE — GARANTE TODAS AS PALAVRAS
# -------------------------------------------------------
def gerar_grade(palavras, dificuldade, tamanho=15):

    palavras = [p.upper() for p in palavras if p]

    if dificuldade == "facil":
        direcoes = [(0, 1), (1, 0)]
    elif dificuldade == "medio":
        direcoes = [(0, 1), (1, 0), (1, 1)]
    else:
        direcoes = [
            (0, 1), (1, 0), (1, 1),
            (0, -1), (-1, 0), (-1, -1)
        ]

    for _ in range(60):
        matriz = [["" for _ in range(tamanho)] for _ in range(tamanho)]
        sucesso = True

        for palavra in palavras:
            colocado = False

            for _ in range(400):
                dx, dy = random.choice(direcoes)
                x = random.randint(0, tamanho - 1)
                y = random.randint(0, tamanho - 1)

                valido = True
                for i, letra in enumerate(palavra):
                    nx, ny = x + dx * i, y + dy * i
                    if not (0 <= nx < tamanho and 0 <= ny < tamanho):
                        valido = False
                        break
                    if matriz[nx][ny] not in ("", letra):
                        valido = False
                        break

                if valido:
                    for i, letra in enumerate(palavra):
                        nx, ny = x + dx * i, y + dy * i
                        matriz[nx][ny] = letra
                    colocado = True
                    break

            if not colocado:
                sucesso = False
                break

        if sucesso:
            break

    letras = string.ascii_uppercase
    for i in range(tamanho):
        for j in range(tamanho):
            if matriz[i][j] == "":
                matriz[i][j] = random.choice(letras)

    return matriz
