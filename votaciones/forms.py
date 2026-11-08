
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
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


class RecuperarClaveForm(PasswordResetForm):
    """Pide el correo registrado para enviar el enlace de restablecimiento."""

    email = forms.EmailField(
        label="Correo electrónico registrado",
        max_length=254,
        error_messages={
            "required": "Escribe el correo con el que te registraste.",
            "invalid": "Escribe un correo electrónico válido.",
        },
        widget=forms.EmailInput(
            attrs={"autocomplete": "email", "placeholder": "tucorreo@ejemplo.com"}
        ),
    )


class NuevaClaveForm(SetPasswordForm):
    """Pantalla del enlace: nueva contraseña y su confirmación."""

    error_messages = {
        **SetPasswordForm.error_messages,
        "password_mismatch": "Las dos contraseñas no coinciden.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "Nueva contraseña"
        self.fields["new_password2"].label = "Confirmar contraseña"
        self.fields["new_password2"].help_text = ""


class VotoForm(forms.Form):
    """Formulario del voto: el usuario elige una opción de la votación.

    Solo acepta opciones de la votación recibida. Si alguien envía a la
    fuerza el id de una opción de otra votación o categoría (CP-06), el
    formulario la rechaza con un mensaje claro.
    """

    MENSAJE_OPCION_INVALIDA = (
        "La opción seleccionada no pertenece a esta votación. "
        "Elige una de las opciones disponibles."
    )

    opcion = forms.ModelChoiceField(
        queryset=Opcion.objects.none(),
        widget=forms.RadioSelect,
        label="Selecciona tu candidato",
        empty_label=None,
        error_messages={
            "required": "Debes seleccionar una opción para votar.",
            "invalid_choice": MENSAJE_OPCION_INVALIDA,
        },
    )

    def __init__(self, *args, votacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.votacion = votacion

        if votacion is not None:
            self.fields["opcion"].queryset = Opcion.objects.filter(
                votacion=votacion,
                activo=True,
            )

    def clean_opcion(self):
        opcion = self.cleaned_data["opcion"]

        # Segunda comprobación en el servidor: la opción debe pertenecer a
        # la misma votación, categoría y edición en la que se está votando.
        if self.votacion is not None and (
            opcion.votacion_id != self.votacion.pk
            or opcion.votacion.categoria_id != self.votacion.categoria_id
            or opcion.votacion.categoria.edicion_id
            != self.votacion.categoria.edicion_id
        ):
            raise forms.ValidationError(self.MENSAJE_OPCION_INVALIDA)

        return opcion

