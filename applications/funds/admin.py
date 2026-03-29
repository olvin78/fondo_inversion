from django.contrib import admin
from .models import (
    Fund,
    FundRiskLevel,
    FundNAV,
    FundDiversification,
    FundTrade,
    FundPosition,
    FundCapitalSnapshot,
)

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
        "participations",
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
    readonly_fields = (
        "participations",  # 🔒 no editable
        "nav_actual",
    )


# ============================
# ADMIN: Fund NAV (Histórico)
# ============================

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
        (Normalmente el NAV vendrá del snapshot de capital)
        """
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============================
# ADMIN: FundCapitalSnapshot (CLAVE)
# ============================

@admin.register(FundCapitalSnapshot)
class FundCapitalSnapshotAdmin(admin.ModelAdmin):

    list_display = (
        "fund",
        "date",
        "capital_interactive_broker",
        "capital_binance",
        "total_capital",
        "nav_participations",
        "participation_value",
    )

    list_filter = ("fund",)
    date_hierarchy = "date"
    ordering = ("-date",)

    readonly_fields = (
        "date",
        "nav_participations",
        "total_capital",
        "participation_value",
        "created_at",
    )

    fieldsets = (
        ("Fondo", {
            "fields": ("fund",)
        }),
        ("Capital por plataforma", {
            "fields": (
                "capital_interactive_broker",
                "capital_binance",
            )
        }),
        ("Cálculos automáticos", {
            "fields": (
                "nav_participations",
                "total_capital",
                "participation_value",
            )
        }),
        ("Auditoría", {
            "fields": (
                "date",
                "created_at",
            )
        }),
    )





# ============================
# ADMIN: FundDiversification
# ============================

@admin.register(FundDiversification)
class FundDiversificationAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "fund",
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

    search_fields = ("name",)

    ordering = ("order",)

    fieldsets = (
        (None, {
            "fields": (
                "fund",
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


# ============================
# ADMIN: FundTrade
# ============================

@admin.register(FundTrade)
class FundTradeAdmin(admin.ModelAdmin):

    list_display = (
        "fund",
        "product",
        "transaction_type",
        "quantity",
        "price",
        "total",
        "created_at",
    )

    list_filter = (
        "fund",
        "transaction_type",
        "product",
    )

    search_fields = (
        "fund__name",
        "product__name",
        "product__ticker",
        "product__isin",
    )

    autocomplete_fields = ("fund", "product")

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "fund",
                "product",
                "transaction_type",
            )
        }),
        ("Detalles de la operación", {
            "fields": (
                "quantity",
                "price",
            )
        }),
        ("Información automática", {
            "fields": (
                "created_at",
            )
        }),
    )

    # 🔒 BLOQUEO DE EDICIÓN DE TRADES HISTÓRICOS
    def has_change_permission(self, request, obj=None):
        return False

# ============================
# ADMIN: FundPosition (INVENTARIO)
# ============================

@admin.register(FundPosition)
class FundPositionAdmin(admin.ModelAdmin):
    list_display = (
        "fund",
        "product",
        "quantity",
        "avg_price",
        "current_value_display",
        "updated_at",
    )

    list_filter = (
        "fund",
        "product__asset_class",
    )

    search_fields = (
        "product__name",
        "product__ticker",
    )

    readonly_fields = (
        "fund",
        "product",
        "quantity",
        "avg_price",
        "updated_at",
    )

    def current_value_display(self, obj):
        val = obj.current_value()
        return f"€ {val:,.2f}"
    
    current_value_display.short_description = "Valor Actual"

    def has_add_permission(self, request):
        return False # 🔒 solo via trades

