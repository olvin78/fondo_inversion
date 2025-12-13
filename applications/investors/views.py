# Create your views here.
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Investor, InvestorFund
from applications.funds.models import Fund
from applications.transactions.models import InvestorTransaction


# -------------------------------------------------
# LISTA DE INVERSORES
# -------------------------------------------------
def investor_list(request):
    investors = Investor.objects.all()
    return render(request, "investors/investor_list.html", {
        "investors": investors
    })


# -------------------------------------------------
# DETALLE DE INVERSOR
# -------------------------------------------------
def investor_detail(request, pk):
    investor = get_object_or_404(Investor, pk=pk)
    positions = investor.fund_positions.select_related("fund")

    return render(request, "investors/investor_detail.html", {
        "investor": investor,
        "positions": positions,
    })


# -------------------------------------------------
# INVERTIR (VERSIÓN SIMPLE, SIN BLOQUEOS)
# -------------------------------------------------
@login_required
def invest(request):
    """
    Versión temporal:
    - NO falla si no hay Investor
    - NO falla si no hay Fund
    - Solo muestra la página para poder trabajar el frontend
    """

    fund = Fund.objects.first()

    # Fondo DEMO si no existe ninguno
    if not fund:
        fund = {
            "name": "Fondo Demo",
            "participation_value": "100.00",
        }

    # Si es POST, por ahora NO hacemos nada real
    if request.method == "POST":
        return redirect("investors:invest")

    return render(request, "investors/invest.html", {
        "fund": fund,
    })
