# applications/accounts/urls.py
from django.urls import path, include
from .views import register, dashboard_view, profile_view

app_name = "accounts"

urlpatterns = [
    path("dashboard/", dashboard_view, name="dashboard"),
    path("profile/", profile_view, name="profile"),
    path("register/", register, name="register"),
    path("", include("allauth.urls")),  # login/logout/signup/google
]
