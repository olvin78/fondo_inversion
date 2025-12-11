from django.urls import path
from . import views

app_name = "funds"

urlpatterns = [
    path("", views.fund_list, name="list"),
    path("<int:pk>/", views.fund_detail, name="detail"),
]
