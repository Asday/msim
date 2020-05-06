from django.contrib.admin import site

from .models import (
    ActualInitialPayment,
    ActualThereafterPayment,
    Discrepancy,
    Mortgage,
    Overpayment,
)


site.register(ActualInitialPayment)
site.register(ActualThereafterPayment)
site.register(Discrepancy)
site.register(Mortgage)
site.register(Overpayment)
