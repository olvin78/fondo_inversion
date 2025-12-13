from django.contrib import admin
from .models import Fund, FundRiskLevel


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
        "risk_label_display",
        "manager",
        "currency",
        "is_open",
        "created_at",
    )

    search_fields = ("name", "manager", "description")
    list_filter = ("currency", "is_open", "risk_level")
    prepopulated_fields = {"slug": ("name",)}

    # ------------------------
    # MÉTODO PARA MOSTRAR RIESGO
    # ------------------------
    def risk_label_display(self, obj):
        return obj.risk_label()

    risk_label_display.short_description = "Nivel de riesgo"
