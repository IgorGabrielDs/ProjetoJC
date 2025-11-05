from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from noticias.models import Assunto, Noticia
from .models import CacaPalavras, ProgressoJogador

import re 
from .utils import gerar_palavras_chave, gerar_grade, normalizar_palavra # Importa a função de normalizar


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

    try:
        caca = CacaPalavras.objects.get(tema=tema, dificuldade=dificuldade, data=hoje)
    except CacaPalavras.DoesNotExist:
        
        noticia = Noticia.objects.filter(assuntos=tema, criado_em__date=hoje).order_by('-criado_em').first()
        
        if not noticia:
            noticia = Noticia.objects.filter(assuntos=tema).order_by('-criado_em').first()

        if not noticia:
            messages.error(request, f"Ainda não há notícias para o tema {tema.nome}. Tente mais tarde.")
            return redirect("cacalinks:escolher_tema")
        
        palavras = gerar_palavras_chave(noticia.conteudo, dificuldade)
        grade = gerar_grade(palavras, dificuldade)
        
        caca = CacaPalavras.objects.create(
            tema=tema,
            noticia=noticia,
            dificuldade=dificuldade,
            palavras_chave=palavras,
            grade=grade,
            data=hoje
        )

    # --- Lógica de Formatação de Texto ---
    texto_formatado = caca.noticia.conteudo
    palavras_no_texto = set(re.findall(r'\b\w+\b', texto_formatado, flags=re.UNICODE))

    for palavra_chave in caca.palavras_chave:
        if not palavra_chave: continue 

        for palavra_original in palavras_no_texto:
            if normalizar_palavra(palavra_original) == palavra_chave:
                texto_formatado = re.sub(
                    f'(\\b{re.escape(palavra_original)}\\b)', 
                    rf'<span class="highlight-word" data-word="{palavra_chave}">\1</span>', 
                    texto_formatado
                )
    # --- Fim da Formatação ---

    return render(request, "cacalinks/jogo.html", {
        "tema": tema,
        "nivel": progresso.nivel_atual,
        "caca": caca,
        "texto_da_noticia_formatado": texto_formatado,
    })

@login_required
def concluir_nivel(request, tema_id):
    tema = get_object_or_404(Assunto, id=tema_id)
    progresso = get_object_or_404(ProgressoJogador, usuario=request.user, tema=tema)

    dificuldade = ["facil", "medio", "dificil"][progresso.nivel_atual - 1]
    
    caca = CacaPalavras.objects.filter(tema=tema, dificuldade=dificuldade).order_by('-data').first()

    if not caca:
        messages.error(request, "Erro ao encontrar o jogo. Tente novamente.")
        return redirect("cacalinks:escolher_tema")

    # --- 1. LÓGICA DE SALVAMENTO (COMO ANTES) ---
    link_da_noticia = None
    if caca.noticia:
        # Confirme que seu app 'noticias' tem uma URL com name='detalhe_noticia'
        link_da_noticia = reverse('noticias:detalhe_noticia', args=[caca.noticia.pk])
        
        if link_da_noticia not in progresso.links_conquistados:
            progresso.links_conquistados.append(link_da_noticia)

    nivel_anterior = progresso.nivel_atual
    if progresso.nivel_atual < 3:
        progresso.nivel_atual += 1
    else:
        progresso.concluido = True
    progresso.save()
    
    # --- 2. MUDANÇA NO REDIRECIONAMENTO ---
    # Se o link da notícia foi encontrado, redireciona para ele.
    if link_da_noticia:
        if progresso.concluido:
             messages.success(request, f"Parabéns! Você completou o tema '{tema.nome}' e desbloqueou a notícia final!")
        else:
             messages.success(request, f"Nível {nivel_anterior} concluído! Você desbloqueou esta notícia.")
        
        # Leva o usuário direto para a notícia que ele desbloqueou
        return redirect(link_da_noticia)
    
    # (Fallback) Se, por algum motivo, não houver notícia, 
    # ele apenas redireciona para a tela de escolha.
    messages.info(request, "Progresso salvo! Escolha o próximo tema.")
    return redirect("cacalinks:escolher_tema")