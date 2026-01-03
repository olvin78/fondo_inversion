from django.urls import path
from . import views
from applications.investors.views import buy_participations_view, sell_participations_view

app_name = "investors"

urlpatterns = [
    path("", views.investor_list, name="investor_list"),
    path("invest/", views.invest, name="invest"),
    path("<int:pk>/", views.investor_detail, name="investor_detail"),
    path("buy/", buy_participations_view, name="buy_participations"),
    path("sell/", sell_participations_view, name="sell_participations"),
]
