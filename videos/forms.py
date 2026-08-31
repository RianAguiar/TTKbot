from django import forms
from .models import Video


class VideoForm(forms.ModelForm):
    agendado_para = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        label="Agendar publicação para",
        help_text="Deixe em branco para publicar assim que o upload terminar.",
    )

    class Meta:
        model = Video
        fields = ["titulo", "descricao", "arquivo", "agendado_para"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "arquivo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }