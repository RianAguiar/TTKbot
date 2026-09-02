import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Video

logger = logging.getLogger(__name__)

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"
TIKTOK_CHUNK_SIZE = 10_000_000

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


def _tiktok_headers():
    return {
        "Authorization": f"Bearer {settings.TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def orquestrar_publicacao_task(video_id):
    video = Video.objects.get(pk=video_id)
    if video.postar_tiktok:
        publicar_video_tiktok_task.delay(video_id)
    if video.postar_instagram:
        publicar_video_instagram_task.delay(video_id)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def publicar_video_tiktok_task(self, video_id):
    video = Video.objects.get(pk=video_id)
    video.tiktok_status = "enviando"
    video.save(update_fields=["tiktok_status"])

    try:
        with video.arquivo.open("rb") as f:
            video_bytes = f.read()

        video_size = len(video_bytes)
        total_chunk_count = max(1, -(-video_size // TIKTOK_CHUNK_SIZE))
        chunk_size = video_size if total_chunk_count == 1 else TIKTOK_CHUNK_SIZE

        init_payload = {
            "post_info": {
                "title": video.titulo,
                "description": video.descricao or "",
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
            headers=_tiktok_headers(),
            json=init_payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        publish_id = data["publish_id"]
        upload_url = data["upload_url"]

        video.tiktok_publish_id = publish_id
        video.save(update_fields=["tiktok_publish_id"])

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

        verificar_status_tiktok_task.apply_async(args=[video.id], countdown=10)

    except Exception as exc:
        logger.exception("Falha ao publicar vídeo %s no TikTok", video_id)
        video.tiktok_status = "erro"
        video.tiktok_erro = str(exc)
        video.save(update_fields=["tiktok_status", "tiktok_erro"])
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=10)
def verificar_status_tiktok_task(self, video_id):
    video = Video.objects.get(pk=video_id)

    if not video.tiktok_publish_id:
        return

    resp = requests.post(
        f"{TIKTOK_API_BASE}/post/publish/status/fetch/",
        headers=_tiktok_headers(),
        json={"publish_id": video.tiktok_publish_id},
        timeout=30,
    )
    resp.raise_for_status()
    status = resp.json()["data"]["status"]

    if status == "PUBLISH_COMPLETE":
        video.tiktok_status = "publicado"
        video.tiktok_publicado_em = timezone.now()
        video.save(update_fields=["tiktok_status", "tiktok_publicado_em"])

    elif status == "FAILED":
        video.tiktok_status = "erro"
        video.tiktok_erro = resp.json()["data"].get("fail_reason", "Falha desconhecida")
        video.save(update_fields=["tiktok_status", "tiktok_erro"])

    else:
        atraso = min(300, 10 * (2 ** self.request.retries))
        raise self.retry(countdown=atraso)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def publicar_video_instagram_task(self, video_id):
    video = Video.objects.get(pk=video_id)
    video.instagram_status = "enviando"
    video.save(update_fields=["instagram_status"])

    try:
        video_url = f"{settings.SITE_DOMAIN}{video.arquivo.url}"

        resp = requests.post(
            f"{GRAPH_API_BASE}/{settings.INSTAGRAM_ACCOUNT_ID}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": f"{video.titulo}\n\n{video.descricao}".strip(),
                "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=30,
        )
        resp.raise_for_status()
        container_id = resp.json()["id"]

        video.instagram_container_id = container_id
        video.save(update_fields=["instagram_container_id"])

        verificar_status_instagram_task.apply_async(args=[video.id], countdown=15)

    except Exception as exc:
        logger.exception("Falha ao publicar vídeo %s no Instagram", video_id)
        video.instagram_status = "erro"
        video.instagram_erro = str(exc)
        video.save(update_fields=["instagram_status", "instagram_erro"])
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=15)
def verificar_status_instagram_task(self, video_id):
    video = Video.objects.get(pk=video_id)

    if not video.instagram_container_id:
        return

    resp = requests.get(
        f"{GRAPH_API_BASE}/{video.instagram_container_id}",
        params={
            "fields": "status_code,status",
            "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    status_code = data.get("status_code")

    if status_code == "FINISHED":
        publish_resp = requests.post(
            f"{GRAPH_API_BASE}/{settings.INSTAGRAM_ACCOUNT_ID}/media_publish",
            data={
                "creation_id": video.instagram_container_id,
                "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=30,
        )
        publish_resp.raise_for_status()

        video.instagram_status = "publicado"
        video.instagram_publicado_em = timezone.now()
        video.save(update_fields=["instagram_status", "instagram_publicado_em"])

    elif status_code == "ERROR":
        video.instagram_status = "erro"
        video.instagram_erro = data.get("status", "Falha desconhecida")
        video.save(update_fields=["instagram_status", "instagram_erro"])

    else:
        atraso = min(300, 15 * (2 ** self.request.retries))
        raise self.retry(countdown=atraso)