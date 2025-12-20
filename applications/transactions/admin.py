from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "product",
        "transaction_type",
        "quantity",
        "price",
        "total_display",
    )

    list_filter = (
        "transaction_type",
        "created_at",
        "product",
    )

    search_fields = (
        "product__name",
        "analysis",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "product",
                "transaction_type",
            )
        }),
        ("Detalles de la operación", {
            "fields": (
                "quantity",
                "price",
                "analysis",
            )
        }),
        ("Información automática", {
            "fields": (
                "created_at",
            )
        }),
    )

    def total_display(self, obj):
        return f"{obj.total:.2f} €"

    total_display.short_description = "Total"
