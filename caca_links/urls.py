from django.urls import path
from . import views

app_name = "caca_links"

urlpatterns = [
    path("", views.escolher_tema, name="escolher_tema"),
    path("jogo/<int:tema_id>/", views.jogo, name="jogar"),
    path("nivel-concluido/<int:id>/", views.nivel_concluido, name="nivel_concluido"),
]
