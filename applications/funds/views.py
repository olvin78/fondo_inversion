from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Fund

def fund_list(request):
    funds = Fund.objects.all()
    return render(request, "funds/fund_list.html", {"funds": funds})

def fund_detail(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    return render(request, "funds/fund_detail.html", {"fund": fund})
