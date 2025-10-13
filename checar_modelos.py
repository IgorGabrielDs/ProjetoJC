# checar_modelos.py

import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (necessário se rodar fora do Django)
load_dotenv()

# Configura a API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Chave da API não encontrada no .env!")
else:
    genai.configure(api_key=api_key)

    print("✅ Modelos disponíveis que suportam 'generateContent':")
    try:
        for m in genai.list_models():
          if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
    except Exception as e:
        print(f"❌ Ocorreu um erro ao listar os modelos: {e}")