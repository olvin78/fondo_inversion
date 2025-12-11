from django.contrib import admin

# Register your models here.
from .models import Fund, FundRiskLevel, FinancialProduct


# ----------------------------
# ADMIN: FundRiskLevel
# ----------------------------
@admin.register(FundRiskLevel)
class FundRiskLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "level")
    ordering = ("level",)
    search_fields = ("name",)


# ----------------------------
# ADMIN: FinancialProduct
# ----------------------------
@admin.register(FinancialProduct)
class FinancialProductAdmin(admin.ModelAdmin):
    list_display = ("name", "ticker", "asset_type", "current_price")
    search_fields = ("name", "ticker", "asset_type")
    list_filter = ("asset_type",)
    ordering = ("name",)


# ----------------------------
# ADMIN: Fund
# ----------------------------
@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "risk_label_display",
        "manager",
        "currency",
        "is_open",
        "created_at",
    )

    search_fields = ("name", "manager", "description")
    list_filter = ("currency", "is_open", "risk_level")

    # Para seleccionar productos en interfaz horizontal bonita
    filter_horizontal = ("products",)

    # ------------------------
    # MÉTODO NECESARIO PARA ADMIN (evita el error E108)
    # ------------------------
    def risk_label_display(self, obj):
        return obj.risk_label() if obj.risk_level else "No definido"

    risk_label_display.short_description = "Nivel de riesgo"