
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Opcion

Usuario = get_user_model()


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta:
        model = Usuario
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta registrada con este correo."
            )

        return email
    
class VotoForm(forms.Form):
    opcion = forms.ModelChoiceField(
        queryset=Opcion.objects.none(),
        widget=forms.RadioSelect,
        label="Selecciona tu candidato",
        empty_label=None,
    )

    def __init__(self, *args, votacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.votacion = votacion

        if votacion is not None:
            self.fields["opcion"].queryset = Opcion.objects.filter(
                votacion=votacion
            )

