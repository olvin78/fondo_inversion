from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Home
    path("", include("applications.home.urls")),

    # Allauth (usa los templates de allauth-ui)
    path("accounts/", include("allauth.urls")),

    # Tus URLs de cuentas (dashboard, etc.)
    path("accounts/", include("applications.accounts.urls")),

    # Investors
    path("investors/", include("applications.investors.urls")),

    # Products
    path("products/", include("applications.products.urls")),

    # Portfolios
    path("portfolios/", include("applications.portfolios.urls")),

    # Transactions
    path("transactions/", include("applications.transactions.urls")),

    # Funds
    path("funds/", include("applications.funds.urls")),
]
