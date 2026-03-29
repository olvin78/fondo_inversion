from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

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
    path("hijack/", include("hijack.urls")),

    # Products
    path("products/", include("applications.products.urls")),

    # Funds
    path("funds/", include("applications.funds.urls")),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
