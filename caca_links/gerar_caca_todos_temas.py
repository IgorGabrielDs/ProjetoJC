from django.utils import timezone
from noticias.models import Assunto, Noticia
from caca_links.models import CacaPalavra
from caca_links.utils import gerar_palavras_chave, gerar_grade


def gerar_caca_por_tema(tema):
    """Gera caça-palavras para as notícias mais recentes de um tema."""
    noticias = Noticia.objects.filter(assuntos=tema).order_by('-criado_em')[:3]

    if not noticias.exists():
        print(f"⚠️ Nenhuma notícia encontrada para o tema '{tema.nome}'.")
        return

    for noticia in noticias:
        palavras = gerar_palavras_chave(noticia.conteudo, "facil")
        grade = gerar_grade(palavras)

        caca, criado = CacaPalavra.objects.get_or_create(
            tema=tema,
            noticia=noticia,
            defaults={
                "dificuldade": "facil",
                "palavras_chave": palavras,
                "grade": grade,
                "data": timezone.now().date(),
            },
        )

        if criado:
            print(f"✅ Caça-palavra criado para: {tema.nome} - {noticia.titulo}")
        else:
            print(f"ℹ️ Já existe caça-palavra para: {tema.nome} - {noticia.titulo}")


def run():
    temas = Assunto.objects.all()
    if not temas.exists():
        print("❌ Nenhum tema encontrado!")
        return

    for tema in temas:
        print(f"\n📰 Gerando caça-palavras para o tema: {tema.nome}")
        gerar_caca_por_tema(tema)


if __name__ == "__main__":
    run()
