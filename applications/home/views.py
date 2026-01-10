# Create your views here.
from django.shortcuts import render
from applications.funds.models import Fund, FundDiversification
from django.views.generic import TemplateView
def index(request):
    fund = Fund.objects.all()


def index(request):
    fund1 = Fund.objects.filter(id=1)
    diversification1 = FundDiversification.objects.filter(is_active=True, fund=1)
    return render(request, "home/index.html", {
        "fund1": fund1,
        "diversification1": diversification1
    })

class SimuladorRentabilidadView(TemplateView):
    template_name = "home/simulador-rentabilidad.html"