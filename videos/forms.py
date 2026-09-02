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
        fields = ["titulo", "descricao", "arquivo", "postar_tiktok", "postar_instagram", "agendado_para"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "arquivo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "postar_tiktok": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "postar_instagram": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "postar_tiktok": "Publicar no TikTok",
            "postar_instagram": "Publicar no Instagram",
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("postar_tiktok") and not cleaned_data.get("postar_instagram"):
            raise forms.ValidationError("Selecione ao menos uma rede social para publicar.")
        return cleaned_data