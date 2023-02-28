from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mortgages", "0004_convert_dates"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="mortgage",
            name="start_month",
        ),
        migrations.RemoveField(
            model_name="mortgage",
            name="start_year",
        ),
        migrations.AlterField(
            model_name="mortgage",
            name="start_date",
            field=models.DateField(),
        ),
    ]
