from django.urls import path
from . import views

app_name = "funds"

urlpatterns = [
    path("", views.fund_list, name="list"),
    path("create/", views.fund_create, name="create"),
    path("<int:pk>/", views.fund_detail, name="detail"),
    path("<int:pk>/evolution-data/", views.fund_evolution_data, name="evolution_data"),
    path("transaction", views.transaction_list, name="transaction_list"),
    path("transaction/create/", views.transaction_create, name="transaction_create"),
    path("transaction<int:pk>/", views.transaction_detail, name="transaction_detail"),
    path("crear-valor-diario/", views.crear_valor_diario, name="crear_valor_diario"),
]
