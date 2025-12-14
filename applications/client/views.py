from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from applications.investors.models import Investor, InvestorFund
from applications.transactions.models import InvestorTransaction
from applications.funds.models import Fund


from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from applications.funds.models import Fund
from applications.transactions.models import Transaction


@login_required
def dashboard(request):
    funds = Fund.objects.all()

    fondocapital = Fund.objects.first()
    nav_actual = fondocapital.nav_actual if fondocapital else Decimal("0")

    nav = Decimal("0")
    capital_del_usuario = Decimal("0")

    inversor = getattr(request.user, "investor_profile", None)
    if inversor:
        position = inversor.get_first_fund_position()  # InvestorFund o None
        if position:
            nav = position.participations  # Decimal
            capital_del_usuario = nav_actual * nav  # Decimal × Decimal

    transactions = Transaction.objects.all()

    return render(request, "client/dashboard.html", {
        "funds": funds,
        "nav": nav,
        "nav_actual": nav_actual,
        "capital_del_usuario": capital_del_usuario,
        "transactions":transactions,
    })





@login_required
def invest(request):
    fund = Fund.objects.first()

    return render(request, "client/invest.html", {
        "fund": fund,
    })
