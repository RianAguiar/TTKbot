from django.urls import path
from . import views
 
urlpatterns = [
    path("", views.lista_videos, name="lista_videos"),
    path("enviar/", views.upload_video, name="upload_video"),
    path("video/<int:pk>/", views.detalhe_video, name="detalhe_video"),
]
 
