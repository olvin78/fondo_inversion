from django.db import models
from decimal import Decimal

from applications.products.models import Product
from applications.funds.models import Fund, FundPosition


# =================================
# TRANSACCIONES DE CARTERA (TRADING)
# =================================

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("BUY", "Compra"),
        ("SELL", "Venta"),
        ("DEPOSIT", "Depósito"),
        ("WITHDRAW", "Retiro"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )

    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Solo operaciones de trading
        if self.transaction_type not in ("BUY", "SELL") or not self.product:
            return

        fund = Fund.objects.first()
        if not fund:
            return

        position, created = FundPosition.objects.get_or_create(
            fund=fund,
            product=self.product,
            defaults={
                "quantity": Decimal("0"),
                "avg_price": Decimal("0"),
            }
        )

        if self.transaction_type == "BUY":
            total_cost = (position.quantity * position.avg_price) + (self.quantity * self.price)
            new_quantity = position.quantity + self.quantity

            position.avg_price = total_cost / new_quantity
            position.quantity = new_quantity
            position.save()

        elif self.transaction_type == "SELL":
            position.quantity -= self.quantity
            if position.quantity <= 0:
                position.delete()
            else:
                position.save()
# =========================================
# TRANSACCIONES DE INVERSORES (FONDO)
# =================================

class InvestorTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("IN", "Aportación"),
        ("OUT", "Retirada"),
    ]

    investor = models.ForeignKey(
        "investors.Investor",
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    fund = models.ForeignKey(
        "funds.Fund",
        on_delete=models.CASCADE,
        related_name="investor_transactions"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Importe aportado o retirado"
    )

    participations = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="Participaciones generadas o retiradas"
    )

    participation_value = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        help_text="Valor de la participación en ese momento"
    )

    transaction_type = models.CharField(
        max_length=3,
        choices=TRANSACTION_TYPES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transacción de inversor"
        verbose_name_plural = "Transacciones de inversores"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.investor.user.username} {self.transaction_type} {self.amount}"
