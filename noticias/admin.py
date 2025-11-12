from django.contrib import admin
from .models import Noticia, Voto, Assunto, Enquete


class EnqueteInline(admin.StackedInline):  # usa StackedInline p/ mostrar campos em blocos verticais
    model = Enquete
    extra = 0  # não cria formulários extras vazios
    can_delete = True  # permite excluir a enquete
    fk_name = 'noticia'  # campo de relação
    verbose_name_plural = "Enquete (opcional)"


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "criado_em")
    search_fields = ("titulo", "conteudo")
    ordering = ("-criado_em",)
    fields = ("titulo", "conteudo", "imagem", "legenda", "criado_em", "assuntos")
    readonly_fields = ("criado_em",)

    # 👉 Adiciona o formulário da enquete dentro da notícia
    inlines = [EnqueteInline]


@admin.register(Assunto)
class AssuntoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}
