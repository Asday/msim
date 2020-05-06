from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse

import attr

from .utils import payment


def between(lower, upper):
    """
    Inclusive of bounds.
    """
    return [MinValueValidator(lower), MaxValueValidator(upper)]


class Mortgage(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    start_year = models.PositiveIntegerField()
    start_month = models.PositiveSmallIntegerField(validators=between(1, 12))
    amount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    term = models.PositiveSmallIntegerField()
    initial_period = models.PositiveSmallIntegerField()
    interest_rate_initial = models.DecimalField(max_digits=5, decimal_places=5)
    interest_rate_thereafter = models.DecimalField(
        max_digits=5,
        decimal_places=5,
    )
    income = models.DecimalField(max_digits=9, decimal_places=2)
    expenditure = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return (
            f"Mortgage of {self.amount} commencing {self.start_year}-"
            f"{self.start_month:02d}"
        )

    def get_absolute_url(self):
        return reverse("mortgages:detail", kwargs={"pk": self.pk})

    @property
    def interest_rates(self):
        return {
            True: self.interest_rate_initial,
            False: self.interest_rate_thereafter,
        }

    def get_payment_amounts(self):
        try:
            initial = self.actualinitialpayment.amount
        except ActualInitialPayment.DoesNotExist:
            initial = None

        try:
            thereafter = self.actualthereafterpayment.amount
        except ActualThereafterPayment.DoesNotExist:
            thereafter = None

        return {
            True: initial or payment(
                self.interest_rates[True] / 12,
                self.term,
                self.amount,
            ),
            False: thereafter or payment(
                self.interest_rates[False] / 12,
                self.term,
                self.amount,
            ),
        }


class ActualPayment(models.Model):
    mortgage = models.OneToOneField(
        "mortgages.Mortgage",
        on_delete=models.CASCADE,
        related_name="%(class)s",
    )
    amount = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        abstract = True

    def __str__(self):
        class_name = self.__class__._meta.verbose_name.capitalize()

        return f"{class_name} of {self.amount}"


class ActualInitialPayment(ActualPayment):
    pass


class ActualThereafterPayment(ActualPayment):
    pass


class AmountQuerySet(models.QuerySet):

    def for_mortgage(self, mortgage):
        return self.filter(mortgage=mortgage)

    def owned_by(self, user):
        return self.filter(mortgage__owner=user)


class AmountManager(models.Manager.from_queryset(AmountQuerySet)):
    pass


class Amount(models.Model):
    mortgage = models.OneToOneField(
        "mortgages.Mortgage",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    month = models.PositiveSmallIntegerField()

    objects = AmountManager()

    class Meta:
        abstract = True
        unique_together = (
            ("mortgage", "month"),
        )

    def __str__(self):
        class_name = self.__class__._meta.verbose_name.capitalize()

        return f"{class_name} of {self.amount}"


class Overpayment(Amount):
    pass


class Discrepancy(Amount):
    pass


@attr.s
class LedgerEntryAmount:
    ledger_entry = attr.ib()
    amount = attr.ib()
    in_get = attr.ib()
    pk = attr.ib()
    type = attr.ib()

    @property
    def month_number(self):
        return self.ledger_entry.month_number

    @property
    def delete(self):
        return f"mortgages:{self.type}.delete"

    @property
    def create_update(self):
        return f"mortgages:{self.type}.create_update"

    @property
    def name(self):
        return f"{self.type}_amount_{self.month_number}"


@attr.s
class LedgerEntry:
    month_number = attr.ib()
    mortgage_pk = attr.ib()
    year = attr.ib()
    month = attr.ib()
    opening_balance = attr.ib()
    interest = attr.ib()
    payment = attr.ib()
    overpayment = attr.ib()
    discrepancy = attr.ib()

    overpayment_in_get = attr.ib(default=False)
    overpayment_pk = attr.ib(default=None)
    discrepancy_in_get = attr.ib(default=False)
    discrepancy_pk = attr.ib(default=None)

    @property
    def closing_balance(self):
        return sum([
            self.opening_balance,
            self.interest,
            self.payment,
            self.overpayment,
            self.discrepancy,
        ])

    def normalise(self):
        if self.closing_balance > 0:
            self.payment = min(
                self.payment,
                abs(self.opening_balance + self.interest),
            )
            self.overpayment = abs(sum([
                self.opening_balance,
                self.interest,
                self.payment,
            ]))

    @property
    def as_tr(self):
        return render_to_string(
            "mortgages/_ledgerentry_tr.html",
            self.as_context,
        )

    @property
    def as_context(self):
        return {
            "year": self.year,
            "month": self.month,
            "opening_balance": self.opening_balance,
            "interest": self.interest,
            "payment": self.payment,
            "overpayment": LedgerEntryAmount(
                ledger_entry=self,
                amount=self.overpayment,
                in_get=self.overpayment_in_get,
                pk=self.overpayment_pk,
                type="overpayment",
            ),
            "discrepancy": LedgerEntryAmount(
                ledger_entry=self,
                amount=self.discrepancy,
                in_get=self.discrepancy_in_get,
                pk=self.discrepancy_pk,
                type="discrepancy",
            ),
            "closing_balance": self.closing_balance,
        }
