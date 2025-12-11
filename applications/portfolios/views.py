from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Portfolio

def portfolio_list(request):
    portfolios = Portfolio.objects.all()
    return render(request, "portfolios/portfolio_list.html", {"portfolios": portfolios})

def portfolio_detail(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk)
    return render(request, "portfolios/portfolio_detail.html", {"portfolio": portfolio})
