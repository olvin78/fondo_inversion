from django.contrib import admin
from django.db import transaction
from decimal import Decimal
from django.core.exceptions import ValidationError

from .models import Investor, InvestorFund, InvestorFundTransaction


# =========================
# INVERSOR
# =========================

from django.urls import reverse
from django.utils.safestring import mark_safe

@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ("user", "document_id", "risk_level", "impersonate_button", "created_at")
    search_fields = ("user__username", "user__email", "document_id")
    list_filter = ("risk_level",)
    ordering = ("-created_at",)

    def impersonate_button(self, obj):
        url = reverse("hijack:acquire", args=[obj.user.pk])
        return mark_safe(f'<a class="button" href="{url}" style="background-color: #3b82f6; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">Ver como usuario</a>')
    
    impersonate_button.short_description = "Acción"


# =========================
# POSICIÓN DEL INVERSOR EN EL FONDO (SOLO LECTURA)
# =========================

@admin.register(InvestorFund)
class InvestorFundAdmin(admin.ModelAdmin):
    list_display = (
        "investor",
        "fund",
        "participations",
        "average_price",
        "current_value_display",
        "created_at",
        "updated_at",
    )

    list_filter = ("fund",)
    search_fields = (
        "investor__user__username",
        "investor__user__email",
        "fund__name",
    )

    readonly_fields = (
        "investor",
        "fund",
        "participations",
        "average_price",
        "current_value_display",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False  # 🔒 no se crea a mano

    def has_change_permission(self, request, obj=None):
        return False  # 🔒 no se edita

    def has_delete_permission(self, request, obj=None):
        return False  # 🔒 no se borra

    def current_value_display(self, obj):
        return obj.current_value()

    current_value_display.short_description = "Valor actual"



# =========================
# TRANSACCIONES DEL FONDO
# =========================

@admin.register(InvestorFundTransaction)
class InvestorFundTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "investor",
        "fund",
        "transaction_type",
        "participations",
        "nav_price",
        "amount",
        "created_at",
    )

    readonly_fields = (
        "nav_price",
        "amount",
        "created_at",
    )

    autocomplete_fields = ("investor", "fund")

    def has_change_permission(self, request, obj=None):
        return False   # 🔒 histórico inmutable

    def has_delete_permission(self, request, obj=None):
        return False
