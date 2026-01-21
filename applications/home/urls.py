from django.urls import path
from . import views
from .views import SimuladorRentabilidadView, FundMapView

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("map/", FundMapView.as_view(), name="map"),
    path("simulador/", SimuladorRentabilidadView.as_view(),name="simulador_rentabilidad"),
]
