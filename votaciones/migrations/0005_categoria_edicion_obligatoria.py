from django.db import migrations, models
import django.db.models.deletion


def validate_categories_have_editions(apps, schema_editor):
    Categoria = apps.get_model("votaciones", "Categoria")
    if Categoria.objects.using(schema_editor.connection.alias).filter(
        edicion__isnull=True
    ).exists():
        raise RuntimeError(
            "No se puede hacer obligatoria la edición: hay categorías sin edición. "
            "Asigne una edición a esas categorías y vuelva a ejecutar la migración."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("votaciones", "0004_voto_categoria_edicion_unicidad"),
    ]

    operations = [
        migrations.RunPython(
            validate_categories_have_editions,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="categoria",
            name="edicion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="votaciones.edicion",
            ),
        ),
    ]
