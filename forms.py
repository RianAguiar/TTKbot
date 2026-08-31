from django import forms
from .models import Video


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = [
            "arquivo",
            "legenda",
            "premium",
            "agendado_para",
        ]
