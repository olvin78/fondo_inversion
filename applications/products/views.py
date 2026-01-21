from django.shortcuts import render, get_object_or_404
from .models import Product
from django.views.generic import TemplateView
from applications.funds.models import Fund

def product_list(request):
    products = Product.objects.all()
    return render(request, "products/product_list.html", {"products": products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "products/product_detail.html", {"product": product})

class FundMapView(TemplateView):
    template_name = ("home/map.html")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fund = Fund.objects.first()  # Fondo único
        positions = fund.positions.select_related("product") if fund else []

        context["fund"] = fund
        context["positions"] = positions

        return context
