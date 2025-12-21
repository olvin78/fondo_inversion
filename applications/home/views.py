# Create your views here.
from django.shortcuts import render
from applications.funds.models import Fund, FundDiversification
def index(request):
    fund = Fund.objects.all()


def index(request):
    fund = Fund.objects.first()
    diversification = FundDiversification.objects.filter(is_active=True)
    return render(request, "home/index.html", {
        "fund": fund,
        "diversification": diversification
    })
