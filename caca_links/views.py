from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from noticias.models import Assunto, Noticia
from .models import CacaPalavras, ProgressoJogador
from .utils import gerar_palavras_chave, gerar_grade, normalizar_palavra, QTD_POR_DIFICULDADE

import re


@login_required
def escolher_tema(request):
    temas = Assunto.objects.filter(id__in=[1,2,3,4,5,6,7,8])

    imgmap = {
        'Blog do Torcedor': 'esportes',
        'Brasil': 'politica',
        'Cultura': 'entretenimento',
        'Economia': 'economia',
        'Internacional': 'internacional',
        'Política': 'politica',
        'Receita da Boa': 'gastronomia',
        'Social1': 'social1',
    }

    for t in temas:
        t.imgfile = imgmap.get(t.nome, "default")

    return render(request, "caca_links/escolher_tema.html", {"temas": temas})






@login_required
def jogar_caca_palavras(request, tema_id):
    tema = get_object_or_404(Assunto, id=tema_id)
    hoje = timezone.now().date()

    progresso, _ = ProgressoJogador.objects.get_or_create(
        usuario=request.user,
        tema=tema
    )

    dificuldade = ["facil", "medio", "dificil"][progresso.nivel_atual - 1]

    noticia = Noticia.objects.filter(assuntos=tema, criado_em__date=hoje).first()
    if not noticia:
        noticia = Noticia.objects.filter(assuntos=tema).order_by("-criado_em").first()

    if not noticia:
        messages.error(request, "Nenhuma notícia disponível para este tema.")
        return redirect("caca_links:escolher_tema")

    caca, created = CacaPalavras.objects.get_or_create(
        tema=tema,
        dificuldade=dificuldade,
        data=hoje,
        defaults={
            "noticia": noticia,
            "palavras_chave": gerar_palavras_chave(noticia.conteudo, dificuldade),
        },
    )

    qtd = QTD_POR_DIFICULDADE[dificuldade]
    palavras = list(caca.palavras_chave)

    conteudo_norm = normalizar_palavra(noticia.conteudo)
    palavras = [p for p in palavras if p in conteudo_norm]

    if len(palavras) > qtd:
        palavras = palavras[:qtd]

    if len(palavras) < qtd:
        novas = gerar_palavras_chave(noticia.conteudo, dificuldade)
        for p in novas:
            if p not in palavras:
                palavras.append(p)
            if len(palavras) == qtd:
                break

    if palavras != caca.palavras_chave:
        caca.palavras_chave = palavras
        caca.grade = gerar_grade(palavras, dificuldade)
        caca.save()

    if not caca.grade:
        caca.grade = gerar_grade(caca.palavras_chave, dificuldade)
        caca.save()

    texto = re.sub(r'<a[^>]*>|</a>', '', noticia.conteudo)
    tokens = re.findall(r"[A-Za-zÀ-ÿ]+|[^A-Za-zÀ-ÿ]+", texto)
    texto_destacado = ""

    for tk in tokens:
        if tk.strip():
            normal = normalizar_palavra(tk)
            if normal in caca.palavras_chave:
                tk = f'<span class="highlight-word" data-word="{normal}">{tk}</span>'
        texto_destacado += tk

    return render(request, "caca_links/jogo.html", {
        "tema": tema,
        "nivel": progresso.nivel_atual,
        "caca": caca,
        "texto_da_noticia_formatado": texto_destacado,
    })


@login_required
def concluir_nivel(request, tema_id):
    tema = get_object_or_404(Assunto, id=tema_id)

    progresso, _ = ProgressoJogador.objects.get_or_create(
        usuario=request.user,
        tema=tema,
        defaults={"nivel_atual": 1, "concluido": False},
    )

    if progresso.nivel_atual < 3:
        progresso.nivel_atual += 1
    else:
        progresso.concluido = True

    progresso.save()

    return redirect("caca_links:escolher_tema")
