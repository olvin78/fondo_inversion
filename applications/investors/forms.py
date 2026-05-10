from django import forms
from .models import Communication

class CommunicationForm(forms.ModelForm):
    class Meta:
        model = Communication
        fields = ["subject", "category", "message", "attachment"]
        widgets = {
            "subject": forms.TextInput(attrs={
                "class": "hud-input",
                "placeholder": "Asunto del comunicado..."
            }),
            "category": forms.Select(attrs={
                "class": "hud-select"
            }),
            "message": forms.Textarea(attrs={
                "class": "hud-textarea",
                "rows": 6,
                "placeholder": "Cuerpo del comunicado formal..."
            }),
            "attachment": forms.FileInput(attrs={
                "class": "form-control bg-transparent border-white border-opacity-10 text-white p-3 rounded-4",
            }),
        }
