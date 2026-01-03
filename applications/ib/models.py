from django.db import models

class IBSnapshot(models.Model):
    """
    Snapshot del estado general de la cuenta de IB
    Se genera cada 15 minutos
    """
    created_at = models.DateTimeField(auto_now_add=True)

    account = models.CharField(max_length=32)

    net_liquidation = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Valor total de la cuenta"
    )

    cash = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Efectivo disponible"
    )

    equity = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Valor de posiciones abiertas"
    )

    margin_used = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Margen utilizado (si aplica)"
    )

    def __str__(self):
        return f"{self.account} | {self.created_at:%Y-%m-%d %H:%M}"


class IBPosition(models.Model):
    """
    Posición individual asociada a un snapshot
    """
    snapshot = models.ForeignKey(
        IBSnapshot,
        on_delete=models.CASCADE,
        related_name="positions"
    )

    symbol = models.CharField(max_length=32)
    exchange = models.CharField(max_length=32, blank=True)
    currency = models.CharField(max_length=8)

    quantity = models.DecimalField(
        max_digits=20,
        decimal_places=4
    )

    avg_price = models.DecimalField(
        max_digits=20,
        decimal_places=4
    )

    market_price = models.DecimalField(
        max_digits=20,
        decimal_places=4
    )

    market_value = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    unrealized_pnl = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    realized_pnl = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.symbol} ({self.quantity})"
