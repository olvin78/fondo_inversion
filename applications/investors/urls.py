from django.urls import path
from . import views

app_name = "investors"

urlpatterns = [
    path("", views.investor_list, name="investor_list"),
    path("invest/", views.invest, name="invest"),
    path("<int:pk>/", views.investor_detail, name="investor_detail"),
]
