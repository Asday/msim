from django import forms

from .models import Mortgage


class ActualPaymentSet(forms.Form):
    actual_payment = forms.DecimalField()

    def __init__(self, *args, model, mortgage, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.mortgage = mortgage

    def save(self):
        default = self.model.get_default(self.mortgage)
        if self.cleaned_data["actual_payment"] == default:
            self.model.objects.for_mortgage(self.mortgage).delete()

            return

        self.model.objects.update_or_create(
            mortgage=self.mortgage,
            defaults={"amount": self.cleaned_data["actual_payment"]},
        )


class AmountCreateUpdate(forms.Form):
    amount = forms.DecimalField()
    month = forms.IntegerField()
    mortgage = forms.ModelChoiceField(queryset=Mortgage.objects.all())

    def __init__(self, *args, model, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model

    def save(self):
        self.model.objects.update_or_create(
            mortgage=self.cleaned_data["mortgage"],
            month=self.cleaned_data["month"],
            defaults={"amount": self.cleaned_data["amount"]},
        )


class MortgageDuplicate(forms.Form):

    def __init__(self, *args, mortgage, **kwargs):
        super().__init__(*args, **kwargs)

        self.mortgage = mortgage

    def save(self):
        return self.mortgage.duplicate()


class SpeculateForm(forms.Form):
    amount = forms.DecimalField()
    month = forms.TypedChoiceField(coerce=int)

    def __init__(self, *args, month_choices, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["month"].choices = month_choices
