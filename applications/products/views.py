from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import json
from .models import Product, Sector, Industry, Strategy, AssetClass, Currency, Country, Region
from .forms import ProductForm
from django.views.generic import TemplateView
from applications.funds.models import Fund
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def product_list(request):
    products = Product.objects.all()
    return render(request, "products/product_list.html", {"products": products})

@staff_member_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("products:list")
    else:
        form = ProductForm()
    
    regions = Region.objects.all()
    return render(request, "products/product_form.html", {"form": form, "edit_mode": False, "regions": regions})

@staff_member_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "products/product_detail.html", {"product": product})

@staff_member_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("products:list")
    else:
        form = ProductForm(instance=product)
    
    regions = Region.objects.all()
    return render(request, "products/product_form.html", {"form": form, "edit_mode": True, "product": product, "regions": regions})

@staff_member_required
def product_quick_add(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            type_ = data.get("type")
            name = data.get("name")
            code = data.get("code")

            if type_ == "sector":
                obj = Sector.objects.create(name=name, code=code)
            elif type_ == "industry":
                sector_id = data.get("sector_id")
                sector = Sector.objects.get(id=sector_id)
                obj = Industry.objects.create(name=name, code=code, sector=sector)
            elif type_ == "strategy":
                obj = Strategy.objects.create(name=name, code=code)
            elif type_ == "asset_class":
                obj = AssetClass.objects.create(name=name, code=code)
            elif type_ == "currency":
                symbol = data.get("symbol")
                obj = Currency.objects.create(name=name, code=code, symbol=symbol)
            elif type_ == "country":
                iso_code = data.get("iso_code")
                region_id = data.get("region_id")
                region = Region.objects.get(id=region_id)
                obj = Country.objects.create(name=name, iso_code=iso_code, region=region)
            else:
                return JsonResponse({"success": False, "error": "Tipo no válido"})

            return JsonResponse({"success": True, "id": obj.id, "name": str(obj)})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"})

@staff_member_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        return redirect("products:list")
    return redirect("products:detail", pk=pk)

class FundMapView(TemplateView):
    template_name = ("home/map.html")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['products'] = Product.objects.all()
        return context
