from django.urls import path
from . import views, views_auth

app_name = "noticias"

urlpatterns = [
    path("", views.index, name="index"),
    
    # --- CORREÇÃO AQUI ---
    # O nome foi alterado de "noticia_detalhe" para "detalhe_noticia"
    path("noticia/<int:pk>/", views.noticia_detalhe, name="detalhe_noticia"),
    
    path("noticia/<int:pk>/votar/", views.votar, name="votar"),
    path("noticia/<int:pk>/toggle-salvo/", views.toggle_salvo, name="toggle_salvo"),
    path("minhas-salvas/", views.minhas_salvas, name="minhas_salvas"),
    path("signup/", views.signup, name="signup"),
    path("noticia/<int:pk>/resumir/", views.resumir_noticia, name="resumir_noticia"),
    path("accounts/password/reset/", views_auth.request_reset_code, name="password_reset"),
    path("accounts/password/code/",  views_auth.verify_reset_code,    name="password_reset_code"),
    path("accounts/password/new/",   views_auth.set_new_password,     name="password_reset_new"),
]