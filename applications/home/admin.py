from django.contrib import admin
from .models import MapElement, MapElementType
from leaflet.admin import LeafletGeoAdmin






@admin.register(MapElementType)
class MapElementTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "is_active",
    )

    search_fields = ("name", "code")
    list_filter = ("is_active",)

    fields = (
        "name",
        "code",
        "icon",
        "description",
        "is_active",
    )

@admin.register(MapElement)
class MapElementAdmin(LeafletGeoAdmin):
    list_display = (
        "name",
        "code",
        "element_type",
        "country",
        "show_in_map",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "element_type",
        "country",
        "show_in_map",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Información principal", {
            "fields": (
                "name",
                "code",
                "element_type",
                "country",
            )
        }),
        ("Ubicación", {
            "fields": ("location",)
        }),
        ("Visibilidad", {
            "fields": (
                "show_in_map",
                "is_active",
            )
        }),
        ("Descripción", {
            "fields": ("description",)
        }),
        ("Auditoría", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
