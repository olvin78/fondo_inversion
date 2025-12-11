from django.shortcuts import render

# Create your views here.
from applications.funds.models import Fund

def index(request):
    fund = Fund.objects.first()
    return render(request, "home/index.html", {
        "fund": fund,
        "products": fund.products.all() if fund else [],
    })
