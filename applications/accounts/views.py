from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm


# Registro manual SI QUIERES uno adicional aparte de allauth
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("account_login")  # login de allauth
    else:
        form = UserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


# Dashboard personalizado
@login_required
def dashboard_view(request):
    return render(request, "accounts/dashboard.html")
