from django.contrib import admin

from django.contrib import admin
from .models import IBSnapshot, IBPosition


class IBPositionInline(admin.TabularInline):
    model = IBPosition
    extra = 0
    readonly_fields = (
        "symbol",
        "quantity",
        "market_value",
        "unrealized_pnl",
    )


@admin.register(IBSnapshot)
class IBSnapshotAdmin(admin.ModelAdmin):
    readonly_fields = (
        "account",
        "net_liquidation",
        "cash",
        "equity",
        "margin_used",
        "created_at",
    )
