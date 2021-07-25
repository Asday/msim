import django.core.validators
from django.db import migrations, models


# Duplicated from `mortgages.utils`.
def payment(interest_rate, period_count, principal):
    j = (interest_rate + 1) ** period_count

    return round(principal * ((interest_rate * j) / (j - 1)), 2)


def set_default_overpayments(apps, schema_editor):
    Mortgage = apps.get_model("mortgages.Mortgage")
    ActualInitialPayment = apps.get_model("mortgages.ActualInitialPayment")
    ActualThereafterPayment = apps.get_model(
        "mortgages.ActualThereafterPayment",
    )

    for mortgage in Mortgage.objects.all():
        disposable_income = mortgage.income - mortgage.expenditure
        try:
            payment_initial = mortgage.actualinitialpayment.amount
        except ActualInitialPayment.DoesNotExist:
            payment_initial = payment(
                mortgage.interest_rate_initial / 12,
                mortgage.term,
                mortgage.amount,
            )

        try:
            payment_thereafter = mortgage.actualthereafterpayment.amount
        except ActualThereafterPayment.DoesNotExist:
            payment_thereafter = payment(
                mortgage.interest_rate_thereafter / 12,
                mortgage.term,
                mortgage.amount,
            )

        mortgage.default_overpayment_initial = max(
            disposable_income - payment_initial,
            0,
        )
        mortgage.default_overpayment_thereafter = max(
            disposable_income - payment_thereafter,
            0,
        )

        mortgage.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mortgages', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mortgage',
            name='default_overpayment_initial',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=9,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='mortgage',
            name='default_overpayment_thereafter',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=9,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.RunPython(
            set_default_overpayments,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='mortgage',
            name='default_overpayment_initial',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='calculated automatically if left blank',
                max_digits=9,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name='mortgage',
            name='default_overpayment_thereafter',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='calculated automatically if left blank',
                max_digits=9,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
    ]
