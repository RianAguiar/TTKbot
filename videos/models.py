from django.db import models


class Video(models.Model):
    STATUS_CHOICES = [
        ("PENDENTE", "Pendente"),
        ("PROCESSANDO", "Processando"),
        ("PUBLICADO", "Publicado"),
        ("ERRO", "Erro"),
    ]

    arquivo = models.FileField(upload_to="videos/")
    legenda = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDENTE",
    )

    premium = models.BooleanField(default=False)

    agendado_para = models.DateTimeField(
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    erro = models.TextField(blank=True)

    def __str__(self):
        return self.arquivo.name
