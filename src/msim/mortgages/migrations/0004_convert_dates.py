import datetime

from django.db import migrations


def convert_dates(apps, schema_editor):
    Mortgage = apps.get_model("mortgages.Mortgage")

    for mortgage in Mortgage.objects.all():
        mortgage.start_date = datetime.datetime(
            year=mortgage.start_year,
            month=mortgage.start_month,
            day=1,
        )

        mortgage.save()


class Migration(migrations.Migration):

    dependencies = [
        ("mortgages", "0003_mortgage_start_date"),
    ]

    operations = [
        migrations.RunPython(convert_dates, migrations.RunPython.noop)
    ]
