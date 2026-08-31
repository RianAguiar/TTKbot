from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Video
from .forms import VideoForm
from .tasks import publicar_video_task


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

            if agendado_para and agendado_para > timezone.now():
                video.status = "agendado"
                video.save()
                # Celery só dispara a task na hora marcada (eta)
                publicar_video_task.apply_async(args=[video.id], eta=agendado_para)
            else:
                video.status = "rascunho"
                video.save()
                # dispara imediatamente, assim que a request terminar
                publicar_video_task.delay(video.id)

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