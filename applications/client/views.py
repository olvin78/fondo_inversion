from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from applications.investors.models import Investor, InvestorFund
from applications.transactions.models import InvestorTransaction
from applications.funds.models import Fund


@login_required
def dashboard(request):
    capital_invertido = Decimal("0")
    fund = None
    fund_position = 45

    return render(request, "client/dashboard.html", {
        "capital_invertido": capital_invertido,
        "fund": fund,
        "fund_position": fund_position,
    })




@login_required
def invest(request):
    fund = Fund.objects.first()

    return render(request, "client/invest.html", {
        "fund": fund,
    })
