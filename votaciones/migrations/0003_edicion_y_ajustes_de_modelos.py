from django.db.models import Count
import django.db.models.deletion
from django.db import migrations, models


def validar_unicidad_existente(apps, schema_editor):
    Categoria = apps.get_model("votaciones", "Categoria")
    Votacion = apps.get_model("votaciones", "Votacion")
    Opcion = apps.get_model("votaciones", "Opcion")
    alias = schema_editor.connection.alias
    consultas = (
        (Categoria.objects.using(alias), ("nombre",), "categorías"),
        (Votacion.objects.using(alias), ("categoria_id", "titulo"), "votaciones"),
        (Opcion.objects.using(alias), ("votacion_id", "nombre"), "opciones"),
    )
    duplicados = []
    for manager, campos, etiqueta in consultas:
        if manager.order_by().values(*campos).annotate(total=Count("pk")).filter(
            total__gt=1
        ).exists():
            duplicados.append(etiqueta)
    if duplicados:
        nombres = ", ".join(duplicados)
        raise RuntimeError(
            "No se aplicó la migración: hay registros duplicados en "
            f"{nombres}. Corrige esos duplicados y vuelve a ejecutar migrate."
        )


def asignar_edicion_2027(apps, schema_editor):
    Edicion = apps.get_model("votaciones", "Edicion")
    Categoria = apps.get_model("votaciones", "Categoria")
    edicion, _ = Edicion.objects.using(schema_editor.connection.alias).get_or_create(
        anio=2027,
        defaults={
            "nombre": "Festival de la Leyenda Vallenata 2027",
            "activa": True,
        },
    )
    Categoria.objects.using(schema_editor.connection.alias).filter(
        edicion__isnull=True
    ).update(edicion_id=edicion.pk)


class Migration(migrations.Migration):
    dependencies = [
        ("votaciones", "0002_votacion_opcion_voto"),
    ]

    operations = [
        migrations.RunPython(
            validar_unicidad_existente,
            migrations.RunPython.noop,
        ),
        migrations.CreateModel(
            name="Edicion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("anio", models.PositiveSmallIntegerField(unique=True, verbose_name="año")),
                ("nombre", models.CharField(max_length=120)),
                ("fecha_inicio", models.DateField(blank=True, null=True)),
                ("fecha_fin", models.DateField(blank=True, null=True)),
                (
                    "activa",
                    models.BooleanField(
                        default=False,
                        help_text="Es la edición que se muestra en la página de inicio. Solo una puede estar activa.",
                    ),
                ),
            ],
            options={
                "verbose_name": "edición",
                "verbose_name_plural": "ediciones",
                "ordering": ["-anio"],
            },
        ),
        migrations.AddField(
            model_name="categoria",
            name="edicion",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="votaciones.edicion",
                verbose_name="edición",
            ),
        ),
        migrations.RunPython(asignar_edicion_2027, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="categoria",
            name="edicion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="votaciones.edicion",
                verbose_name="edición",
            ),
        ),
        migrations.AlterField(
            model_name="categoria",
            name="descripcion",
            field=models.TextField(blank=True, verbose_name="descripción"),
        ),
        migrations.AlterField(
            model_name="categoria",
            name="nombre",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="votacion",
            name="descripcion",
            field=models.TextField(blank=True, verbose_name="descripción"),
        ),
        migrations.AlterField(
            model_name="votacion",
            name="abierta",
            field=models.BooleanField(
                default=False,
                help_text="Para poder votar debe estar marcada y dentro del periodo de votación.",
            ),
        ),
        migrations.AlterField(
            model_name="opcion",
            name="descripcion",
            field=models.TextField(blank=True, verbose_name="descripción"),
        ),
        migrations.AlterModelOptions(
            name="categoria",
            options={
                "ordering": ["edicion", "nombre"],
                "verbose_name": "categoría",
                "verbose_name_plural": "categorías",
            },
        ),
        migrations.AlterModelOptions(
            name="votacion",
            options={
                "ordering": ["titulo"],
                "verbose_name": "votación",
                "verbose_name_plural": "votaciones",
            },
        ),
        migrations.AlterModelOptions(
            name="opcion",
            options={
                "ordering": ["nombre"],
                "verbose_name": "opción",
                "verbose_name_plural": "opciones",
            },
        ),
        migrations.AlterModelOptions(
            name="voto",
            options={
                "verbose_name": "voto",
                "verbose_name_plural": "votos",
            },
        ),
        migrations.AddConstraint(
            model_name="categoria",
            constraint=models.UniqueConstraint(
                fields=("edicion", "nombre"),
                name="categoria_nombre_unico_por_edicion",
            ),
        ),
        migrations.AddConstraint(
            model_name="votacion",
            constraint=models.UniqueConstraint(
                fields=("categoria", "titulo"),
                name="votacion_titulo_unico_por_categoria",
            ),
        ),
        migrations.AddConstraint(
            model_name="opcion",
            constraint=models.UniqueConstraint(
                fields=("votacion", "nombre"),
                name="opcion_nombre_unico_por_votacion",
            ),
        ),
    ]
