from django.db import models
from django.utils import timezone
from noticias.models import Noticia, Assunto


class CacaPalavra(models.Model):
    DIFICULDADE_CHOICES = [
        ("facil", "Fácil"),
        ("medio", "Médio"),
        ("dificil", "Difícil"),
    ]

    tema = models.ForeignKey(
        Assunto,
        on_delete=models.CASCADE,
        related_name="cacas",
        verbose_name="Tema",
    )

    noticia = models.ForeignKey(
        Noticia,
        on_delete=models.CASCADE,
        related_name="cacas_palavras",
        verbose_name="Notícia",
    )

    dificuldade = models.CharField(
        max_length=10,
        choices=DIFICULDADE_CHOICES,
        default="facil",
        verbose_name="Dificuldade",
    )

    palavras_chave = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Palavras-chave",
    )

    grade = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Grade do caça-palavras",
    )

    data = models.DateField(
        default=timezone.now,
        verbose_name="Data de geração",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tema.nome} - {self.noticia.titulo} ({self.dificuldade})"

    class Meta:
        verbose_name = "Caça-palavra"
        verbose_name_plural = "Caça-palavras"
        ordering = ["-data", "tema", "dificuldade"]
