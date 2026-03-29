# Create your views here.
from django.shortcuts import render
from applications.funds.models import Fund, FundDiversification
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .models import MapElement, MapElementType
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


@method_decorator(staff_member_required, name="dispatch")
class FundMapView(TemplateView):
    template_name = "home/map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund = Fund.objects.first()
        positions = fund.positions.select_related("product") if fund else []
        map_elements = MapElement.objects.filter(
            is_active=True,
            show_in_map=True
        )

        context["fund"] = fund
        context["positions"] = positions
        context["map_elements"] = map_elements

        return context
