
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from .models import FundTrade
from decimal import Decimal
from applications.funds.models import (
    Fund,
    FundPosition,
    FundDiversification,
)
from applications.investors.models import Investor


def fund_list(request):
    funds = Fund.objects.all()
    return render(request, "funds/fund_list.html", {"funds": funds})








def fund_detail(request, pk):
    fund = get_object_or_404(Fund, pk=pk)

    # =========================
    # POSICIONES DEL FONDO
    # =========================
    positions_qs = (
        FundPosition.objects
        .filter(fund=fund)
        .select_related("product")
    )

    total_fund_value = Decimal("0")
    for p in positions_qs:
        total_fund_value += p.quantity * p.avg_price

    positions = []
    for p in positions_qs:
        position_value = p.quantity * p.avg_price

        weight = (
            (position_value / total_fund_value) * 100
            if total_fund_value > 0
            else Decimal("0")
        )

        positions.append({
            "product": p.product,
            "weight": round(weight, 2),
        })

    # =========================
    # HISTÓRICO DE NAV (CLAVE)
    # =========================
    nav_history = (
        fund.nav_history
        .all()
        .order_by("date")
    )

    # =========================
    # OTROS DATOS DEL FONDO
    # =========================
    buy_transactions = (
        FundTrade.objects
        .filter(
            fund=fund,
            transaction_type="BUY"
        )
        .select_related("product")
    )

    investors = fund.investors.count()

    diversification = (
        FundDiversification.objects
        .filter(is_active=True)
    )

    return render(
        request,
        "funds/fund_detail.html",
        {
            "fund": fund,
            "positions": positions,          # ← pesos (%)
            "nav_history": nav_history,      # ← gráfico NAV
            "buy_transactions": buy_transactions,
            "investors": investors,
            "diversification": diversification,
        }
    )


def fund_list(request):
    funds = Fund.objects.all().order_by("name")

    return render(request, "funds/fund_list.html", {
        "funds": funds
    })





def transaction_list(request):
    transactions = FundTrade.objects.all()
    return render(request, "funds/fundTrade_list.html", {"transactions": transactions})

def transaction_detail(request, pk):
    transaction = get_object_or_404(FundTrade, pk=pk)
    return render(request, "funds/fundTrade_detail.html", {"transaction": transaction})