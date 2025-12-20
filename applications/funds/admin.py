from django.contrib import admin
from .models import Fund, FundRiskLevel, FundNAV, FundDiversification


# ============================
# ADMIN: FundRiskLevel
# ============================

@admin.register(FundRiskLevel)
class FundRiskLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "level")
    ordering = ("level",)
    search_fields = ("name",)


# ============================
# ADMIN: Fund
# ============================

@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "currency",
        "nav_actual",
        "risk_level",
        "is_open",
        "created_at",
    )

    list_filter = (
        "currency",
        "risk_level",
        "is_open",
    )

    search_fields = (
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }






@admin.register(FundNAV)
class FundNAVAdmin(admin.ModelAdmin):
    list_display = (
        "fund",
        "date",
        "nav_value",
        "created_at",
        "created_by",
    )

    list_filter = (
        "fund",
        "date",
    )

    search_fields = (
        "fund__name",
    )

    ordering = ("-date",)

    readonly_fields = (
        "created_at",
        "created_by",
    )

    fields = (
        "fund",
        "date",
        "nav_value",
        "created_at",
        "created_by",
    )

    def save_model(self, request, obj, form, change):
        """
        Asignar automáticamente el usuario que registra el NAV.
        """
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.register(FundDiversification)
    class FundDiversificationAdmin(admin.ModelAdmin):
        list_display = (
            "name",
            "product_type",
            "percentage",
            "color_preview",
            "is_active",
            "order",
        )

        list_editable = (
            "percentage",
            "order",
            "is_active",
        )

        list_filter = (
            "product_type",
            "is_active",
        )

        search_fields = (
            "name",
        )

        ordering = ("order",)

        fieldsets = (
            (None, {
                "fields": (
                    "name",
                    "product_type",
                    "percentage",
                )
            }),
            ("Visualización", {
                "fields": (
                    "color",
                    "order",
                    "is_active",
                )
            }),
        )

        def color_preview(self, obj):
            return f"⬤ {obj.color}"

        color_preview.short_description = "Color"


