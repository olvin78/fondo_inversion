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
        help_text="DNI / Pasaporte"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
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
        default="MEDIUM"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inversor: {self.user.username}"


# =========================================
# PARTICIPACIONES DEL INVERSOR EN UN FONDO
# =========================================

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

    # Participaciones del fondo
    participations = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal("0.0"),
        help_text="Participaciones del fondo"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("investor", "fund")
        verbose_name = "Participación en fondo"
        verbose_name_plural = "Participaciones en fondos"

    def current_value(self) -> Decimal:
        """
        Valor actual de la posición del inversor en este fondo.
        """
        return self.participations * self.fund.participation_value()

    def __str__(self):
        return f"{self.investor.user.username} → {self.fund.name}"
