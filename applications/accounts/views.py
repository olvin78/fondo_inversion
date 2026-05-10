from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

from .forms import UserProfileForm, InvestorProfileForm


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


@login_required
def profile_view(request):
    user = request.user
    investor = getattr(user, "investor_profile", None)

    if request.method == "POST":
        user_form = UserProfileForm(request.POST, instance=user)
        investor_form = InvestorProfileForm(request.POST, instance=investor, user=user) if investor else None

        if user_form.is_valid() and (investor_form is None or investor_form.is_valid()):
            user_form.save()
            if investor_form is not None:
                investor_form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("accounts:profile")
    else:
        user_form = UserProfileForm(instance=user)
        investor_form = InvestorProfileForm(instance=investor, user=user) if investor else None

    return render(
        request,
        "accounts/profile.html",
        {
            "user_form": user_form,
            "investor_form": investor_form,
            "investor": investor,
        },
    )
