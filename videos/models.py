from django.db import models


class Video(models.Model):
    STATUS_CHOICES = [
        ("rascunho", "Rascunho"),
        ("agendado", "Agendado"),
        ("enviando", "Enviando para o TikTok"),
        ("publicado", "Publicado"),
        ("erro", "Erro ao publicar"),
    ]

    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    arquivo = models.FileField(upload_to="videos/%Y/%m/")
    criado_em = models.DateTimeField(auto_now_add=True)

    # --- Campos novos para publicação no TikTok ---
    agendado_para = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora em que o vídeo deve ser publicado no TikTok. Deixe em branco para publicar imediatamente.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="rascunho")
    tiktok_publish_id = models.CharField(max_length=255, blank=True)
    publicado_em = models.DateTimeField(null=True, blank=True)
    erro_publicacao = models.TextField(blank=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo