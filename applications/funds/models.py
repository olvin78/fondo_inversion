from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from decimal import Decimal
from applications.products.models import Product

User = get_user_model()


# =========================
# NIVEL DE RIESGO DEL FONDO
# =========================

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


# ==========
# FONDO
# ==========

class Fund(models.Model):

    CURRENCIES = [
        ("EUR", "Euro"),
        ("USD", "Dólar estadounidense"),
        ("GBP", "Libra esterlina"),
    ]

    # Información básica
    name = models.CharField(max_length=150)
    products = models.ManyToManyField(Product)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    manager = models.CharField(
        max_length=100,
        blank=True,
        help_text="Gestor del fondo"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCIES,
        default="EUR"
    )
    nav_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal("0.00"),
        help_text="NAV (valor neto de las participaciones)"
    )

    # Riesgo
    risk_level = models.ForeignKey(
        FundRiskLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="funds"
    )

    # Estado del fondo
    is_open = models.BooleanField(
        default=True,
        help_text="Indica si el fondo acepta nuevas aportaciones"
    )

    # Tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_funds"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =========================
    # MÉTODOS FINANCIEROS CLAVE
    # =========================

    def total_participations(self) -> Decimal:
        """
        Total de participaciones emitidas del fondo.
        """
        total = sum(
            inv.participations
            for inv in self.investors.all()
        )
        return total or Decimal("0")

    def portfolio_value(self) -> Decimal:
        """
        Valor total de la cartera del fondo.
        (De momento mock / manual)
        Luego se conectará con Portfolio / IBKR.
        """
        return Decimal("0")

    def cash(self) -> Decimal:
        """
        Efectivo disponible del fondo.
        (Mock por ahora)
        """
        return Decimal("0")

    def nav(self) -> Decimal:
        """
        NAV (Net Asset Value) del fondo.
        """
        return self.portfolio_value() + self.cash()

    def participation_value(self) -> Decimal:
        """
        Valor actual de una participación.
        """
        total = self.total_participations()
        if total == 0:
            return Decimal("1.00")  # valor inicial
        return self.nav() / total

    def risk_label(self) -> str:
        if self.risk_level:
            return f"{self.risk_level.name} (Nivel {self.risk_level.level})"
        return "No definido"

    # ==========
    # DJANGO
    # ==========

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

