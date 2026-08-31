from django.shortcuts import render, redirect
from .models import Video
from .forms import VideoForm


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
            form.save()
            return redirect("lista_videos")

    else:
        form = VideoForm()

    return render(
        request,
        "videos/upload.html",
        {"form": form},
    )
