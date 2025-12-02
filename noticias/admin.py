from django.contrib import admin
# 1. Importamos TODOS os modelos (incluindo o novo Video)
from .models import (
    Noticia, 
    Voto, 
    Assunto, 
    Perfil, 
    Salvo, 
    Enquete, 
    OpcaoEnquete, 
    VotoEnquete,
    Video  # <--- Adicionado aqui
)


# 2. O seu EnqueteInline original (para a Notícia)
class EnqueteInline(admin.StackedInline): 
    model = Enquete
    extra = 0 
    can_delete = True 
    fk_name = 'noticia' 
    verbose_name_plural = "Enquete (opcional)"
    fields = ('titulo',)


# 3. O Inline para as OPÇÕES (que vai dentro da página da Enquete separada)
class OpcaoEnqueteInline(admin.TabularInline): 
    model = OpcaoEnquete
    extra = 2 
    verbose_name_plural = "Opções da Enquete"


# 4. O seu NoticiaAdmin original
@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "criado_em")
    search_fields = ("titulo", "conteudo")
    ordering = ("-criado_em",)
    
    # Mantendo sua configuração original
    inlines = [EnqueteInline]


# 5. O Admin para ENQUETE original
@admin.register(Enquete)
class EnqueteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'noticia')
    search_fields = ('titulo', 'noticia__titulo')
    
    # Aqui você edita as opções da enquete
    inlines = [OpcaoEnqueteInline]


# 6. (NOVO) Configuração para o modelo VÍDEO
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tem_link', 'tem_arquivo', 'ativo', 'criado_em')
    search_fields = ('titulo', 'descricao')
    list_filter = ('ativo', 'criado_em')
    ordering = ('-criado_em',)
    list_editable = ('ativo',) 

    # Helpers visuais para saber se tem link ou arquivo
    @admin.display(boolean=True, description="Link")
    def tem_link(self, obj):
        return bool(obj.link)

    @admin.display(boolean=True, description="Arquivo")
    def tem_arquivo(self, obj):
        return bool(obj.arquivo)


# 7. Outros registros originais
@admin.register(Assunto)
class AssuntoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(VotoEnquete)
class VotoEnqueteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'enquete', 'opcao_selecionada', 'criado_em')
    list_filter = ('enquete',)
    search_fields = ('usuario__username', 'enquete__titulo')

admin.site.register(Voto)
admin.site.register(Salvo)
admin.site.register(Perfil)