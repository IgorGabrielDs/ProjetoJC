from django.contrib import admin
# Importamos os modelos
from .models import (
    Noticia, 
    Voto, 
    Assunto, 
    Perfil, 
    Salvo, 
    Enquete, 
    OpcaoEnquete, 
    VotoEnquete,
    Video
)

# 1. Inline das OPÇÕES (Essencial: permite adicionar respostas na tela da Enquete)
class OpcaoEnqueteInline(admin.TabularInline): 
    model = OpcaoEnquete
    extra = 2  # Mostra 2 linhas vazias por padrão
    verbose_name_plural = "Opções da Enquete"


# 2. Admin da ENQUETE (Fluxo Principal)
@admin.register(Enquete)
class EnqueteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'get_noticia_titulo')
    search_fields = ('titulo', 'noticia__titulo')
    
    # É aqui que a mágica acontece: Opções dentro da Enquete
    inlines = [OpcaoEnqueteInline]

    # Helper para mostrar o título da notícia na listagem de forma segura
    @admin.display(description='Notícia Vinculada')
    def get_noticia_titulo(self, obj):
        return obj.noticia.titulo if obj.noticia else "-"


# 3. Admin da NOTÍCIA
@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "criado_em", "tem_enquete")
    search_fields = ("titulo", "conteudo")
    ordering = ("-criado_em",)
    
    # REMOVI o 'inlines = [EnqueteInline]' propositalmente.
    # Motivo: Criar enquete por aqui gerava enquetes sem opções de resposta.
    # Agora o usuário deve ir em "Enquetes > Adicionar" para fazer do jeito certo.

    @admin.display(boolean=True, description="Tem Enquete?")
    def tem_enquete(self, obj):
        # Verifica se existe uma enquete vinculada (reverso do OneToOne)
        return hasattr(obj, 'enquete')


# 4. Admin de VÍDEO (Sua configuração estava ótima, mantive igual)
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tem_link', 'tem_arquivo', 'ativo', 'criado_em')
    search_fields = ('titulo', 'descricao')
    list_filter = ('ativo', 'criado_em')
    ordering = ('-criado_em',)
    list_editable = ('ativo',) 

    @admin.display(boolean=True, description="Link")
    def tem_link(self, obj):
        return bool(obj.link)

    @admin.display(boolean=True, description="Arquivo")
    def tem_arquivo(self, obj):
        return bool(obj.arquivo)


# 5. Outros Registros
@admin.register(Assunto)
class AssuntoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(VotoEnquete)
class VotoEnqueteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'enquete', 'opcao_selecionada', 'criado_em')
    list_filter = ('enquete',)
    search_fields = ('usuario__username', 'enquete__titulo', 'enquete__noticia__titulo')


admin.site.register(Voto)
admin.site.register(Salvo)
admin.site.register(Perfil)