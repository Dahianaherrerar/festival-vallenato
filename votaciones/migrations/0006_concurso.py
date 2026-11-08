"""Agrega el nivel Concurso: Edición → Concurso → Categoría → Votación → Opción.

Las categorías que ya existían pasan al «Concurso general» de su edición,
para no perder datos.
"""

from django.db import migrations, models
import django.db.models.deletion


def asignar_concurso_general(apps, schema_editor):
    Categoria = apps.get_model("votaciones", "Categoria")
    Concurso = apps.get_model("votaciones", "Concurso")
    db = schema_editor.connection.alias

    for categoria in Categoria.objects.using(db).filter(concurso__isnull=True):
        concurso, _ = Concurso.objects.using(db).get_or_create(
            edicion_id=categoria.edicion_id,
            nombre="Concurso general",
        )
        categoria.concurso = concurso
        categoria.save(update_fields=["concurso"])


class Migration(migrations.Migration):

    dependencies = [
        ("votaciones", "0005_categoria_edicion_obligatoria"),
    ]

    operations = [
        migrations.CreateModel(
            name="Concurso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=150)),
                ("descripcion", models.TextField(blank=True)),
                ("activo", models.BooleanField(default=True)),
                (
                    "edicion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="concursos",
                        to="votaciones.edicion",
                    ),
                ),
            ],
            options={
                "verbose_name": "concurso",
                "verbose_name_plural": "concursos",
                "ordering": ["edicion", "nombre"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("edicion", "nombre"),
                        name="concurso_unico_por_edicion",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="categoria",
            name="concurso",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="votaciones.concurso",
            ),
        ),
        migrations.RunPython(asignar_concurso_general, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="categoria",
            name="concurso",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="votaciones.concurso",
            ),
        ),
        migrations.AlterField(
            model_name="categoria",
            name="edicion",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="votaciones.edicion",
            ),
        ),
    ]
