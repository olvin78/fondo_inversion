from decimal import Decimal, InvalidOperation
from core.utils.decimal import round4

from applications.ib.services.ib_client import get_ib_client


def _summary_value(summary, tag):
    for row in summary:
        if row.tag == tag and row.value not in ("", None):
            try:
                return round4(Decimal(row.value))
            except (InvalidOperation, TypeError):
                return Decimal("0.0000")
    return Decimal("0.0000")


def get_ibkr_account_summary():
    """
    Conecta con IBKR y devuelve un resumen de cuenta con valores Decimal.
    """
    ib = get_ib_client()

    try:
        ib.sleep(2)

        summary = None
        for _ in range(10):
            summary = ib.accountSummary()
            if summary:
                break
            ib.sleep(2)

        if not summary:
            raise TimeoutError("Account summary not received from IBKR")

        cash_balance = _summary_value(summary, "CashBalance")
        if cash_balance == Decimal("0.0000"):
            cash_balance = _summary_value(summary, "TotalCashValue")

        return {
            "net_liquidation": _summary_value(summary, "NetLiquidation"),
            "available_funds": _summary_value(summary, "AvailableFunds"),
            "cash_balance": cash_balance,
        }
    finally:
        ib.disconnect()


def get_ibkr_account_value():
    """
    Conecta con IBKR y devuelve el Net Liquidation Value (Decimal).
    """
    return get_ibkr_account_summary()["net_liquidation"]
