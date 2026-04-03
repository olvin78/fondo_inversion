from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from .models import (
    Fund,
    FundRiskLevel,
    FundDiversification,
    FundTrade,
    FundPosition,
    ValorDiarioFondo,
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
        "current_nav_display",
        "participations_stored",
        "participations_calculated",
        "sync_status",
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
        "participations_stored",
        "participations_calculated",
        "diff_participations",
        "sync_status_msg",
        "current_nav_display",
    )

    def participations_stored(self, obj):
        return obj.participations
    participations_stored.short_description = "Part. Almacenadas (Campo DB)"

    def participations_calculated(self, obj):
        return obj.total_participations
    participations_calculated.short_description = "Part. Reales (Calculadas)"

    def diff_participations(self, obj):
        diff = obj.participations - obj.total_participations
        return f"{diff:,.4f}"
    diff_participations.short_description = "Diferencia"

    def sync_status(self, obj):
        diff = obj.participations - obj.total_participations
        if abs(diff) > Decimal("0.000001"):
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠️ ERROR SYNC</span>')
        return format_html('<span style="color: #10b981; font-weight: bold;">✅ OK</span>')
    sync_status.short_description = "Sincronización"

    def sync_status_msg(self, obj):
        diff = obj.participations - obj.total_participations
        if abs(diff) > Decimal("0.000001"):
            return format_html(
                '<div style="background: #fee2e2; border: 1px solid #ef4444; color: #b91c1c; padding: 10px; border-radius: 8px; font-weight: bold;">'
                '⚠️ Las participaciones del fondo no están sincronizadas. Se recomienda recalcular.'
                '</div>'
            )
        return "Sincronización correcta."
    sync_status_msg.short_description = "Aviso de Sincronización"

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "slug",
                "description",
                "manager",
                "currency",
            )
        }),
        ("Participaciones y Sincronización", {
            "fields": (
                "sync_status_msg",
                "participations_stored",
                "participations_calculated",
                "diff_participations",
            )
        }),
        ("Finanzas y Riesgo", {
            "fields": (
                "current_nav_display",
                "risk_level",
                "is_open",
            )
        }),
    )

    def current_nav_display(self, obj):
        return f"{obj.current_nav():,.4f}"
    current_nav_display.short_description = "NAV actual"


# ============================
# ADMIN: ValorDiarioFondo (CLAVE)
# ============================

@admin.register(ValorDiarioFondo)
class ValorDiarioFondoAdmin(admin.ModelAdmin):

    list_display = (
        "fund",
        "fecha",
        "capital_interactive_broker",
        "capital_binance",
        "valor_total",
        "participaciones",
        "nav",
        "creado_en",
        "creado_por",
    )

    list_filter = ("fund",)
    date_hierarchy = "fecha"
    ordering = ("-fecha",)

    readonly_fields = (
        "valor_total",
        "participaciones",
        "nav",
        "creado_en",
        "creado_por",
    )

    fieldsets = (
        ("Fondo", {
            "fields": ("fund",)
        }),
        ("Valor diario", {
            "fields": (
                "fecha",
                "capital_interactive_broker",
                "capital_binance",
            )
        }),
        ("Cálculos automáticos", {
            "fields": (
                "valor_total",
                "participaciones",
                "nav",
            )
        }),
        ("Auditoría", {
            "fields": (
                "creado_en",
                "creado_por",
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.creado_por:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)





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
        return f"€ {val:,.4f}"
    
    current_value_display.short_description = "Valor Actual"

    def has_add_permission(self, request):
        return False # 🔒 solo via trades
