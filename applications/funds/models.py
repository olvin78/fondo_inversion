from django.db import models

# Create your models here.
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class FundRiskLevel(models.Model):
    name = models.CharField(max_length=50, unique=True)
    level = models.IntegerField(
        help_text="1 = bajo riesgo, 5 = alto riesgo"
    )
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Nivel de riesgo"
        verbose_name_plural = "Niveles de riesgo"
        ordering = ("level",)

    def __str__(self):
        return f"{self.name} (Nivel {self.level})"



class Fund(models.Model):
    CURRENCIES = [
        ("EUR", "Euro"),
        ("USD", "Dólar estadounidense"),
        ("GBP", "Libra esterlina"),
    ]

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    manager = models.CharField(max_length=100, blank=True, help_text="Gestor del fondo")
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="EUR")

    # Relación con riesgo
    risk_level = models.ForeignKey(
        FundRiskLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="funds"
    )

    # 👉 Aquí agregas la relación con productos financieros
    products = models.ManyToManyField(
        "FinancialProduct",
        related_name="funds",
        blank=True,
        help_text="Productos financieros que componen este fondo"
    )

    # Estado del fondo
    is_open = models.BooleanField(default=True)

    # Tracking
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Datos financieros básicos
    nav = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Valor liquidativo actual (NAV)"
    )
    performance_1y = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Rentabilidad 1 año (%)"
    )
    performance_5y = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Rentabilidad 5 años (%)"
    )

    class Meta:
        verbose_name = "Fondo"
        verbose_name_plural = "Fondos"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    # 👇 ESTE MÉTODO ES OBLIGATORIO
    def risk_label(self):
        if self.risk_level:
            return f"{self.risk_level.name} (Nivel {self.risk_level.level})"
        return "No definido"


class FinancialProduct(models.Model):
    ASSET_TYPES = [
        ("stock", "Acción"),
        ("bond", "Bono"),
        ("etf", "ETF"),
        ("crypto", "Criptomoneda"),
        ("fund", "Fondo"),
        ("commodity", "Materia prima"),
        ("other", "Otro"),
    ]

    name = models.CharField(max_length=150)
    ticker = models.CharField(max_length=20, blank=True, null=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default="stock")
    description = models.TextField(blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.ticker})"

