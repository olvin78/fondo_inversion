from django.db import models
from decimal import Decimal

from applications.portfolios.models import Portfolio
from applications.products.models import Product


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

    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

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

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=Decimal("0.0")
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.0")
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Importe total de la transacción"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transacción de cartera"
        verbose_name_plural = "Transacciones de cartera"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.transaction_type} - {self.portfolio}"


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
