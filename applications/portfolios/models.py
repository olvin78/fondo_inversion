from django.db import models


class Portfolio(models.Model):
    investor = models.ForeignKey(
        "investors.Investor",
        on_delete=models.CASCADE,
        related_name="portfolios"
    )

    name = models.CharField(
        max_length=100,
        default="Cartera principal"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cartera de {self.investor.user.username} - {self.name}"


class PortfolioItem(models.Model):
    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4
    )

    avg_buy_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def current_value(self):
        return self.quantity * self.product.current_price

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
