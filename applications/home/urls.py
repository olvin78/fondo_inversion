from django.urls import path
from . import views
from .views import SimuladorRentabilidadView

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("simulador/", SimuladorRentabilidadView.as_view(),name="simulador_rentabilidad"),
]
