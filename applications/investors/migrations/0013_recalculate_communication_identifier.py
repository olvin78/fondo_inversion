from django.db import migrations


def recalculate_communication_identifiers(apps, schema_editor):
    Communication = apps.get_model("investors", "Communication")
    for communication in Communication.objects.all():
        communication.identifier = f"COM-{communication.pk + 499}"
        communication.save(update_fields=["identifier"])


class Migration(migrations.Migration):

    dependencies = [
        ("investors", "0012_communication_identifier"),
    ]

    operations = [
        migrations.RunPython(
            recalculate_communication_identifiers,
            migrations.RunPython.noop,
        ),
    ]
