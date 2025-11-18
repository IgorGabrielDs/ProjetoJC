from django.contrib import admin
# 1. Importamos TODOS os modelos novos
from .models import (
    Noticia, 
    Voto, 
    Assunto, 
    Perfil, 
    Salvo, 
    Enquete, 
    OpcaoEnquete, 
    VotoEnquete
)


# 2. O seu EnqueteInline (para a Notícia) - PERFEITO
class EnqueteInline(admin.StackedInline): # usa StackedInline p/ mostrar campos em blocos verticais
    model = Enquete
    extra = 0 # não cria formulários extras vazios
    can_delete = True # permite excluir a enquete
    fk_name = 'noticia' # campo de relação
    verbose_name_plural = "Enquete (opcional)"
    
    # Adicionamos 'fields' para garantir que só o título apareça aqui
    fields = ('titulo',)


# 3. (NOVO) Um Inline para as OPÇÕES (que vai dentro da Enquete)
class OpcaoEnqueteInline(admin.TabularInline): # Tabular é mais compacto para opções
    model = OpcaoEnquete
    extra = 2 # Começa com 2 campos para opções (ex: 'Sim' e 'Não')
    verbose_name_plural = "Opções da Enquete"


# 4. O seu NoticiaAdmin (com o EnqueteInline) - PERFEITO
@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "criado_em")
    search_fields = ("titulo", "conteudo")
    ordering = ("-criado_em",)
    
    # Nota: Removi 'fields' e 'readonly_fields' para usar a configuração padrão
    # ou você pode mantê-los se preferir, mas 'criado_em' precisa estar
    # em readonly_fields se estiver em 'fields'.
    
    # fields = ("titulo", "conteudo", "imagem", "legenda", "criado_em", "assuntos")
    # readonly_fields = ("criado_em",)

    # 👉 Adiciona o formulário da enquete dentro da notícia
    inlines = [EnqueteInline]


# 5. (NOVO) Um Admin para o modelo ENQUETE
@admin.register(Enquete)
class EnqueteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'noticia')
    search_fields = ('titulo', 'noticia__titulo')
    
    # 👉 Aqui está a mágica:
    # Adicionamos o inline das OPÇÕES dentro do admin da ENQUETE
    inlines = [OpcaoEnqueteInline]


# 6. O seu AssuntoAdmin - PERFEITO
@admin.register(Assunto)
class AssuntoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}


# 7. (NOVO) Registramos os outros modelos para que apareçam no admin
# (Especialmente VotoEnquete, para você ver os votos)
@admin.register(VotoEnquete)
class VotoEnqueteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'enquete', 'opcao_selecionada', 'criado_em')
    list_filter = ('enquete',)
    search_fields = ('usuario__username', 'enquete__titulo')

admin.site.register(Voto)
admin.site.register(Salvo)
admin.site.register(Perfil)