from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from core.utils.decimal import quantize_4


User = get_user_model()


# =========================
# PERFIL DEL INVERSOR
# =========================

class Investor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="investor_profile"
    )

    # Datos personales / KYC básico
    document_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="DNI / Pasaporte",
        null=True,
        blank=True
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    birth_date = models.DateField(
        blank=True,
        null=True
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Dirección física"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        default="España"
    )

    # Identificador estratégico (para no mostrar IDs bajos a clientes)
    client_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Código estratégico de cliente (ej: INV-501)"
    )

    # Perfil de riesgo del inversor
    RISK_LEVELS = [
        ("LOW", "Bajo"),
        ("MEDIUM", "Medio"),
        ("HIGH", "Alto"),
    ]
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVELS,
        default="MEDIUM",
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Primero guardamos para tener un ID si es nuevo (necesario para el código)
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.client_code:
            # Generamos el código estratégico (BASE 500)
            self.client_code = f"INV-{500 + self.id:03d}"
            # Guardamos solo el campo client_code
            super().save(update_fields=["client_code"])

    def get_fund_positions(self):
        """
        Devuelve todas las posiciones del inversor en fondos.
        """
        return self.fund_positions.select_related("fund")

    def get_first_fund_position(self):
        """
        Devuelve la primera posición del inversor (si existe).
        """
        return self.fund_positions.first()

    class Meta:
        verbose_name = "Inversor"
        verbose_name_plural = "Inversores"

    def __str__(self):
        return f"Inversor: {self.user.username} ({self.client_code})"

# =========================================
# PARTICIPACIONES DEL INVERSOR EN UN FONDO
# =========================================
from decimal import Decimal


class InvestorFund(models.Model):
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="fund_positions"
    )

    fund = models.ForeignKey(
        "funds.Fund",
        on_delete=models.CASCADE,
        related_name="investors"
    )

    participations = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal("0")
    )

    average_price = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal("0")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Participación de Inversor"
        verbose_name_plural = "Participaciones de Inversores"
        unique_together = ("investor", "fund")

    def __str__(self):
        return f"{self.investor.user.username} → {self.fund.name} ({self.participations} part.)"

    def current_value(self) -> Decimal:
        """
        Valor actual de la posición del inversor en el fondo
        """
        nav = self.fund.current_nav()
        return quantize_4(self.participations * nav)

    def apply_transaction(self, transaction):
        """
        Aplica una transacción BUY o SELL al inversor
        y sincroniza las participaciones del fondo
        """

        # 🔒 Validación básica
        if transaction.participations <= 0:
            raise ValidationError(
                "Las participaciones deben ser mayores que cero."
            )

        if transaction.transaction_type == "BUY":

            # 🔒 Bloquear nuevas aportaciones si el fondo está cerrado
            if not self.fund.is_open:
                raise ValidationError(
                    "El fondo está cerrado y no acepta nuevas aportaciones."
                )

            total_cost = (
                self.participations * self.average_price
                + transaction.participations * transaction.nav_price
            )
            total_parts = self.participations + transaction.participations

            self.average_price = quantize_4(
                total_cost / total_parts
            )
            self.participations = total_parts

            # 🔁 Actualizar participaciones del fondo
            self.fund.participations += transaction.participations

        elif transaction.transaction_type == "SELL":

            if transaction.participations > self.participations:
                raise ValidationError(
                    "No se pueden vender más participaciones de las disponibles."
                )

            self.participations -= transaction.participations
            self.fund.participations -= transaction.participations

        # 🔒 Evitar negativos por seguridad
        self.fund.participations = max(
            self.fund.participations,
            Decimal("0")
        )

        # Guardar cambios
        self.fund.save(update_fields=["participations"])
        self.save()

class InvestorFundTransaction(models.Model):

    BUY = "BUY"
    SELL = "SELL"

    TRANSACTION_TYPES = [
        (BUY, "Compra"),
        (SELL, "Venta"),
    ]

    investor = models.ForeignKey(
        "investors.Investor",
        on_delete=models.CASCADE,
        related_name="fund_transactions"
    )

    fund = models.ForeignKey(
        "funds.Fund",
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    transaction_type = models.CharField(
        max_length=4,
        choices=TRANSACTION_TYPES
    )

    participations = models.DecimalField(
        max_digits=15,
        decimal_places=6
    )

    nav_price = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        editable=False   # 🔒 no editable
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False   # 🔒 calculado
    )

    created_at = models.DateTimeField(auto_now_add=True)

    reference = models.CharField(
        max_length=64,
        blank=True
    )

    class Meta:
        verbose_name = "Transacción de Inversor"
        verbose_name_plural = "Transacciones de Inversores"
        ordering = ("-created_at",)

    def __str__(self):
        return f"[{self.transaction_type}] {self.investor.user.username} - {self.fund.name}"



    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not self.nav_price:
            self.nav_price = self.fund.current_nav()

        self.amount = (self.participations * self.nav_price).quantize(
            Decimal("0.01")
        )

        with db_transaction.atomic():
            super().save(*args, **kwargs)

            if is_new:
                position, _ = InvestorFund.objects.get_or_create(
                    investor=self.investor,
                    fund=self.fund,
                    defaults={
                        "participations": Decimal("0"),
                        "average_price": Decimal("0"),
                    }
                )

                position.apply_transaction(self)


class Notification(models.Model):

    TEMPLATE_CHOICES = [
        ("GENERAL", "Aviso general"),
        ("ASSETS", "Informe de activos"),
        ("WELCOME", "Documento de bienvenida"),
        ("MONTHLY", "Informe mensual"),
    ]

    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        help_text="Inversor al que pertenece el aviso"
    )

    title = models.CharField(max_length=200)

    template = models.CharField(
        max_length=20,
        choices=TEMPLATE_CHOICES
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ("DRAFT", "Borrador"),
        ("SENT", "Enviado"),
        ("ERROR", "Error"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"[{self.status}] {self.title} -> {self.investor}"




