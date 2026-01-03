from decimal import Decimal
from applications.ib.models import IBSnapshot, IBPosition


def val(summary, tag):
    for row in summary:
        if row.tag == tag and row.value not in ("", None):
            return Decimal(row.value)
    return Decimal("0")


def sync_ib_snapshot():
    from applications.ib.services.ib_client import get_ib_client

    ib = get_ib_client()

    try:
        # Esperar a que IB esté listo
        ib.sleep(2)

        summary = None
        for _ in range(10):  # hasta ~20 segundos
            summary = ib.accountSummary()
            if summary:
                break
            ib.sleep(2)

        if not summary:
            raise TimeoutError("Account summary not received")

        account = next(
            (row.account for row in summary if row.account and row.account != "All"),
            None
        )

        snapshot = IBSnapshot.objects.create(
            account=account,
            net_liquidation=val(summary, "NetLiquidation"),
            cash=val(summary, "AvailableFunds"),
            equity=val(summary, "GrossPositionValue"),
            margin_used=val(summary, "InitMarginReq"),
        )

        for p in ib.positions():
            IBPosition.objects.create(
                snapshot=snapshot,
                symbol=p.contract.symbol,
                exchange=p.contract.exchange or "",
                currency=p.contract.currency,
                quantity=Decimal(p.position),
                avg_price=Decimal(p.avgCost),
                market_price=Decimal(p.marketPrice),
                market_value=Decimal(p.marketValue),
                unrealized_pnl=Decimal(p.unrealizedPNL),
                realized_pnl=Decimal(p.realizedPNL),
            )

    finally:
        ib.disconnect()
