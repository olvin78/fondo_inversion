# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Investor

def investor_list(request):
    investors = Investor.objects.all()
    return render(request, "investors/investor_list.html", {"investors": investors})

def investor_detail(request, pk):
    investor = get_object_or_404(Investor, pk=pk)
    return render(request, "investors/investor_detail.html", {"investor": investor})
