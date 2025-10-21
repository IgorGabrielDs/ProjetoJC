from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # 🔐 Login e Logout sem prefixo /accounts/
    path("login/",
         auth_views.LoginView.as_view(template_name="registration/login.html"),
         name="login"),
    path("logout/",
         auth_views.LogoutView.as_view(template_name="registration/logged_out.html"),
         name="logout"),
    # 🔧 Fluxo completo de redefinição de senha
    path("password_reset/",
         auth_views.PasswordResetView.as_view(
             template_name="registration/password_reset_form.html"
         ),
         name="password_reset"),
    path("password_reset/done/",
         auth_views.PasswordResetDoneView.as_view(
             template_name="registration/password_reset_done.html"
         ),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(
             template_name="registration/password_reset_confirm.html"
         ),
         name="password_reset_confirm"),
    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(
             template_name="registration/password_reset_complete.html"
         ),
         name="password_reset_complete"),
    path("", include(("noticias.urls", "noticias"), namespace="noticias")),
    path("caca-links/", include(("caca_links.urls", "caca_links"), namespace="caca_links")),
    path('sudoku/', include(('sudoku.urls', 'sudoku'), namespace='sudoku')),
]
