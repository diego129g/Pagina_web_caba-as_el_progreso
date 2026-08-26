from django import forms
from .models import Comentario


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['nombre', 'correo', 'texto']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'comentario-form__input',
                'placeholder': 'Tu nombre',
                'maxlength': '100',
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'comentario-form__input',
                'placeholder': 'Tu correo electrónico',
            }),
            'texto': forms.Textarea(attrs={
                'class': 'comentario-form__textarea',
                'placeholder': 'Cuéntanos tu experiencia en Cabañas El Progreso...',
                'maxlength': '1000',
                'rows': 4,
            }),
        }
