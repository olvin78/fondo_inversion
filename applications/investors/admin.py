from django.contrib import admin
from .models import Investor, InvestorFund, InvestorFundTransaction


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "document_id",
        "risk_level",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "document_id",
    )
    list_filter = ("risk_level",)
    ordering = ("-created_at",)


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

    list_filter = (
        "fund",
        "created_at",
    )

    search_fields = (
        "investor__user__username",
        "investor__user__email",
        "fund__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "current_value_display",
    )

    ordering = ("-updated_at",)

    def current_value_display(self, obj):
        return obj.current_value()

    current_value_display.short_description = "Valor actual"



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

    list_filter = (
        "transaction_type",
        "fund",
        "created_at",
    )

    search_fields = (
        "investor__user__username",
        "investor__user__email",
        "fund__name",
        "reference",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "investor",
        "fund",
        "transaction_type",
        "participations",
        "nav_price",
        "amount",
        "created_at",
        "reference",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return True  # permitir añadir TEMPORALMENTE

