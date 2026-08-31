import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Video

logger = logging.getLogger(__name__)

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"
CHUNK_SIZE = 10_000_000  # 10 MB, conforme recomendado na doc da TikTok


def _headers():
    return {
        "Authorization": f"Bearer {settings.TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def publicar_video_task(self, video_id):
    """
    Inicia a publicação de um vídeo no TikTok (Content Posting API - Direct Post).
    Disparada imediatamente (.delay()) ou agendada (.apply_async(eta=...)).
    """
    video = Video.objects.get(pk=video_id)
    video.status = "enviando"
    video.save(update_fields=["status"])

    try:
        with video.arquivo.open("rb") as f:
            video_bytes = f.read()

        video_size = len(video_bytes)
        total_chunk_count = max(1, -(-video_size // CHUNK_SIZE))  # ceil division
        chunk_size = video_size if total_chunk_count == 1 else CHUNK_SIZE

        # 1. Inicializar o post
        init_payload = {
            "post_info": {
                "title": video.titulo,
                "description": video.descricao or "",
                # Enquanto o app não passar pela auditoria da TikTok,
                # só é permitido publicar como SELF_ONLY (privado).
                "privacy_level": getattr(settings, "TIKTOK_PRIVACY_LEVEL", "SELF_ONLY"),
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count,
            },
        }

        resp = requests.post(
            f"{TIKTOK_API_BASE}/post/publish/video/init/",
            headers=_headers(),
            json=init_payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        publish_id = data["publish_id"]
        upload_url = data["upload_url"]

        video.tiktok_publish_id = publish_id
        video.save(update_fields=["tiktok_publish_id"])

        # 2. Enviar o(s) chunk(s) do vídeo
        for i in range(total_chunk_count):
            start = i * chunk_size
            end = min(start + chunk_size, video_size) - 1
            chunk_data = video_bytes[start : end + 1]

            put_resp = requests.put(
                upload_url,
                data=chunk_data,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{video_size}",
                    "Content-Type": "video/mp4",
                },
                timeout=60,
            )
            put_resp.raise_for_status()

        # 3. Agendar a primeira checagem de status (processamento é assíncrono)
        verificar_status_publicacao.apply_async(args=[video.id], countdown=10)

    except Exception as exc:
        logger.exception("Falha ao publicar vídeo %s no TikTok", video_id)
        video.status = "erro"
        video.erro_publicacao = str(exc)
        video.save(update_fields=["status", "erro_publicacao"])
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=10)
def verificar_status_publicacao(self, video_id):
    """
    Faz polling no endpoint de status até a publicação terminar (ou falhar).
    Usa backoff crescente para não estourar o rate limit (6 req/min por token).
    """
    video = Video.objects.get(pk=video_id)

    if not video.tiktok_publish_id:
        return

    resp = requests.post(
        f"{TIKTOK_API_BASE}/post/publish/status/fetch/",
        headers=_headers(),
        json={"publish_id": video.tiktok_publish_id},
        timeout=30,
    )
    resp.raise_for_status()
    status = resp.json()["data"]["status"]

    if status == "PUBLISH_COMPLETE":
        video.status = "publicado"
        video.publicado_em = timezone.now()
        video.save(update_fields=["status", "publicado_em"])

    elif status == "FAILED":
        video.status = "erro"
        video.erro_publicacao = resp.json()["data"].get("fail_reason", "Falha desconhecida")
        video.save(update_fields=["status", "erro_publicacao"])

    else:
        # ainda processando: tenta de novo com backoff exponencial (máx. ~5 min)
        atraso = min(300, 10 * (2 ** self.request.retries))
        raise self.retry(countdown=atraso)