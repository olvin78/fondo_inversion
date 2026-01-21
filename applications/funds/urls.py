from django.urls import path
from . import views

app_name = "funds"

urlpatterns = [
    path("", views.fund_list, name="list"),
    path("<int:pk>/", views.fund_detail, name="detail"),
    path("transaction", views.transaction_list, name="transaction_list"),
    path("transaction<int:pk>/", views.transaction_detail, name="transaction_detail"),
]
