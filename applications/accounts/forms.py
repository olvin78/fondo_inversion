from django import forms
from django.contrib.auth import get_user_model

from applications.investors.models import Investor


User = get_user_model()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class InvestorProfileForm(forms.ModelForm):
    class Meta:
        model = Investor
        fields = [
            "document_id",
            "phone",
            "birth_date",
            "address",
            "city",
            "postal_code",
            "country",
            "risk_level",
        ]
        widgets = {
            "document_id": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "birth_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "risk_level": forms.Select(attrs={"class": "form-select"}),
        }
