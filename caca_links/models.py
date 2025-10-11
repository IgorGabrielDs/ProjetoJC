from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from noticias.models import Noticia, Assunto

class CacaPalavras(models.Model):
    DIFICULDADES = [
        ("facil", "Fácil"),
        ("medio", "Médio"),
        ("dificil", "Difícil"),
    ]

    tema = models.ForeignKey(Assunto, on_delete=models.CASCADE)
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE)
    dificuldade = models.CharField(max_length=10, choices=DIFICULDADES)
    palavras_chave = models.JSONField(default=list)
    grade = models.JSONField(default=list, blank=True)
    data = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ("tema", "dificuldade", "data")

    def __str__(self):
        return f"{self.tema.nome} - {self.dificuldade} ({self.data})"


class ProgressoJogador(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tema = models.ForeignKey(Assunto, on_delete=models.CASCADE)
    nivel_atual = models.PositiveSmallIntegerField(default=1)
    concluido = models.BooleanField(default=False)
    links_conquistados = models.JSONField(default=list)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("usuario", "tema")

    def __str__(self):
        return f"{self.usuario.username} - {self.tema.nome} (Nível {self.nivel_atual})"
