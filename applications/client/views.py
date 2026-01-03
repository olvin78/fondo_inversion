from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from applications.investors.models import Investor
from applications.transactions.models import InvestorTransaction

from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from applications.ib.models import IBSnapshot
from applications.funds.models import Fund
from applications.investors.models import InvestorFund
from applications.transactions.models import Transaction



@login_required
def dashboard(request):
    fund = Fund.objects.first()
    funds = Fund.objects.all()

    # -----------------------------
    # 1. Último snapshot de IB
    # -----------------------------
    ib_snapshot = IBSnapshot.objects.order_by("-created_at").first()
    net_liquidation = ib_snapshot.net_liquidation if ib_snapshot else Decimal("0")

    # -----------------------------
    # 2. Total participaciones fondo
    # -----------------------------
    total_participations = fund.total_participations() if fund else Decimal("0")

    # -----------------------------
    # 3. NAV actual (real)
    # -----------------------------
    nav_actual = Decimal("0")
    if total_participations > 0:
        nav_actual = net_liquidation / total_participations

    # -----------------------------
    # 4. Usuario (participaciones reales)
    # -----------------------------
    nav_usuario = Decimal("0")
    capital_del_usuario = Decimal("0")
    position = None

    inversor = getattr(request.user, "investor_profile", None)
    if inversor and fund:
        position = (
            InvestorFund.objects
            .filter(investor=inversor, fund=fund)
            .first()
        )

        if position:
            nav_usuario = position.participations
            capital_del_usuario = nav_usuario * nav_actual

    # -----------------------------
    # 5. Limpieza visual
    # -----------------------------
    capital_del_usuario = capital_del_usuario.quantize(Decimal("0.01"))
    nav_actual = nav_actual.quantize(Decimal("0.0001"))

    transactions = Transaction.objects.all()

    return render(request, "client/dashboard.html", {
        "funds": funds,
        "fund": fund,
        "position": position,
        "nav_usuario": nav_usuario,
        "nav_actual": nav_actual,
        "capital_del_usuario": capital_del_usuario,
        "net_liquidation": net_liquidation,
        "transactions": transactions,
    })



@login_required
def invest(request):
    fund = Fund.objects.first()

    return render(request, "client/invest.html", {
        "fund": fund,
    })
