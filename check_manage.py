# check_models.py - VERSÃO CORRIGIDA PARA O PYLANCE

# Importações específicas para satisfazer o Pylance
from google.generativeai.client import configure
from google.generativeai.models import list_models
from google.api_core import exceptions

# COLOQUE SUA CHAVE REAL AQUI
YOUR_API_KEY = "AIzaSyCOu_OYT9PmXAT-p9GBxUGWvOgjWXSrnpY" 

try:
    # A função configure() é chamada diretamente
    configure(api_key=YOUR_API_KEY)

    print("--- VERIFICAÇÃO DE MODELOS GEMINI ---")
    print("Modelos disponíveis que suportam 'generateContent':\n")
    
    count = 0
    # A função list_models() é chamada diretamente
    for model in list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            count += 1
    
    if count == 0:
        print("\n❌ Nenhum modelo compatível foi encontrado para esta chave de API.")
    else:
        print(f"\n✨ Total de {count} modelos encontrados. Sua chave e a biblioteca parecem estar funcionando corretamente!")

except exceptions.PermissionDenied:
    print(f"\n❌ ERRO DE PERMISSÃO: Sua chave de API foi recusada. Verifique se ela é válida.")
except Exception as e:
    print(f"\n❌ Ocorreu um erro inesperado: {e}")