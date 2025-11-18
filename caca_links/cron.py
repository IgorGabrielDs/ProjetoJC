import random
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events
from noticias.models import Noticia, Assunto
from .models import CacaPalavra
from .utils import gerar_palavras_chave, gerar_grade


# =======================================================
# 🔁 GERADOR DIÁRIO DE CAÇA-PALAVRAS
# =======================================================

def gerar_caca_links_diario():
    """Gera ou atualiza um caça-palavras diário para cada tema ativo."""
    hoje = timezone.now().date()
    total_criados = 0

    print("🔁 Gerando caça-palavras do dia:", hoje)

    for tema in Assunto.objects.all():
        noticia = Noticia.objects.filter(assuntos=tema).order_by("-criado_em").first()
        if not noticia:
            print(f"⚠️ Nenhuma notícia encontrada para o tema: {tema.nome}")
            continue

        for dificuldade in ["facil", "medio", "dificil"]:
            palavras = gerar_palavras_chave(noticia.conteudo, dificuldade)
            if not palavras:
                print(f"⚠️ Nenhuma palavra válida para o tema: {tema.nome} ({dificuldade})")
                continue

            grade = gerar_grade(palavras, dificuldade)

            # Apaga caça-palavras antigos do mesmo dia, tema e dificuldade
            CacaPalavra.objects.filter(
                tema=tema,
                dificuldade=dificuldade,
                data=hoje
            ).delete()

            # Cria o novo caça-palavras
            CacaPalavra.objects.create(
                tema=tema,
                noticia=noticia,
                dificuldade=dificuldade,
                palavras_chave=palavras,
                grade=grade,
                data=hoje,
            )

            total_criados += 1

    print("✅ Caça-palavras gerados com sucesso!")
    print(f"🆕 Criados: {total_criados}")
    print("🎯 Cron Caça Links executado com sucesso!")


# =======================================================
# 🕒 AGENDADOR AUTOMÁTICO
# =======================================================

def iniciar_cron_caca_links():
    """Inicia o agendador automático diário do Caça Links."""
    scheduler = BackgroundScheduler(timezone="America/Recife")

    # executa 1x por dia à meia-noite
    scheduler.add_job(
        gerar_caca_links_diario,
        trigger="cron",
        hour=0,
        minute=1,
        id="cron_caca_links_diario",
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()
    print("✅ Job diário do Caça Links agendado para 00:01 (horário de Brasília).")
    print("🕒 Scheduler do Caça Links iniciado com sucesso.")
