from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import Product


@admin.register(Product)
class ProductAdmin(LeafletGeoAdmin):
    list_display = (
        "name",
        "asset_class",
        "country",
        "get_region",
    )

    search_fields = ("name", "ticker", "isin")

    list_filter = (
        "asset_class",
        "country__region",
    )

    def get_region(self, obj):
        return obj.country.region if obj.country else None

    get_region.short_description = "Region"
