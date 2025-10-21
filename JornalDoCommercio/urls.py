from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from noticias import views_auth as reset_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # 🔐 Login e Logout sem prefixo /accounts/ (mantidos como você já tinha)
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="registration/logged_out.html"),
        name="logout",
    ),

    # 🔧 Fluxo customizado de redefinição de senha com OTP (6 dígitos)
    # 1) Enviar código por e-mail
    path("password_reset/", reset_views.request_reset_code, name="password_reset"),
    # 2) Verificar código
    path("password_reset/code/", reset_views.verify_reset_code, name="password_reset_code"),
    # 3) Definir nova senha
    path("password_reset/new/", reset_views.set_new_password, name="password_reset_new"),

    # 🔗 Rotas dos apps
    path("", include(("noticias.urls", "noticias"), namespace="noticias")),
    path("caca-links/", include(("caca_links.urls", "caca_links"), namespace="caca_links")),
    path("sudoku/", include(("sudoku.urls", "sudoku"), namespace="sudoku")),
]

# 👇 ESSENCIAL em dev para servir /media/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
