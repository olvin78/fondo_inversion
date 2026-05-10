from django.db import migrations, models
from django.db.models import Q


def populate_communication_identifiers(apps, schema_editor):
    Communication = apps.get_model("investors", "Communication")
    for communication in Communication.objects.filter(Q(identifier__isnull=True) | Q(identifier="")):
        communication.identifier = f"COM-{communication.pk:06d}"
        communication.save(update_fields=["identifier"])


class Migration(migrations.Migration):

    dependencies = [
        ("investors", "0011_communication_attachment"),
    ]

    operations = [
        migrations.AddField(
            model_name="communication",
            name="identifier",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=20,
                null=True,
                unique=True,
                verbose_name="Identificador",
            ),
        ),
        migrations.RunPython(
            populate_communication_identifiers,
            migrations.RunPython.noop,
        ),
    ]
