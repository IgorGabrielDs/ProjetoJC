import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "JornalDoCommercio.settings")
django.setup()

from django.conf import settings
from django.core.files.storage import default_storage

print("BACKEND em settings:", settings.STORAGES.get("default", {}).get("BACKEND"))
print("Classe efetiva:", default_storage.__class__)

path = default_storage.save("teste_backend.txt", open("manage.py", "rb"))
print("Salvo em:", path)
print("URL:", default_storage.url(path))