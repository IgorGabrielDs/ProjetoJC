# JornalDoCommercio/settings_dev.py
# Uso: DJANGO_SETTINGS_MODULE=JornalDoCommercio.settings_dev

from .settings import *  # herda tudo do seu settings "principal" (produção/base)

# -----------------------
# Modo Desenvolvimento
# -----------------------
DEBUG = True

# Hosts comuns em dev
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    # Se você também usa o App Service para testes, mantenha:
    "jornaldocommercio.azurewebsites.net",
]

# -----------------------
# Banco de Dados (SQLite)
# -----------------------
# Ignora qualquer configuração Postgres do settings base sem alterar o .env.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -----------------------
# E-mails em Dev
# -----------------------
# Não depende de SMTP: imprime no console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Remeta de desenvolvimento (se não vier do .env)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@jc.local")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# -----------------------
# Arquivos Estáticos
# -----------------------
# Mantém sua estrutura atual. WhiteNoise pode ficar; funciona bem em dev também.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "noticias" / "static"]

# Se o middleware do WhiteNoise estiver ativo no settings base, isto mantém o comportamento.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -----------------------
# Segurança / CSRF (Dev)
# -----------------------
# Em dev, garanta que localhost/127.0.0.1 estejam permitidos
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://*.azurewebsites.net",  # mantém se você testar lá também
]

# -----------------------
# APScheduler em Dev
# -----------------------
# Se você **não** quiser rodar migrações automáticas do django_apscheduler em dev:
# APSCHEDULER_RUN_MIGRATIONS = False
# (Se deixar True, também funciona; depende do seu fluxo.)

# -----------------------
# Qualquer ajuste opcional de logging
# -----------------------
# LOGGING = { ... }  # se quiser silenciar logs em dev, adicione aqui.
