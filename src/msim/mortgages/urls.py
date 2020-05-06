from django.urls import path

from .views import (
    DiscrepancyDelete,
    DiscrepancyCreateUpdate,
    MortgageDetail,
    MortgageList,
    OverpaymentDelete,
    OverpaymentCreateUpdate,
)


app_name = "mortgages"
urlpatterns = [
    path("", MortgageList.as_view(), name="list"),
    path("<int:pk>", MortgageDetail.as_view(), name="detail"),
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
