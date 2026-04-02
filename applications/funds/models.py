from django.db import models
from django.db.models import Sum, Case, When, F, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from decimal import Decimal
from applications.products.models import Product
from django.core.exceptions import ValidationError



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
        verbose_name = "Nivel de Riesgo"
        verbose_name_plural = "Niveles de Riesgo"
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

    participations = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal("0"),
        help_text="Total de participaciones emitidas (auto)"
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
    # NAV HISTÓRICO
    # =========================

    def current_nav(self) -> Decimal:
        """
        Devuelve el último NAV registrado.
        """
        latest = self.valores_diarios.order_by("-fecha").first()
        return latest.nav if latest else Decimal("0.00")

    def nav_on_date(self, date):
        """
        Devuelve el NAV del fondo en una fecha concreta.
        """
        nav = self.valores_diarios.filter(fecha__lte=date).order_by("-fecha").first()
        return nav.nav if nav else None


    # =========================
    # MÉTODOS FINANCIEROS CLAVE
    # =========================



    def portfolio_value(self) -> Decimal:
        """
        Valor total de la cartera del fondo (suma de posiciones)
        """
        total = Decimal("0")

        for position in self.positions.select_related("product"):
            if hasattr(position.product, "current_price") and position.product.current_price:
                total += position.quantity * position.product.current_price

        return total

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
        total = self.total_participations_calculated
        if total == 0:
            return Decimal("1.00")  # valor inicial
        return self.nav() / total

    @property
    def aum(self) -> Decimal:
        """
        Assets Under Management (AUM) = participaciones actuales * NAV actual.
        """
        nav_value = self.nav_actual or self.current_nav()
        return (self.total_participations or Decimal("0")) * (nav_value or Decimal("0"))

    @property
    def total_participations_calculated(self) -> Decimal:
        """
        Calcula dinámicamente el total de participaciones a partir de las transacciones reales.
        Utiliza InvestorFundTransaction (related_name='transactions').
        """
        from applications.investors.models import InvestorFundTransaction

        sell_types = [
            InvestorFundTransaction.SELL,
            "WITHDRAW",
            "RETIRADA",
        ]

        result = self.transactions.aggregate(
            total=Coalesce(
                Sum(
                    Case(
                        When(
                            transaction_type=InvestorFundTransaction.BUY,
                            then=F("participations"),
                        ),
                        When(
                            transaction_type__in=sell_types,
                            then=-F("participations"),
                        ),
                        default=Value(Decimal("0")),
                        output_field=DecimalField(max_digits=20, decimal_places=6),
                    )
                ),
                Value(Decimal("0"), output_field=DecimalField(max_digits=20, decimal_places=6)),
            )
        )
        return result["total"]

    @property
    def total_participations(self) -> Decimal:
        return self.total_participations_calculated

    def get_total_participations(self) -> Decimal:
        return self.total_participations

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

class FundDiversification(models.Model):
    """
    Bloque de diversificación del fondo
    (para gráficos tipo tarta)
    """

    PRODUCT_TYPES = [
        ("STOCK", "Acciones"),
        ("ETF", "ETF"),
        ("COMMODITY", "Materias primas"),
        ("BOND", "Bonos"),
        ("CASH", "Liquidez"),
        ("CRYPTO", "Criptomonedas"),
    ]

    fund = models.ForeignKey(
        "funds.Fund",
        on_delete=models.CASCADE,
        related_name="diversification"
    )

    name = models.CharField(
        max_length=50,
        help_text="Nombre visible (ej: Acciones)"
    )

    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje asignado (ej: 40.00)"
    )

    color = models.CharField(
        max_length=7,
        default="#3b82f6",
        help_text="Color HEX para el gráfico (ej: #3b82f6)"
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Mostrar en el gráfico"
    )

    class Meta:
        verbose_name = "Diversificación del fondo"
        verbose_name_plural = "Diversificación del fondo"
        ordering = ("order",)
        unique_together = ("fund", "product_type")

    def clean(self):
        total = (
            FundDiversification.objects
            .filter(fund=self.fund)
            .exclude(pk=self.pk)
            .aggregate(models.Sum("percentage"))["percentage__sum"]
            or Decimal("0")
        )

        if total + self.percentage > Decimal("100"):
            raise ValidationError(
                "La suma de la diversificación no puede superar el 100% para este fondo."
            )

    def __str__(self):
        return f"{self.fund.name} · {self.name} ({self.percentage}%)"



