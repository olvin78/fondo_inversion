from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "ticker", "isin", "asset_class", "currency",
            "country", "sector", "industry", "strategy",
            "description", "is_active", "show_in_map"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control rounded-3 p-3", "placeholder": "Ej: Apple Inc."}),
            "ticker": forms.TextInput(attrs={"class": "form-control rounded-3 p-3", "placeholder": "Ej: AAPL"}),
            "isin": forms.TextInput(attrs={"class": "form-control rounded-3 p-3", "placeholder": "Ej: US0378331005"}),
            "asset_class": forms.Select(attrs={"class": "form-select rounded-3 p-3"}),
            "currency": forms.Select(attrs={"class": "form-select rounded-3 p-3"}),
            "country": forms.Select(attrs={"class": "form-select rounded-3 p-3"}),
            "sector": forms.Select(attrs={"class": "form-select rounded-3 p-3"}),
            "industry": forms.Select(attrs={"class": "form-select rounded-3 p-3"}),
            "strategy": forms.Select(attrs={"class": "form-select rounded-3 p-3"}),
            "description": forms.Textarea(attrs={"class": "form-control rounded-3 p-3", "rows": 3, "placeholder": "Descripción del activo..."}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_in_map": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name": "Nombre del Activo",
            "ticker": "Símbolo (Ticker)",
            "isin": "Código ISIN",
            "asset_class": "Clase de Activo",
            "currency": "Moneda Base",
            "country": "Pais de Origen",
            "sector": "Sector Económico",
            "industry": "Industria Específica",
            "strategy": "Estrategia de Inversión",
            "is_active": "Activo Habilitado",
            "show_in_map": "Mostrar en Mapa de Calor",
        }
