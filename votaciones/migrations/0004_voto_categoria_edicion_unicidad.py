from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Count, F


def validate_existing_votes(apps, schema_editor):
    Voto = apps.get_model("votaciones", "Voto")
    using = schema_editor.connection.alias
    votos = Voto.objects.using(using)

    if votos.filter(votacion__categoria__edicion__isnull=True).exists():
        raise RuntimeError(
            "No se puede migrar Voto: hay votos cuya categoría no tiene edición. "
            "Asigne una edición a esas categorías y vuelva a ejecutar la migración."
        )

    if votos.exclude(opcion__votacion_id=F("votacion_id")).exists():
        raise RuntimeError(
            "No se puede migrar Voto: hay opciones que no corresponden "
            "a la votación guardada."
        )

    duplicate_votes = (
        votos.values(
            "usuario_id",
            "votacion__categoria_id",
            "votacion__categoria__edicion_id",
        )
        .annotate(total=Count("pk"))
        .filter(total__gt=1)
    )
    if duplicate_votes.exists():
        raise RuntimeError(
            "No se puede migrar Voto: hay usuarios con más de un voto "
            "en una misma categoría y edición. Revise esos registros antes "
            "de volver a ejecutar la migración."
        )


def populate_vote_category_edition(apps, schema_editor):
    Voto = apps.get_model("votaciones", "Voto")
    using = schema_editor.connection.alias
    votos = Voto.objects.using(using).select_related(
        "votacion__categoria"
    )
    batch = []

    for voto in votos.iterator():
        voto.categoria_id = voto.votacion.categoria_id
        voto.edicion_id = voto.votacion.categoria.edicion_id
        batch.append(voto)

        if len(batch) == 500:
            Voto.objects.using(using).bulk_update(
                batch,
                ["categoria", "edicion"],
            )
            batch.clear()

    if batch:
        Voto.objects.using(using).bulk_update(
            batch,
            ["categoria", "edicion"],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("votaciones", "0003_edicion_categoria_edicion"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(
            validate_existing_votes,
            migrations.RunPython.noop,
        ),
        migrations.AddField(
            model_name="voto",
            name="categoria",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to="votaciones.categoria",
            ),
        ),
        migrations.AddField(
            model_name="voto",
            name="edicion",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to="votaciones.edicion",
            ),
        ),
        migrations.RunPython(
            populate_vote_category_edition,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name="voto",
            name="un_voto_por_usuario_y_votacion",
        ),
        migrations.AlterField(
            model_name="voto",
            name="categoria",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to="votaciones.categoria",
            ),
        ),
        migrations.AlterField(
            model_name="voto",
            name="edicion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to="votaciones.edicion",
            ),
        ),
        migrations.AddConstraint(
            model_name="voto",
            constraint=models.UniqueConstraint(
                fields=("usuario", "categoria", "edicion"),
                name="un_voto_por_usuario_categoria_edicion",
            ),
        ),
    ]
