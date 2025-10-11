from django.utils import timezone
from noticias.utils import get_top3_noticias_por_tema
from .models import CacaPalavras
from .utils import gerar_palavras_chave, gerar_grade

def gerar_caca_links_diario():
    hoje = timezone.now().date()
    dificuldades = ["facil", "medio", "dificil"]

    top3_por_tema = get_top3_noticias_por_tema()

    for tema, noticias in top3_por_tema.items():
        for i, noticia in enumerate(noticias[:3]):
            dificuldade = dificuldades[i]
            palavras = gerar_palavras_chave(noticia.conteudo, dificuldade)
            grade = gerar_grade(palavras, dificuldade)

            CacaPalavras.objects.update_or_create(
                tema=tema,
                dificuldade=dificuldade,
                data=hoje,
                defaults={
                    "noticia": noticia,
                    "palavras_chave": palavras,
                    "grade": grade,
                },
            )

        print(f"[OK] {tema.nome}: caça-palavras gerados.")
