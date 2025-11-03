from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from noticias.models import Assunto
from .models import CacaPalavras, ProgressoJogador

@login_required
def escolher_tema(request):
    temas = Assunto.objects.filter(slug__in=[
        "politica", "blog-do-torcedor", "social1", "cultura", "receita-da-boa", "brasil", "economia", "internacional"
    ])
    progresso = ProgressoJogador.objects.filter(usuario=request.user)
    return render(request, "cacalinks/escolher_tema.html", {"temas": temas, "progresso": progresso})

@login_required
def jogar_caca_palavras(request, tema_id):
    tema = get_object_or_404(Assunto, id=tema_id)
    hoje = timezone.now().date()

    progresso, _ = ProgressoJogador.objects.get_or_create(usuario=request.user, tema=tema)
    if progresso.concluido:
        messages.info(request, f"Você já completou o Caça Links de {tema.nome}!")
        return redirect("cacalinks:escolher_tema")

    dificuldade = ["facil", "medio", "dificil"][progresso.nivel_atual - 1]
    caca = get_object_or_404(CacaPalavras, tema=tema, dificuldade=dificuldade, data=hoje)

    return render(request, "cacalinks/jogo.html", {
        "tema": tema,
        "nivel": progresso.nivel_atual,
        "caca": caca,
        "palavras": caca.palavras_chave,
    })

@login_required
def concluir_nivel(request, tema_id):
    tema = get_object_or_404(Assunto, id=tema_id)
    progresso = get_object_or_404(ProgressoJogador, usuario=request.user, tema=tema)

    dificuldade = ["facil", "medio", "dificil"][progresso.nivel_atual - 1]
    caca = get_object_or_404(CacaPalavras, tema=tema, dificuldade=dificuldade, data=timezone.now().date())

    if caca.noticia:
        link = reverse('noticias:detalhe_noticia', args=[caca.noticia.pk])
        if link not in progresso.links_conquistados:
            progresso.links_conquistados.append(link)

    if progresso.nivel_atual < 3:
        progresso.nivel_atual += 1
    else:
        progresso.concluido = True
    progresso.save()

    messages.success(request, "Nível concluído com sucesso!")
    return redirect("cacalinks:jogar", tema.pk)
