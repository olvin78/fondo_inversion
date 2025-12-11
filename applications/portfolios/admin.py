from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Portfolio, PortfolioItem

admin.site.register(Portfolio)
admin.site.register(PortfolioItem)
