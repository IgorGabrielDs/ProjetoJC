import openai
import random
import string
import re
from django.conf import settings
import unicodedata # Importe o unicodedata

# 1. FUNÇÃO ADICIONAL PARA REMOVER ACENTOS E NORMALIZAR
def normalizar_palavra(palavra):
    # Remove acentos (ex: "INCRÍVEL" -> "INCRIVEL")
    nfkd_form = unicodedata.normalize('NFKD', palavra)
    sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Remove tudo que não for letra A-Z
    limpa = re.sub(r'[^A-Z]', '', sem_acento.upper())
    return limpa

def gerar_palavras_chave(conteudo, dificuldade):
    qtd = 6

    try:
        # Tenta usar a OpenAI (como antes)
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
        palavras_brutas = [p.strip() for p in texto.split(",") if p.strip()]

    except Exception:
        # --- NOVO FALLBACK (MUITO MELHOR) ---
        # 1. Limpa o texto de pontuação e o coloca em maiúsculo
        conteudo_limpo = re.sub(r'[^\w\s]', '', conteudo).upper()
        # 2. Encontra todas as palavras únicas com 5 ou mais letras (agora com suporte a unicode)
        palavras_brutas = list(set(re.findall(r'\b\w{5,}\b', conteudo_limpo, flags=re.UNICODE)))
        random.shuffle(palavras_brutas)

    # 2. NORMALIZA TODAS AS PALAVRAS (DA OPENAI OU DO FALLBACK)
    palavras_normalizadas = [normalizar_palavra(p) for p in palavras_brutas]
    # Retorna apenas as 'qtd' primeiras que não estão vazias
    palavras_finais = [p for p in palavras_normalizadas if p][:qtd]
    
    return palavras_finais

# 3. GERAR GRADE (sem alteração, pois já usa .upper())
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
        if not palavra: continue 
        coloca_palavra(palavra.upper()) # .upper() aqui é seguro pois as palavras já estão normalizadas (A-Z)

    letras = string.ascii_uppercase
    for i in range(tamanho):
        for j in range(tamanho):
            if matriz[i][j] == "":
                matriz[i][j] = random.choice(letras)

    return matriz