from django import forms
from .models import FundTrade, Fund
from applications.products.models import Product

class FundTradeForm(forms.ModelForm):
    class Meta:
        model = FundTrade
        fields = ["fund", "product", "transaction_type", "quantity", "price"]
        widgets = {
            "fund": forms.Select(attrs={"class": "form-select rounded-3 shadow-sm border-0 bg-light-subtle p-3"}),
            "product": forms.Select(attrs={"class": "form-select rounded-3 shadow-sm border-0 bg-light-subtle p-3"}),
            "transaction_type": forms.Select(attrs={"class": "form-select rounded-3 shadow-sm border-0 bg-light-subtle p-3"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control rounded-3 shadow-sm border-0 bg-light-subtle p-3", "placeholder": "Ej: 10.5"}),
            "price": forms.NumberInput(attrs={"class": "form-control rounded-3 shadow-sm border-0 bg-light-subtle p-3", "placeholder": "Ej: 145.20"}),
        }
        labels = {
            "fund": "Fondo de Inversión",
            "product": "Activo / Instrumento",
            "transaction_type": "Tipo de Operación",
            "quantity": "Cantidad (Unidades)",
            "price": "Precio de Ejecución (Unitario)",
        }
