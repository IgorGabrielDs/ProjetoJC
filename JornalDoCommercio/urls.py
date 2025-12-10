from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Login e Logout
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

    # Apps
    path("", include(("noticias.urls", "noticias"), namespace="noticias")),
    path("caca-links/", include(("caca_links.urls", "caca_links"), namespace="caca_links")),
    path("sudoku/", include(("sudoku.urls", "sudoku"), namespace="sudoku")),

    # Password Reset
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html"
        ),
        name="password_reset",
    ),
]

# ✔ APENAS static — porque Whitenoise cuida do resto.
# ❗ NÃO ADICIONAR MEDIA AQUI QUANDO USANDO AZURE BLOB.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
