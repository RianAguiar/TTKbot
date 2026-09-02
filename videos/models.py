from django.db import models


class Video(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("agendado", "Agendado"),
        ("enviando", "Enviando"),
        ("publicado", "Publicado"),
        ("erro", "Erro ao publicar"),
    ]

    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    arquivo = models.FileField(upload_to="videos/%Y/%m/")
    criado_em = models.DateTimeField(auto_now_add=True)

    agendado_para = models.DateTimeField(null=True, blank=True)

    postar_tiktok = models.BooleanField(default=True)
    postar_instagram = models.BooleanField(default=False)

    tiktok_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    tiktok_publish_id = models.CharField(max_length=255, blank=True)
    tiktok_publicado_em = models.DateTimeField(null=True, blank=True)
    tiktok_erro = models.TextField(blank=True)

    instagram_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    instagram_container_id = models.CharField(max_length=255, blank=True)
    instagram_publicado_em = models.DateTimeField(null=True, blank=True)
    instagram_erro = models.TextField(blank=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo