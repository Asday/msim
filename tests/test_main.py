from decimal import Decimal

from mortgages.models import LedgerEntry
from mortgages.utils import payment


def test_server_starts(client):
    assert client.get('/spurious-url').status_code == 404


def test_payment():
    assert payment(0.0184 / 12, 180, 156000) == 992.42


def test_ledgerentry_normalise():
    entry = LedgerEntry(
        month_number=0,
        mortgage_pk=1,
        year=2020,
        month=5,
        opening_balance=Decimal("-1931.99"),
        interest=Decimal("-5.70"),
        payment=Decimal("1118.28"),
        overpayment=Decimal("1414.33"),
        discrepancy=0,
    )

    entry.normalise()

    assert 0 <= entry.overpayment
