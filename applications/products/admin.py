from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

from .models import (
    Currency,
    Strategy,
    Sector,
    Industry,
    Region,
    MarketType,
    Country,
    AssetClass,
    Product,
    ProductPrice,
)

# =========================
# CATÁLOGOS BÁSICOS
# =========================

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(AssetClass)
class AssetClassAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("sector", "code", "name")
    list_filter = ("sector",)
    search_fields = ("code", "name")
    ordering = ("sector", "code")


# =========================
# GEOGRAFÍA / MERCADOS
# =========================

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(MarketType)
class MarketTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(Country)
class CountryAdmin(LeafletGeoAdmin):
    list_display = (
        "name",
        "iso_code",
        "region",
        "market_type",
        "currency",
        "risk_rating",
        "is_active",
    )

    list_filter = (
        "region",
        "market_type",
        "is_active",
    )

    search_fields = (
        "name",
        "iso_code",
    )

    ordering = ("name",)


# =========================
# PRODUCTOS
# =========================

@admin.register(Product)
class ProductAdmin(LeafletGeoAdmin):
    list_display = (
        "name",
        "asset_class",
        "country",
        "sector",
        "strategy",
        "currency",
        "is_active",
    )

    list_filter = (
        "asset_class",
        "country__region",
        "sector",
        "strategy",
        "is_active",
    )

    search_fields = (
        "name",
        "ticker",
        "isin",
    )

    ordering = ("name",)


# =========================
# HISTÓRICO DE PRECIOS
# =========================

@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = ("product", "price", "date")
    list_filter = ("date",)
    search_fields = ("product__name", "product__ticker")

    ordering = ("-date",)

    # 🔒 Normalmente no se editan precios históricos
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
