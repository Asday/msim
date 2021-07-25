from copy import deepcopy
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from . import forms
from .models import (
    ActualInitialPayment,
    ActualThereafterPayment,
    Discrepancy,
    Ledger,
    Mortgage,
    Overpayment,
)


class MortgageCreateUpdateMixin:
    model = Mortgage
    fields = [
        "start_year",
        "start_month",
        "amount",
        "term",
        "initial_period",
        "interest_rate_initial",
        "interest_rate_thereafter",
        "income",
        "expenditure",
    ]


class MortgageCreate(
    LoginRequiredMixin,
    MortgageCreateUpdateMixin,
    CreateView,
):

    def form_valid(self, form):
        form.instance.owner = self.request.user

        return super().form_valid(form)


class OwnerMixin:

    def get_queryset(self):
        return super().get_queryset().owned_by(self.request.user)


class MortgageUpdate(
    LoginRequiredMixin,
    MortgageCreateUpdateMixin,
    OwnerMixin,
    UpdateView,
):
    pass


class MortgageList(LoginRequiredMixin, OwnerMixin, ListView):
    model = Mortgage


class MortgageDetail(LoginRequiredMixin, OwnerMixin, DetailView):
    model = Mortgage

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ledger = Ledger(mortgage=self.object)
        cost = ledger.calculate_cost()

        without_overriden_overpayments = {}
        for month in ledger.overpayments:
            without_overridden_overpayment = deepcopy(ledger)
            without_overridden_overpayment.delete_overpayment(month)
            cost_without_overpayment = (
                without_overridden_overpayment.calculate_cost()
            )

            # Positive for greater total cost.
            without_overriden_overpayments[month] = (
                cost_without_overpayment - cost
            )

        return {
            **context,
            "ledger": ledger.ledger,
            "total_cost": cost,
            "average_overpayment": self.object.overpayments.average(),
            "what_could_have_been": without_overriden_overpayments,
            "speculate_form": forms.SpeculateForm(
                month_choices=ledger.month_choices,
            )
        }


class ActualPaymentSet(
    LoginRequiredMixin,
    OwnerMixin,
    SingleObjectMixin,
    FormView,
):
    model = Mortgage
    form_class = forms.ActualPaymentSet
    template_name = "mortgages/actualpayment_set.html"
    actual_payment_model = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.object = self.get_object()

    def get_form_kwargs(self):
        if self.actual_payment_model is None:
            raise ImproperlyConfigured("no")

        return {
            **super().get_form_kwargs(),
            "model": self.actual_payment_model,
            "mortgage": self.object,
        }

    def form_valid(self, form):
        form.save()

        return HttpResponseRedirect(self.object.get_absolute_url())


class ActualInitialPaymentSet(ActualPaymentSet):
    actual_payment_model = ActualInitialPayment


class ActualThereafterPaymentSet(ActualPaymentSet):
    actual_payment_model = ActualThereafterPayment


class MortgageDuplicate(
    LoginRequiredMixin,
    OwnerMixin,
    SingleObjectMixin,
    FormView,
):
    model = Mortgage
    form_class = forms.MortgageDuplicate
    template_name = "mortgages/mortgage_duplicate.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.object = self.get_object()

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "mortgage": self.object,
        }

    def form_valid(self, form):
        mortgage = form.save()

        return HttpResponseRedirect(mortgage.get_absolute_url())


class MortgageDelete(LoginRequiredMixin, OwnerMixin, DeleteView):
    model = Mortgage
    success_url = reverse_lazy("mortgages:list")


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


class Speculate(LoginRequiredMixin, OwnerMixin, DetailView):
    model = Mortgage
    template_name_suffix = "_speculate"

    def get_context_data(self, **kwargs):
        ledger = Ledger(self.object)
        month_choices = ledger.month_choices
        form = forms.SpeculateForm(
            self.request.GET,
            month_choices=month_choices,
        )
        valid = form.is_valid()

        delta = None
        data = None
        no_money = False
        if valid:
            base_cost = ledger.calculate_cost()

            data = form.cleaned_data
            remaining = data['amount']
            month = data['month']
            while remaining > 0:
                overpayment = ledger.ledger[month].overpayment
                ledger.set_overpayment(
                    month,
                    Overpayment(amount=max(overpayment - remaining, 0)),
                )
                remaining -= overpayment
                month -= 1

                if month < 0:
                    no_money = True

                    break

            new_cost = ledger.calculate_cost()

            delta = base_cost - new_cost + data['amount']

        return {
            **super().get_context_data(**kwargs),
            "valid": valid,
            "form": form,
            "delta": delta,
            "data": data,
            "no_money": no_money,
            "month_names": dict(month_choices),
        }