class FundPosition(models.Model):
    """
    Posición real del fondo en un activo concreto
    """

    fund = models.ForeignKey(
        "funds.Fund",
        on_delete=models.CASCADE,
        related_name="positions"
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="fund_positions"
    )

    quantity = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        help_text="Cantidad total del activo en cartera"
    )

    avg_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Precio medio de compra"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("fund", "product")
        verbose_name = "Posición de Cartera"
        verbose_name_plural = "Inventario de Cartera"

    def current_value(self) -> Decimal:
        """
        Valor actual de la posición (mock por ahora)
        """
        if hasattr(self.product, "current_price") and self.product.current_price:
            return self.quantity * self.product.current_price
        return Decimal("0")

    @property
    def total_value(self):
        return self.quantity * self.avg_price

    def __str__(self):
        return f"{self.product.name} — {self.quantity}"

class FundTrade(models.Model):
    TRANSACTION_TYPES = [
        ("BUY", "Compra"),
        ("SELL", "Venta"),
    ]

    fund = models.ForeignKey(
        "funds.Fund",
        on_delete=models.CASCADE,
        related_name="trades"
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="fund_trades"
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )

    quantity = models.DecimalField(max_digits=16, decimal_places=6)
    price = models.DecimalField(max_digits=12, decimal_places=4)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return self.quantity * self.price

    class Meta:
        verbose_name = "Operación de Fondo"
        verbose_name_plural = "Libro Diario de Operaciones"
        ordering = ("-created_at",)

    def __str__(self):
        return f"[{self.transaction_type}] {self.product.ticker} - {self.fund.name} ({self.created_at.date()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        position, _ = FundPosition.objects.get_or_create(
            fund=self.fund,
            product=self.product,
            defaults={
                "quantity": Decimal("0"),
                "avg_price": Decimal("0"),
            }
        )

        if self.transaction_type == "BUY":
            total_cost = (
                position.quantity * position.avg_price
                + self.quantity * self.price
            )
            new_quantity = position.quantity + self.quantity

            position.avg_price = total_cost / new_quantity
            position.quantity = new_quantity
            position.save()

        elif self.transaction_type == "SELL":
            if self.quantity > position.quantity:
                raise ValidationError("No se puede vender más de lo disponible")

            position.quantity -= self.quantity
            if position.quantity == 0:
                position.delete()
            else:
                position.save()


class ValorDiarioFondo(models.Model):
    """
    Valor real del fondo en una fecha concreta.
    """

    fund = models.ForeignKey(
        Fund,
        on_delete=models.CASCADE,
        related_name="valores_diarios"
    )

    fecha = models.DateField(
        help_text="Fecha efectiva del valor del fondo"
    )

    capital_interactive_broker = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Capital total en Interactive Brokers"
    )

    capital_binance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Capital total en Binance"
    )

    valor_total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        help_text="Valor total del fondo (IBKR + Binance)"
    )

    participaciones = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Número total de participaciones del fondo"
    )

    nav = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        default=Decimal("0"),
        editable=False,
        help_text="NAV del fondo en la fecha indicada"
    )

    creado_en = models.DateTimeField(auto_now_add=True)

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="valores_diarios_creados"
    )

    class Meta:
        verbose_name = "Valor diario del fondo"
        verbose_name_plural = "Valores diarios del fondo"
        ordering = ("-fecha",)
        unique_together = ("fund", "fecha")

    def __str__(self):
        return f"{self.fund.name} · {self.fecha}"

    def save(self, *args, **kwargs):
        self.valor_total = (
            (self.capital_interactive_broker or Decimal("0"))
            + (self.capital_binance or Decimal("0"))
        )

        total_participations = self.fund.total_participations
        self.participaciones = total_participations or Decimal("0")

        if self.participaciones > 0:
            self.nav = (self.valor_total / self.participaciones).quantize(
                Decimal("0.000001")
            )
        else:
            self.nav = Decimal("0")

        super().save(*args, **kwargs)

        self.fund.nav_actual = self.nav
        self.fund.save(update_fields=["nav_actual"])
