from django.contrib import admin
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

# --- 1. CONFIGURAÇÃO DAS OPÇÕES (RESPOSTAS) ---
class OpcaoEnqueteInline(admin.TabularInline): 
    """
    Permite adicionar opções (Sim, Não, etc.) diretamente
    na tela de criação da Enquete.
    """
    model = OpcaoEnquete
    extra = 2  # Já exibe 2 campos em branco para facilitar
    verbose_name_plural = "Opções da Enquete"


# --- 2. ADMIN DA ENQUETE (ONDE VOCÊ CRIA A PERGUNTA) ---
@admin.register(Enquete)
class EnqueteAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'get_noticia_titulo')
    search_fields = ('titulo', 'noticia__titulo')
    
    # CRUCIAL: Adiciona o formulário de opções dentro da enquete
    inlines = [OpcaoEnqueteInline]

    # Helper para mostrar o título da notícia sem dar erro se estiver vazia
    @admin.display(description='Notícia Vinculada')
    def get_noticia_titulo(self, obj):
        if obj.noticia:
            return obj.noticia.titulo
        return "-"


# --- 3. ADMIN DA NOTÍCIA (SEM ENQUETE INLINE) ---
@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "criado_em", "tem_enquete")
    search_fields = ("titulo", "conteudo")
    ordering = ("-criado_em",)
    
    # IMPORTANTE: Não colocamos 'inlines = [EnqueteInline]' aqui.
    # Isso evita o erro de "Inline dentro de Inline" e o erro 500.

    @admin.display(boolean=True, description="Tem Enquete?")
    def tem_enquete(self, obj):
        # Verifica se a notícia já tem uma enquete associada
        return hasattr(obj, 'enquete')


# --- 4. ADMIN DE VÍDEO ---
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tem_link', 'tem_arquivo', 'ativo', 'criado_em')
    search_fields = ('titulo', 'descricao')
    list_filter = ('ativo', 'criado_em')
    ordering = ('-criado_em',)
    list_editable = ('ativo',) 

    @admin.display(boolean=True, description="Link Externo")
    def tem_link(self, obj):
        return bool(obj.link)

    @admin.display(boolean=True, description="Arquivo Local")
    def tem_arquivo(self, obj):
        return bool(obj.arquivo)


# --- 5. ADMIN DE ASSUNTO (TAXONOMIA) ---
@admin.register(Assunto)
class AssuntoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}


# --- 6. ADMIN DE VOTOS DA ENQUETE (LOGS) ---
@admin.register(VotoEnquete)
class VotoEnqueteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'enquete', 'opcao_selecionada', 'criado_em')
    list_filter = ('enquete',)
    search_fields = ('usuario__username', 'enquete__titulo')


# --- 7. REGISTROS SIMPLES ---
admin.site.register(Voto)
admin.site.register(Salvo)
admin.site.register(Perfil)
# admin.site.register(OpcaoEnquete) -> Não registrar separadamente, pois já está no Inline da Enquete