import openai
import random
import string
from django.conf import settings

def gerar_palavras_chave(conteudo, dificuldade):
    qtd = 6

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user",
                 "content": f"liste {qtd} palavras importantes (substantivos ou nomes próprios) desse texto jornalístico, separadas por vírgulas: {conteudo}"},
            ],
            max_tokens=150,
            temperature=0.7
        )

        texto = response.choices[0].message.content

        if texto:
            palavras = [p.strip().upper() for p in texto.split(",") if p.strip()]
            return palavras[:qtd]
        else:
            return []

    except Exception:
        return conteudo.split()[:qtd]

def gerar_grade(palavras, dificuldade, tamanho=15):
    palavras = palavras[:6]
    matriz = [["" for _ in range(tamanho)] for _ in range(tamanho)]

    if dificuldade == "facil":
        direcoes = [(0, 1), (1, 0)]
    elif dificuldade == "medio":
        direcoes = [(0, 1), (1, 0), (1, 1)]
    elif dificuldade == "dificil":
        direcoes = [(0, 1), (1, 0), (1, 1), (0, -1), (-1, 0), (-1, -1)]

    def pode_colocar(palavra, x, y, dx, dy):
        for i, letra in enumerate(palavra):
            nx, ny = x + i * dx, y + i * dy
            if not (0 <= nx < tamanho and 0 <= ny < tamanho):
                return False
            if matriz[nx][ny] not in ("", letra):
                return False
        return True

    def coloca_palavra(palavra):
        for _ in range(200):
            dx, dy = random.choice(direcoes)
            x = random.randint(0, tamanho - 1)
            y = random.randint(0, tamanho - 1)
            if pode_colocar(palavra, x, y, dx, dy):
                for i, letra in enumerate(palavra):
                    nx, ny = x + i * dx, y + i * dy
                    matriz[nx][ny] = letra
                return True
        return False

    for palavra in palavras:
        coloca_palavra(palavra.upper())

    letras = string.ascii_uppercase
    for i in range(tamanho):
        for j in range(tamanho):
            if matriz[i][j] == "":
                matriz[i][j] = random.choice(letras)

    return matriz