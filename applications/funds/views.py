from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Fund
from applications.transactions.models import Transaction

def fund_list(request):
    funds = Fund.objects.all()
    return render(request, "funds/fund_list.html", {"funds": funds})

def fund_detail(request, pk):
    fund = get_object_or_404(Fund, pk=pk)

    buy_transactions = Transaction.objects.filter(
        transaction_type="BUY"
    ).select_related("product")

    return render(request, "funds/fund_detail.html", {
        "fund": fund,
        "buy_transactions": buy_transactions,
    })

def fund_list(request):
    funds = Fund.objects.all().order_by("name")

    return render(request, "funds/fund_list.html", {
        "funds": funds
    })