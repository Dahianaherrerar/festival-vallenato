"""Formularios del panel de Administración (crear y editar)."""

from django import forms

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion


class EstiloBootstrap:
    """Agrega las clases de Bootstrap a todos los campos del formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                clase = "form-check-input"
            elif isinstance(widget, forms.Select):
                clase = "form-select"
            else:
                clase = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {clase}".strip()
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 3)


class EdicionForm(EstiloBootstrap, forms.ModelForm):
    class Meta:
        model = Edicion
        fields = ["anio", "nombre", "descripcion", "activa"]
        labels = {
            "anio": "Año",
            "nombre": "Nombre",
            "descripcion": "Descripción",
            "activa": "Edición activa",
        }
        error_messages = {
            "anio": {"unique": "Ya existe una edición con ese año."},
        }


class ConcursoForm(EstiloBootstrap, forms.ModelForm):
    class Meta:
        model = Concurso
        fields = ["edicion", "nombre", "descripcion", "activo"]
        labels = {
            "edicion": "Edición",
            "nombre": "Nombre del concurso",
            "descripcion": "Descripción",
            "activo": "Concurso activo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["edicion"].queryset = Edicion.objects.order_by("-anio")

    def clean(self):
        datos = super().clean()
        edicion, nombre = datos.get("edicion"), datos.get("nombre")
        if edicion and nombre and (
            Concurso.objects.filter(edicion=edicion, nombre__iexact=nombre)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            self.add_error("nombre", "Ya existe un concurso con ese nombre en esta edición.")
        return datos



class CategoriaForm(EstiloBootstrap, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["concurso", "nombre", "descripcion", "activa"]
        labels = {
            "concurso": "Concurso",
            "nombre": "Nombre de la categoría",
            "descripcion": "Descripción",
            "activa": "Categoría activa",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["concurso"].queryset = Concurso.objects.select_related("edicion").order_by(
            "-edicion__anio", "nombre"
        )

    def clean(self):
        datos = super().clean()
        concurso = datos.get("concurso")
        nombre = datos.get("nombre")

        if concurso and nombre:
            duplicada = Categoria.objects.filter(
                concurso=concurso,
                nombre__iexact=nombre.strip(),
            )

            if self.instance.pk:
                duplicada = duplicada.exclude(pk=self.instance.pk)

            if duplicada.exists():
                self.add_error(
                    "nombre",
                    "Ya existe una categoría con ese nombre en este concurso.",
                )

        return datos



class SelectorCategoria(forms.ModelChoiceField):
    def label_from_instance(self, categoria):
        return f"{categoria.concurso.nombre} · {categoria.nombre} ({categoria.edicion.anio})"


class SelectorVotacion(forms.ModelChoiceField):
    def label_from_instance(self, votacion):
        categoria = votacion.categoria
        return f"{categoria.concurso.nombre} · {categoria.nombre} · {votacion.titulo}"


class FechaHoraInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%dT%H:%M", **kwargs)


class VotacionForm(EstiloBootstrap, forms.ModelForm):
    categoria = SelectorCategoria(
        queryset=Categoria.objects.select_related("concurso", "edicion").order_by(
            "-edicion__anio", "concurso__nombre", "nombre"
        ),
        label="Categoría",
    )

    class Meta:
        model = Votacion
        fields = ["categoria", "titulo", "descripcion", "fecha_inicio", "fecha_fin", "abierta"]
        labels = {
            "titulo": "Título de la votación",
            "descripcion": "Descripción",
            "fecha_inicio": "Inicio",
            "fecha_fin": "Cierre",
            "abierta": "Votación abierta",
        }
        widgets = {
            "fecha_inicio": FechaHoraInput(),
            "fecha_fin": FechaHoraInput(),
        }



class ParticipanteForm(EstiloBootstrap, forms.ModelForm):
    votacion = SelectorVotacion(
        queryset=Votacion.objects.select_related(
            "categoria__concurso", "categoria__edicion"
        ).order_by(
            "-categoria__edicion__anio",
            "categoria__concurso__nombre",
            "categoria__nombre",
        ),
        label="Votación (concurso · categoría · votación)",
    )

    class Meta:
        model = Opcion
        fields = ["votacion", "nombre", "descripcion", "activo"]
        labels = {
            "nombre": "Nombre del participante",
            "descripcion": "Descripción",
            "activo": "Participante activo",
        }

    def clean(self):
        datos = super().clean()
        votacion = datos.get("votacion")
        nombre = datos.get("nombre")

        if votacion and nombre:
            duplicada = Opcion.objects.filter(
                votacion=votacion,
                nombre__iexact=nombre.strip(),
            )

            if self.instance.pk:
                duplicada = duplicada.exclude(pk=self.instance.pk)

            if duplicada.exists():
                self.add_error(
                    "nombre",
                    "Ya existe un participante con ese nombre en esta votación.",
                )

        return datos
