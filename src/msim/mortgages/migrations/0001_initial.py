from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Mortgage',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('start_year', models.PositiveIntegerField()),
                (
                    'start_month',
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(12),
                        ],
                    ),
                ),
                (
                    'amount',
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=9,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                        ],
                    ),
                ),
                ('term', models.PositiveSmallIntegerField(help_text='months')),
                (
                    'initial_period',
                    models.PositiveSmallIntegerField(help_text='months'),
                ),
                (
                    'interest_rate_initial',
                    models.DecimalField(
                        decimal_places=5,
                        help_text='(1% = 0.01)',
                        max_digits=5,
                    ),
                ),
                (
                    'interest_rate_thereafter',
                    models.DecimalField(
                        decimal_places=5,
                        help_text='(1% = 0.01)',
                        max_digits=5,
                    ),
                ),
                (
                    'income',
                    models.DecimalField(decimal_places=2, max_digits=9),
                ),
                (
                    'expenditure',
                    models.DecimalField(
                        decimal_places=2,
                        help_text='(not including your mortgage payments)',
                        max_digits=9,
                    ),
                ),
                (
                    'owner',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='ActualThereafterPayment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=9),
                ),
                (
                    'mortgage',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='actualthereafterpayment',
                        to='mortgages.Mortgage',
                    )
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ActualInitialPayment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=9),
                ),
                (
                    'mortgage',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='actualinitialpayment',
                        to='mortgages.Mortgage',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Overpayment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=9),
                ),
                ('month', models.PositiveSmallIntegerField()),
                (
                    'mortgage',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='overpayments',
                        to='mortgages.Mortgage',
                    ),
                ),
            ],
            options={
                'abstract': False,
                'unique_together': {('mortgage', 'month')},
            },
        ),
        migrations.CreateModel(
            name='Discrepancy',
            fields=[
                (
                    'id',
                        models.AutoField(auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=9),
                ),
                ('month', models.PositiveSmallIntegerField()),
                (
                    'mortgage',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='discrepancys',
                        to='mortgages.Mortgage',
                    )
                ),
            ],
            options={
                'abstract': False,
                'unique_together': {('mortgage', 'month')},
            },
        ),
    ]
