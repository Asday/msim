from django import forms

from .models import Mortgage


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
