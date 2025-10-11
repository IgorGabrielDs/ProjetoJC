from django.db.models import Sum, F
from django.utils import timezone
from .models import Noticia, Assunto

def get_top3_noticias_por_tema():
    """
    Retorna as 3 notícias mais relevantes de cada tema (Assunto),
    com base em um score que prioriza visualizações.
    Fórmula do Score: (Soma dos Votos) + (Visualizações * 0.01)
    """
    principais_por_assunto = {}
    hoje = timezone.now().date()
    
    assuntos = Assunto.objects.filter(slug__in=[
        "politica", "blog-do-torcedor", "social1", "cultura", "receita-da-boa", "brasil", "economia", "internacional"
    ])

    for assunto in assuntos:
        top_noticias_qs = (
            Noticia.objects.filter(assuntos=assunto, criado_em__date=hoje)
            .annotate(
                score_calculado=Sum('votos__valor', default=0) + (F('visualizacoes') * 0.01)
            )
            .order_by("-score_calculado", "-criado_em")[:3]
        )
        
        if top_noticias_qs.count() < 3:
            faltam = 3 - top_noticias_qs.count()
            ids_existentes = list(top_noticias_qs.values_list("id", flat=True))
            
            antigas = (
                Noticia.objects.filter(assuntos=assunto)
                .exclude(id__in=ids_existentes)
                .annotate(
                    score_calculado=Sum('votos__valor', default=0) + (F('visualizacoes') * 0.01)
                )
                .order_by("-score_calculado", "-criado_em")[:faltam]
            )
            lista_final = list(top_noticias_qs) + list(antigas)
            principais_por_assunto[assunto] = lista_final
        else:
             principais_por_assunto[assunto] = list(top_noticias_qs)

    return principais_por_assunto