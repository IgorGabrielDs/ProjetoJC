from django.urls import path
from . import views

# Define o namespace usado em redirects e reverses
app_name = "caca_links"

urlpatterns = [
    # Página inicial do jogo (escolha de tema)
    path(
        "",
        views.escolher_tema,
        name="escolher_tema",
    ),

    # Tela principal do jogo de caça-palavras
    path(
        "jogar/<int:tema_id>/",
        views.jogar_caca_palavras,
        name="jogar",
    ),

    # Conclusão de nível (avança ou finaliza o jogo)
    path(
        "concluir/<int:tema_id>/",
        views.concluir_nivel,
        name="concluir_nivel",
    ),
]
