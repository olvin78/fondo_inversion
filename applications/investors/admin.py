from django.contrib import admin
from .models import Investor, InvestorFund


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username", "user__email")


@admin.register(InvestorFund)
class InvestorFundAdmin(admin.ModelAdmin):
    list_display = (
        "investor",
        "fund",
        "participations",
        "current_value_display",
        "created_at",
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
        "current_value_display",
    )

    ordering = ("-created_at",)

    def current_value_display(self, obj):
        return obj.current_value()

    current_value_display.short_description = "Valor actual"
