from decimal import Decimal
from django.db import transaction
from applications.investors.models import (
    InvestorFund,
    InvestorFundTransaction,
)

BUY = "BUY"
SELL = "SELL"


@transaction.atomic
def buy_participations(*, investor, fund, amount, nav_price, executed_by=None):
    """
    Compra de participaciones (importe en €)
    """
    amount = Decimal(amount)
    nav_price = Decimal(nav_price)

    participations = amount / nav_price

    # 1. Crear transacción (histórico)
    tx = InvestorFundTransaction.objects.create(
        investor=investor,
        fund=fund,
        transaction_type=BUY,
        participations=participations,
        nav_price=nav_price,
        amount=amount,
        reference=f"Compra ejecutada por {executed_by}" if executed_by else "",
    )

    # 2. Obtener o crear posición actual
    position, _ = InvestorFund.objects.get_or_create(
        investor=investor,
        fund=fund,
        defaults={"participations": 0, "average_price": 0},
    )

    # 3. Recalcular precio medio
    total_cost = (
        position.participations * position.average_price
        + amount
    )
    total_parts = position.participations + participations

    position.participations = total_parts
    position.average_price = total_cost / total_parts
    position.save()

    return tx


@transaction.atomic
def sell_participations(*, investor, fund, participations, nav_price, executed_by=None):
    """
    Venta de participaciones
    """
    participations = Decimal(participations)
    nav_price = Decimal(nav_price)

    position = InvestorFund.objects.select_for_update().get(
        investor=investor,
        fund=fund,
    )

    if participations > position.participations:
        raise ValueError("No se pueden vender más participaciones de las que se tienen")

    amount = participations * nav_price

    tx = InvestorFundTransaction.objects.create(
        investor=investor,
        fund=fund,
        transaction_type=SELL,
        participations=participations,
        nav_price=nav_price,
        amount=amount,
        reference=f"Venta ejecutada por {executed_by}" if executed_by else "",
    )

    position.participations -= participations
    position.save()

    return tx
