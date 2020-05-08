from django.urls import path

from .views import (
    ActualInitialPaymentSet,
    ActualThereafterPaymentSet,
    DiscrepancyDelete,
    DiscrepancyCreateUpdate,
    MortgageCreate,
    MortgageDelete,
    MortgageDetail,
    MortgageDuplicate,
    MortgageList,
    OverpaymentDelete,
    OverpaymentCreateUpdate,
)


app_name = "mortgages"
urlpatterns = [
    path("", MortgageList.as_view(), name="list"),
    path("create/", MortgageCreate.as_view(), name="create"),
    path("<int:pk>/", MortgageDetail.as_view(), name="detail"),
    path(
        "<int:pk>/set_initial/",
        ActualInitialPaymentSet.as_view(),
        name="actualinitialpayment.set",
    ),
    path(
        "<int:pk>/set_thereafter/",
        ActualThereafterPaymentSet.as_view(),
        name="actualthereafterpayment.set",
    ),
    path("<int:pk>/duplicate/", MortgageDuplicate.as_view(), name="duplicate"),
    path("<int:pk>/delete/", MortgageDelete.as_view(), name="delete"),
    path(
        "<int:pk>/overpayments/",
        OverpaymentCreateUpdate.as_view(),
        name="overpayment.create_update",
    ),
    path(
        "overpayments/<int:pk>/delete/",
        OverpaymentDelete.as_view(),
        name="overpayment.delete",
    ),
    path(
        "<int:pk>/discrepancies/",
        DiscrepancyCreateUpdate.as_view(),
        name="discrepancy.create_update",
    ),
    path(
        "discrepancies/<int:pk>/delete/",
        DiscrepancyDelete.as_view(),
        name="discrepancy.delete",
    ),
]
