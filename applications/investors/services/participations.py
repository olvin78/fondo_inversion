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

    # 1. Cálculo de comisión (1%) y Neto Inversor (99%)
    fee_amount = amount * Decimal("0.01")
    net_investor_amount = amount - fee_amount
    
    # Participaciones para el inversor
    investor_participations = net_investor_amount / nav_price

    # 2. Transacción del Inversor (Neto)
    tx = InvestorFundTransaction.objects.create(
        investor=investor,
        fund=fund,
        transaction_type=BUY,
        participations=investor_participations,
        nav_price=nav_price,
        amount=net_investor_amount,
        reference=f"Compra neta (99%) - Comisión 1% descontada. Gestor: {executed_by}" if executed_by else "",
    )

    # 4. ABONO DE COMISIÓN AL GESTOR (admin)
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user = User.objects.get(username="admin")
        from applications.investors.models import Investor as InvestorProfile
        gestor_profile, _ = InvestorProfile.objects.get_or_create(user=admin_user)
        
        # El gestor recibe su 1% en forma de participaciones en el mismo fondo
        gestor_parts = fee_amount / nav_price
        
        # Transacción del Gestor (Comisión)
        InvestorFundTransaction.objects.create(
            investor=gestor_profile,
            fund=fund,
            transaction_type=BUY,
            participations=gestor_parts,
            nav_price=nav_price,
            amount=fee_amount,
            reference=f"Comisión 1% de la transacción de {investor.user.username}",
        )
    except Exception:
        # Silenciamos errores de comisión para no bloquear la transacción principal
        pass

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

    return tx
