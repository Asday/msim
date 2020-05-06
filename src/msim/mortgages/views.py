from decimal import Decimal
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, FormView, ListView

from . import forms
from .models import Discrepancy, LedgerEntry, Mortgage, Overpayment


class OwnerMixin:

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class MortgageList(LoginRequiredMixin, OwnerMixin, ListView):
    model = Mortgage


class MortgageDetail(LoginRequiredMixin, OwnerMixin, DetailView):
    model = Mortgage

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        overpayments = Overpayment.objects.for_mortgage(self.object)
        list(overpayments)
        discrepancies = Discrepancy.objects.for_mortgage(self.object)
        list(overpayments)

        payment_amounts = self.object.get_payment_amounts()
        current_year = self.object.start_year
        current_month = self.object.start_month

        ledger = []
        balance = -self.object.amount
        while balance:
            month_number = len(ledger)
            initial_period = month_number <= self.object.initial_period
            payment_amount = payment_amounts[initial_period]
            entry = LedgerEntry(
                month_number=month_number,
                mortgage_pk=self.object.pk,
                year=current_year,
                month=current_month,
                opening_balance=balance,
                interest=round(
                    balance * self.object.interest_rates[initial_period] / 12,
                    2,
                ),
                payment=payment_amount,
                overpayment=max(
                    0,
                    sum([
                        self.object.income,
                        -self.object.expenditure,
                        -payment_amount,
                    ]),
                ),
                discrepancy=Decimal("0"),
            )

            # If there are real values for this month's discrepancy or
            # overpayment, use those instead.
            try:
                overpayment = overpayments.get(month=month_number)
                entry.overpayment = overpayment.amount
                entry.overpayment_pk = overpayment.pk
            except Overpayment.DoesNotExist:
                pass

            try:
                discrepancy = discrepancies.get(month=month_number)
                entry.discrepancy = discrepancy.amount
                entry.discrepancy_pk = discrepancy.pk
            except Discrepancy.DoesNotExist:
                pass

            # If the user has provided temporary values for this
            # month's discrepancy or overpayment, use THOSE instead.
            #
            # Normalise the entry before to account for the amount
            # usually changing for the last payment, and after to deal
            # with the user being silly.
            #
            # No user input sanitisation because I'm lazy and angry at
            # estate agents.
            entry.normalise()
            if f"revert_{month_number}_overpayment" not in self.request.GET:
                overpayment = self.request.GET.get(
                    f"overpayment_amount_{month_number}",
                )
                if overpayment not in (None, str(entry.overpayment)):
                    entry.overpayment = Decimal(overpayment)
                    entry.overpayment_in_get = True

            if f"revert_{month_number}_discrepancy" not in self.request.GET:
                discrepancy = self.request.GET.get(
                    f"discrepancy_amount_{month_number}",
                )
                if discrepancy not in (None, str(entry.discrepancy)):
                    entry.discrepancy = Decimal(discrepancy)
                    entry.discrepancy_in_get = True


            entry.normalise()

            balance = entry.closing_balance
            current_month += 1
            if current_month == 13:  # Decemberer.
                current_month = 1
                current_year += 1
            ledger.append(entry)

        return {
            **context,
            "ledger": ledger,
            "total_cost": sum(sum(
                [[entry.interest, entry.discrepancy] for entry in ledger],
                [],
            )),
        }


class AmountOwnerMixin:

    def get_queryset(self):
        return super().get_queryset().owned_by(self.request.user)


class BaseAmountCreateUpdate(LoginRequiredMixin, AmountOwnerMixin, FormView):
    form_class = forms.AmountCreateUpdate

    def form_valid(self, form):
        form.save()

        return HttpResponse(status=204)

    def form_invalid(self, form):
        return HttpResponse(
            json.dumps(form.errors).encode("utf-8"),
            status=400,
            content_type="application/json",
        )

    def get_form_kwargs(self):
        kwargs = {
            **super().get_form_kwargs(),
            "model": self.model,
        }

        if "data" in kwargs:
            kwargs["data"] = kwargs["data"].copy()
            kwargs["data"]["mortgage"] = self.kwargs.get("pk")

        return kwargs


class DiscrepancyDelete(LoginRequiredMixin, AmountOwnerMixin, DeleteView):
    model = Discrepancy
    success_url = reverse_lazy("mortgages:list")


class DiscrepancyCreateUpdate(BaseAmountCreateUpdate):
    model = Discrepancy
    success_url = reverse_lazy("mortgages:list")
    fields = ["amount"]


class OverpaymentDelete(LoginRequiredMixin, AmountOwnerMixin, DeleteView):
    model = Overpayment
    success_url = reverse_lazy("mortgages:list")


class OverpaymentCreateUpdate(BaseAmountCreateUpdate):
    model = Overpayment
    success_url = reverse_lazy("mortgages:list")
