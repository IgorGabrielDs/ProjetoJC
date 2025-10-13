from django.urls import path
from . import views

app_name = "caca_links"

urlpatterns = [
    path("", views.escolher_tema, name="escolher_tema"),
    path("jogar/<int:tema_id>/", views.jogar_caca_palavras, name="jogar"),
    path("concluir/<int:tema_id>/", views.concluir_nivel, name="concluir_nivel"),
]
