from django.urls import path
from . import views

app_name = "investors"

urlpatterns = [
    path("", views.investor_list, name="list"),
    path("<int:pk>/", views.investor_detail, name="detail"),
]
