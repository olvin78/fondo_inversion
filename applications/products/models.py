from django.db import models

# Create your models here.
from django.db import models

class Product(models.Model):
    PRODUCT_TYPES = [
        ("STOCK", "Acciones"),
        ("ETF", "ETF"),
        ("FUND", "Fondo de inversión"),
        ("CRYPTO", "Criptomonedas"),
        ("COMMODITY", "Materias primas"),
        ("BOND", "Bonos"),
    ]

    name = models.CharField(max_length=100)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    ticker = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.product_type})"
