
from django.shortcuts import render, get_object_or_404
from .models import Fund, FundDiversification
from applications.investors.models import Investor
from django.views.generic import TemplateView
from .models import FundTrade

def fund_list(request):
    funds = Fund.objects.all()
    return render(request, "funds/fund_list.html", {"funds": funds})

def fund_detail(request, pk):
    fund = get_object_or_404(Fund, pk=pk)

    buy_transactions = FundTrade.objects.filter(
        transaction_type="BUY"
    ).select_related("product")

    nav_history = fund.nav_history.order_by("date")
    investors = Investor.objects.all().count()
    diversification = FundDiversification.objects.filter(is_active=True)

    return render(request, "funds/fund_detail.html", {
        "fund": fund,
        "buy_transactions": buy_transactions,
        "nav_history": nav_history,
        "investors": investors,
        "diversification": diversification
    })

def fund_list(request):
    funds = Fund.objects.all().order_by("name")

    return render(request, "funds/fund_list.html", {
        "funds": funds
    })

class FundMapView(TemplateView):
    template_name = "funds/fund_map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fund = Fund.objects.first()
        positions = fund.positions.select_related("product") if fund else []

        context["fund"] = fund
        context["positions"] = positions
        return context



def transaction_list(request):
    transactions = FundTrade.objects.all()
    return render(request, "funds/fundTrade_list.html", {"transactions": transactions})

def transaction_detail(request, pk):
    transaction = get_object_or_404(FundTrade, pk=pk)
    return render(request, "funds/fundTrade_detail.html", {"transaction": transaction})