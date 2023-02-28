from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F
from django.db.models.expressions import RawSQL
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

import attr

from .utils import payment


class MortgageQuerySet(models.QuerySet):

    def owned_by(self, user):
        return self.filter(owner=user)


class MortgageManager(models.Manager.from_queryset(MortgageQuerySet)):
    pass


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
    start_date = models.DateField()
    amount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    term = models.PositiveSmallIntegerField(help_text="months")
    initial_period = models.PositiveSmallIntegerField(help_text="months")
    interest_rate_initial = models.DecimalField(
        max_digits=5,
        decimal_places=5,
        help_text="(1% = 0.01)",
    )
    interest_rate_thereafter = models.DecimalField(
        max_digits=5,
        decimal_places=5,
        help_text="(1% = 0.01)",
    )
    income = models.DecimalField(max_digits=9, decimal_places=2)
    expenditure = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        help_text="(not including your mortgage payments)",
    )
    default_overpayment_initial = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        help_text="calculated automatically if left blank",
    )
    default_overpayment_thereafter = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        help_text="calculated automatically if left blank",
    )

    objects = MortgageManager()

    def __str__(self):
        return (
            f"Mortgage of {self.amount} commencing {self.start_date.year}-"
            f"{self.start_date.month:02d}"
        )

    def get_absolute_url(self):
        return reverse("mortgages:detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        self.ensure_defaults()

        return super().save(*args, **kwargs)

    @property
    def default_payment_initial(self):
        return payment(
            self.interest_rate_initial / 12,
            self.term,
            self.amount,
        )

    @property
    def default_payment_thereafter(self):
        return payment(
            self.interest_rate_thereafter / 12,
            self.term,
            self.amount,
        )

    @property
    def disposable_income(self):
        return self.income - self.expenditure

    def ensure_defaults(self):
        if self.default_overpayment_initial is None:
            self.default_overpayment_initial = max(
                self.disposable_income - self.default_payment_initial,
                0,
            )

        if self.default_overpayment_thereafter is None:
            self.default_overpayment_thereafter = max(
                self.disposable_income - self.default_payment_thereafter,
                0,
            )

    def as_periods(self):
        try:
            payment_initial = self.actualinitialpayment.amount
        except ActualInitialPayment.DoesNotExist:
            payment_initial = self.default_payment_initial

        try:
            payment_thereafter = self.actualthereafterpayment.amount
        except ActualThereafterPayment.DoesNotExist:
            payment_thereafter = self.default_payment_thereafter

        return Periods(periods=[
            Period(
                interest_rate=self.interest_rate_initial,
                payment=payment_initial,
                default_overpayment=self.default_overpayment_initial,
                start_month=0,
            ),
            Period(
                interest_rate=self.interest_rate_thereafter,
                payment=payment_thereafter,
                default_overpayment=self.default_overpayment_thereafter,
                start_month=self.initial_period,
            ),
        ])

    def duplicate(self):
        try:
            initial = self.actualinitialpayment
        except ActualInitialPayment.DoesNotExist:
            initial = None

        try:
            thereafter = self.actualthereafterpayment
        except ActualThereafterPayment.DoesNotExist:
            thereafter = None

        overpayments = Overpayment.objects.for_mortgage(self)
        discrepancies = Discrepancy.objects.for_mortgage(self)

        self.pk = None
        self.save()

        if initial is not None:
            initial.duplicate_for(self)

        if thereafter is not None:
            thereafter.duplicate_for(self)

        for overpayment in overpayments:
            overpayment.duplicate_for(self)

        for discrepancy in discrepancies:
            discrepancy.duplicate_for(self)

        return self


class ActualPaymentQuerySet(models.QuerySet):

    def for_mortgage(self, mortgage):
        return self.filter(mortgage=mortgage)


class ActualPaymentManager(
    models.Manager.from_queryset(ActualPaymentQuerySet),
):
    pass


class ActualPayment(models.Model):
    mortgage = models.OneToOneField(
        "mortgages.Mortgage",
        on_delete=models.CASCADE,
        related_name="%(class)s",
    )
    amount = models.DecimalField(max_digits=9, decimal_places=2)

    objects = ActualPaymentManager()

    class Meta:
        abstract = True

    def __str__(self):
        class_name = self.__class__._meta.verbose_name.capitalize()

        return f"{class_name} of {self.amount}"

    def duplicate_for(self, mortgage):
        self.pk = None
        self.mortgage = mortgage

        self.save()

    @staticmethod
    def get_default(mortgage):
        raise NotImplementedError()


class ActualInitialPayment(ActualPayment):

    @staticmethod
    def get_default(mortgage):
        return mortgage.default_payment_initial


class ActualThereafterPayment(ActualPayment):

    @staticmethod
    def get_default(mortgage):
        return mortgage.default_payment_thereafter


class AmountQuerySet(models.QuerySet):

    def for_mortgage(self, mortgage):
        return self.filter(mortgage=mortgage)

    def owned_by(self, user):
        return self.filter(mortgage__owner=user)

    def as_monthly_dict(self):
        return {
            amount.month: amount
            for amount in self
        }

    def average(self):
        return self.aggregate(a=models.Avg("amount"))["a"]

    def with_current_month(self):
        return (
            self
            .annotate(start_date=F("mortgage__start_date"))
            .annotate(current_month=RawSQL(
                "SELECT start_date + make_interval(0, month)"
                " AS current_month",
                (),
            ))
        )

    def in_the_past(self):
        return (
            self
            .with_current_month()
            .filter(current_month__lte=timezone.now())
        )


class AmountManager(models.Manager.from_queryset(AmountQuerySet)):
    pass


class Amount(models.Model):
    mortgage = models.ForeignKey(
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

    def duplicate_for(self, mortgage):
        self.pk = None
        self.mortgage = mortgage

        self.save()


class Overpayment(Amount):
    pass


class Discrepancy(Amount):
    pass


@attr.s
class LedgerEntryAmount:
    ledger_entry = attr.ib()
    amount = attr.ib()
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

    overpayment_pk = attr.ib(default=None)
    discrepancy_pk = attr.ib(default=None)

    default_overpayment = None

    def __attrs_post_init__(self):
        self.default_overpayment = self.overpayment

    @property
    def overpayment_delta(self):
        return self.default_overpayment - self.overpayment

    @property
    def overpayment_delta_positive(self):
        return self.overpayment_delta > 0

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
                abs(self.opening_balance + self.interest + self.discrepancy),
            )
            self.overpayment = abs(sum([
                self.opening_balance,
                self.interest,
                self.discrepancy,
                self.payment,
            ]))

    @property
    def month_name(self):
        return f"{self.year}-{self.month:02d}"

    @property
    def as_tds(self):
        return render_to_string(
            "mortgages/_ledgerentry_tds.html",
            self.as_context,
        )

    @property
    def as_context(self):
        return {
            "month_name": self.month_name,
            "opening_balance": self.opening_balance,
            "interest": self.interest,
            "payment": self.payment,
            "overpayment": LedgerEntryAmount(
                ledger_entry=self,
                amount=self.overpayment,
                pk=self.overpayment_pk,
                type="overpayment",
            ),
            "discrepancy": LedgerEntryAmount(
                ledger_entry=self,
                amount=self.discrepancy,
                pk=self.discrepancy_pk,
                type="discrepancy",
            ),
            "closing_balance": self.closing_balance,
        }


@attr.s
class Period:
    interest_rate = attr.ib()
    payment = attr.ib()
    default_overpayment = attr.ib()
    start_month = attr.ib()


@attr.s
class Periods:
    periods = attr.ib()

    @property
    def sorted_periods(self):
        return sorted(
            self.periods,
            key=lambda period: period.start_month,
            reverse=True,
        )

    def get_period(self, month):
        for period in self.sorted_periods:
            if period.start_month <= month:
                return period


@attr.s
class Ledger:
    mortgage = attr.ib()

    ledger = None

    _overpayments = None
    _discrepancies = None
    _periods = None

    def __attrs_post_init__(self):
        self.ledger = []

    @property
    def periods(self):
        if self._periods is not None:
            return self._periods

        self._periods = self.mortgage.as_periods()

        return self._periods

    @property
    def balance(self):
        if not self.ledger:
            return -self.mortgage.amount

        return self.ledger[-1].closing_balance

    @property
    def complete(self):
        return self.balance == 0

    @property
    def next_year_month(self):
        if not self.ledger:
            return {
                "year": self.mortgage.start_date.year,
                "month": self.mortgage.start_date.month,
            }

        month = self.ledger[-1].month + 1
        year = self.ledger[-1].year
        if month == 13:  # Decemberer.
            month = 1
            year += 1

        return {"year": year, "month": month}

    @property
    def overpayments(self):
        if self._overpayments is not None:
            return self._overpayments

        self._overpayments = (
            Overpayment.objects
            .for_mortgage(self.mortgage)
            .as_monthly_dict()
        )

        return self._overpayments

    @property
    def discrepancies(self):
        if self._discrepancies is not None:
            return self._discrepancies

        self._discrepancies = (
            Discrepancy.objects
            .for_mortgage(self.mortgage)
            .as_monthly_dict()
        )

        return self._discrepancies

    def _set_amount(self, overpayments, month, to):
        target = self._overpayments if overpayments else self._discrepancies

        current = target.get(month)
        if current == to:
            return

        if to is None:  # Delete.
            target.pop(month)
        else:
            target[month] = to

        self.ledger = self.ledger[:month]

    def set_overpayment(self, month, to):
        return self._set_amount(overpayments=True, month=month, to=to)

    def delete_overpayment(self, month):
        return self._set_amount(overpayments=True, month=month, to=None)

    def set_discrepancy(self, month, to):
        return self._set_amount(overpayments=False, month=month, to=to)

    def delete_discrepancy(self, month):
        return self._set_amount(overpayments=False, month=month, to=None)

    def calculate_entry(self):
        month_number = len(self.ledger)
        period = self.periods.get_period(month_number)

        entry = LedgerEntry(
            month_number=month_number,
            mortgage_pk=self.mortgage.pk,
            **self.next_year_month,
            opening_balance=self.balance,
            interest=round(self.balance * period.interest_rate / 12, 2),
            payment=period.payment,
            overpayment=period.default_overpayment,
            discrepancy=Decimal("0"),
        )

        # If there are real values for this month's discrepancy or
        # overpayment, use those instead.
        overpayment = self.overpayments.get(month_number)
        if overpayment is not None:
            entry.overpayment = overpayment.amount
            entry.overpayment_pk = overpayment.pk

        discrepancy = self.discrepancies.get(month_number)
        if discrepancy is not None:
            entry.discrepancy = discrepancy.amount
            entry.discrepancy_pk = discrepancy.pk

        entry.normalise()

        self.ledger.append(entry)

    def calculate_entries(self):
        while not self.complete:
            self.calculate_entry()

    def calculate_cost(self):
        self.calculate_entries()

        return sum(sum(
            [[entry.interest, entry.discrepancy] for entry in self.ledger],
            [],
        ))

    @property
    def month_choices(self):
        self.calculate_entries()

        return tuple((
            (entry.month_number, entry.month_name)
            for entry in self.ledger
        ))
