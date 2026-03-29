from django.urls import path
from . import views
from .views import FundMapView

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("create/", views.product_create, name="create"),
    path("<int:pk>/", views.product_detail, name="detail"),
    path("<int:pk>/edit/", views.product_edit, name="edit"),
    path("<int:pk>/delete/", views.product_delete, name="delete"),
    path("quick-add/", views.product_quick_add, name="quick_add"),
]
