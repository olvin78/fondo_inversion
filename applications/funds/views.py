from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from .models import FundTrade
from .forms import FundTradeForm
from decimal import Decimal
from applications.funds.models import (
    Fund,
    FundPosition,
    FundDiversification,
)
from applications.investors.models import Investor


@staff_member_required
def fund_list(request):
    funds = Fund.objects.all().order_by("name")
    return render(request, "funds/fund_list.html", {"funds": funds})


@staff_member_required
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


@staff_member_required
def transaction_list(request):
    transactions = FundTrade.objects.all().order_by("-created_at")
    return render(request, "funds/fundTrade_list.html", {"transactions": transactions})


@staff_member_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(FundTrade, pk=pk)
    return render(request, "funds/fundTrade_detail.html", {"transaction": transaction})


@staff_member_required
def transaction_create(request):
    product_id = request.GET.get("product")
    product = None
    if product_id:
        from applications.products.models import Product
        product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = FundTradeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("funds:transaction_list")
    else:
        # Pre-poblar el producto si se proporciona
        initial = {}
        if product:
            initial['product'] = product
        form = FundTradeForm(initial=initial)
    
    return render(request, "funds/fundTrade_form.html", {
        "form": form,
        "product": product
    })
