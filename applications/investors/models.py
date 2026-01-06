from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

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

    def __str__(self):
        return f"Inversor: {self.user.username}"

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
        unique_together = ("investor", "fund")

    def current_value(self) -> Decimal:
        """
        Valor actual de la posición del inversor en el fondo
        """
        nav = self.fund.participation_value()
        return self.participations * nav

    def __str__(self):
        return f"{self.investor.user.username} → {self.fund.name}"


class InvestorFundTransaction(models.Model):

    BUY = "BUY"
    SELL = "SELL"

    TRANSACTION_TYPES = [
        (BUY, "Compra"),
        (SELL, "Venta"),
    ]

    investor = models.ForeignKey(
        Investor,
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
        help_text="Precio NAV aplicado en la operación"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Importe total (€)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    reference = models.CharField(
        max_length=64,
        blank=True,
        help_text="Referencia externa / IB / bancaria"
    )

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.investor.user.username} {self.transaction_type} {self.participations}"


def recalculate_position(position, transaction):
    if transaction.transaction_type == "BUY":
        total_cost = (
            position.participations * position.average_price +
            transaction.participations * transaction.nav_price
        )
        total_parts = position.participations + transaction.participations

        position.average_price = total_cost / total_parts
        position.participations = total_parts

    elif transaction.transaction_type == "SELL":
        position.participations -= transaction.participations

    position.save()



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

    def __str__(self):
        return f"{self.title} ({self.investor})"




def notification_create_monthly(request):
    investor = request.user.investor_profile  # 👈 AQUÍ ESTÁ LA CLAVE

    # cálculos (los que ya tienes)
    capital_invertido = ...
    capital_actual = ...
    variacion = ...
    porcentaje = ...
    participaciones = ...

    return render(
        request,
        "investors/monthly_report.html",
        {
            "investor": investor,   # 👈 PASAS EL INVERSOR
            "capital_invertido": capital_invertido,
            "capital_actual": capital_actual,
            "variacion": variacion,
            "porcentaje": porcentaje,
            "participaciones": participaciones,
        }
    )
