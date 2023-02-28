from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mortgages", "0002_configurable_overpayments"),
    ]

    operations = [
        migrations.AddField(
            model_name="mortgage",
            name="start_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
