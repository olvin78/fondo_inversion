from django.db import models

# Create your models here.
from django.db import models
from applications.portfolios.models import Portfolio
from applications.products.models import Product

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("BUY", "Compra"),
        ("SELL", "Venta"),
        ("DEPOSIT", "Depósito"),
        ("WITHDRAW", "Retiro"),
    ]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="transactions")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.portfolio}"
