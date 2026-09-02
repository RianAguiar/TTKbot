from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Video
from .forms import VideoForm
from .tasks import (
    publicar_video_tiktok_task,
    publicar_video_instagram_task,
)


def lista_videos(request):
    videos = Video.objects.order_by("-criado_em")

    return render(
        request,
        "videos/lista.html",
        {"videos": videos},
    )


def upload_video(request):
    if request.method == "POST":
        form = VideoForm(request.POST, request.FILES)

        if form.is_valid():
            video = form.save(commit=False)
            agendado_para = form.cleaned_data.get("agendado_para")
            video.save()

            agendado = agendado_para and agendado_para > timezone.now()

            if video.postar_tiktok:
                if agendado:
                    video.tiktok_status = "agendado"
                    publicar_video_tiktok_task.apply_async(args=[video.id], eta=agendado_para)
                else:
                    publicar_video_tiktok_task.delay(video.id)

            if video.postar_instagram:
                if agendado:
                    video.instagram_status = "agendado"
                    publicar_video_instagram_task.apply_async(args=[video.id], eta=agendado_para)
                else:
                    publicar_video_instagram_task.delay(video.id)

            video.save()

            return redirect("lista_videos")

    else:
        form = VideoForm()

    return render(
        request,
        "videos/upload.html",
        {"form": form},
    )


def detalhe_video(request, pk):
    video = get_object_or_404(Video, pk=pk)

    return render(
        request,
        "videos/detalhe.html",
        {"video": video},
    )