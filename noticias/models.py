from django.db import models
from django.conf import settings
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver


# --- PERFIL E USUÁRIO ---

class Perfil(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    data_nascimento = models.DateField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de {self.user}"


# --- TAXONOMIA (ASSUNTOS) ---

class Assunto(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# --- CONTEÚDO PRINCIPAL (NOTÍCIA) ---

class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    resumo = models.TextField(blank=True, null=True)

    # timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # mídia
    imagem = models.ImageField(upload_to="noticias/", null=True, blank=True)
    legenda = models.CharField(max_length=255, null=True, blank=True)
    credito_imagem = models.CharField(max_length=255, blank=True, default="")

    # autoria
    autor = models.CharField(max_length=120, blank=True, default="JC")

    # taxonomia
    assuntos = models.ManyToManyField(Assunto, related_name="noticias", blank=True)

    # métricas/engajamento
    visualizacoes = models.PositiveIntegerField(default=0)

    # salvos (through)
    salvos = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Salvo",
        related_name="noticias_salvas",
        blank=True,
    )

    def get_absolute_url(self):
        return reverse("noticias:noticia_detalhe", args=[self.pk])

    @property
    def votos(self):
        # Referencia o Voto de upvote/downvote da notícia
        return Voto.objects.filter(noticia=self)

    def is_salva_por(self, user):
        if not user.is_authenticated:
            return False
        return self.salvos.filter(pk=user.pk).exists()

    def salvos_count(self):
        return self.salvos.count()

    def score(self):
        return sum(v.valor for v in self.votos.all())

    def upvotes(self):
        return self.votos.filter(valor=1).count()

    def downvotes(self):
        return self.votos.filter(valor=-1).count()

    def __str__(self):
        return self.titulo


# --- NOVO MODELO: VÍDEO (INDEPENDENTE) ---

class Video(models.Model):
    titulo = models.CharField("Título do Vídeo", max_length=200)
    descricao = models.TextField("Descrição", blank=True, null=True)

    # IMPORTANTE: campo de capa para o carrossel
    imagem = models.ImageField(
        "Capa do Vídeo",
        upload_to="videos/capas/",
        blank=True,
        null=True,
    )

    # Opção para Link Externo (YouTube/Vimeo)
    link = models.URLField("Link do YouTube/Vimeo", blank=True, null=True)

    # Opção para Upload de Arquivo
    arquivo = models.FileField(
        "Arquivo de Vídeo",
        upload_to="videos/",
        blank=True,
        null=True,
    )

    # Se você tiver um model de "Assunto" ou "Categoria", pode adicionar aqui:
    # assuntos = models.ManyToManyField(Assunto, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Vídeo"
        verbose_name_plural = "Vídeos"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("noticias:detalhe_video", args=[self.pk])


# --- SISTEMA DE ENQUETES ---

class Enquete(models.Model):
    noticia = models.OneToOneField(
        Noticia,
        on_delete=models.CASCADE,
        related_name="enquete",
        blank=True,
        null=True,
    )
    # O 'titulo' agora é a PERGUNTA da enquete
    titulo = models.CharField(
        "Pergunta da enquete",
        max_length=200,
        blank=True,
        null=True,
    )

    # As opções (opcao_a / opcao_b) foram movidas para o modelo OpcaoEnquete

    def __str__(self):
        return self.titulo or f"Enquete da notícia: {self.noticia.titulo}"

    def ja_votou(self, user):
        """Verifica se um usuário específico já votou nesta enquete."""
        if not user.is_authenticated:
            return False
        return VotoEnquete.objects.filter(enquete=self, usuario=user).exists()


class OpcaoEnquete(models.Model):
    """Uma opção de escolha para uma enquete."""

    enquete = models.ForeignKey(
        Enquete,
        on_delete=models.CASCADE,
        related_name="opcoes",
    )
    texto = models.CharField("Texto da opção", max_length=100)

    def __str__(self):
        return f"{self.enquete.titulo} -> {self.texto}"

    @property
    def total_votos(self):
        """Calcula o total de votos para esta opção."""
        # Contamos quantos VotoEnquete estão ligados a esta OpcaoEnquete
        return self.votoenquete_set.count()


class VotoEnquete(models.Model):
    """Registra o voto de um usuário em uma enquete/opção."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="votos_enquete",
    )
    enquete = models.ForeignKey(
        Enquete,
        on_delete=models.CASCADE,
        related_name="votos_registrados",
    )
    opcao_selecionada = models.ForeignKey(
        OpcaoEnquete,
        on_delete=models.CASCADE,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Garante que um usuário só pode votar UMA VEZ por enquete
            models.UniqueConstraint(
                fields=["usuario", "enquete"],
                name="unique_user_poll_vote",
            )
        ]

    def __str__(self):
        return f"{self.usuario.username} votou em '{self.opcao_selecionada.texto}'"


# --- INTERAÇÕES (SCORE E SALVOS) ---

class Voto(models.Model):
    """Este é o Voto de UPVOTE/DOWNVOTE da Notícia (Score)."""

    noticia = models.ForeignKey(
        Noticia,
        on_delete=models.CASCADE,
        related_name="votos",
    )
    # Usamos AUTH_USER_MODEL para ficar consistente com o projeto
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    # -1 para downvote, 1 para upvote
    valor = models.IntegerField()

    criado_em = models.DateTimeField(auto_now_add=True)
    # Corrigindo um erro de digitação de antes: auto_now=True
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["noticia", "usuario"],
                name="unique_user_vote_per_news",
            )
        ]

    def __str__(self):
        return f"{self.usuario} -> {self.valor} em {self.noticia}"


class Salvo(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    noticia = models.ForeignKey(
        Noticia,
        on_delete=models.CASCADE,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "noticia")

    def __str__(self):
        return f"{self.usuario} salvou {self.noticia}"


# --- SIGNALS ---

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_perfil_ao_criar_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(user=instance)
