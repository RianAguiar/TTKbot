from django.urls import path
from . import views


urlpatterns = [
    path("", views.lista_videos, name="lista_videos"),
    path("upload/", views.upload_video, name="upload_video"),
]
