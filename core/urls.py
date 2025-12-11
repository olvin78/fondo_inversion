from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Home
    path("", include("applications.home.urls")),

    # Tus URLs de cuentas
    path("accounts/", include("applications.accounts.urls")),

    # ALLAUTH (Login con Google se activa aquí)
    path("accounts/", include("allauth.urls")),

    # Investors
    path("investors/", include("applications.investors.urls")),

    # Products
    path("products/", include("applications.products.urls")),

    # Portfolios
    path("portfolios/", include("applications.portfolios.urls")),

    # Transactions
    path("transactions/", include("applications.transactions.urls")),

    # Founds
    path("funds/", include("applications.funds.urls")),

]
