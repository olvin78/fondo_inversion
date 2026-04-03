from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Case, DecimalField, F, IntegerField, Q, Sum, Value, When

from applications.funds.models import Fund
from applications.investors.models import Investor, InvestorFund, InvestorFundTransaction


class Command(BaseCommand):
    help = "Audita discrepancias de participaciones entre posiciones y transacciones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tolerance",
            type=Decimal,
            default=Decimal("0.000001"),
            help="Tolerancia para diferencias (default: 0.000001)",
        )

    def handle(self, *args, **options):
        tolerance = options["tolerance"]

        self.stdout.write(self.style.MIGRATE_HEADING("Auditoria de participaciones"))
        self.stdout.write(f"Tolerancia: {tolerance}")

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("1) Inversor/Fondo: InvestorFund vs Transacciones"))

        tx_sums = (
            InvestorFundTransaction.objects.values("investor_id", "fund_id")
            .annotate(
                expected=Sum(
                    Case(
                        When(transaction_type=InvestorFundTransaction.BUY, then=F("participations")),
                        When(transaction_type=InvestorFundTransaction.SELL, then=F("participations") * Value(-1)),
                        default=Value(0),
                        output_field=DecimalField(max_digits=20, decimal_places=6),
                    )
                ),
                unknown_types=Sum(
                    Case(
                        When(
                            ~Q(
                                transaction_type__in=[
                                    InvestorFundTransaction.BUY,
                                    InvestorFundTransaction.SELL,
                                ]
                            ),
                            then=Value(1),
                        ),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ),
            )
        )

        discrepancies = 0
        for row in tx_sums:
            investor = Investor.objects.filter(id=row["investor_id"]).select_related("user").first()
            fund = Fund.objects.filter(id=row["fund_id"]).first()
            position = InvestorFund.objects.filter(
                investor_id=row["investor_id"],
                fund_id=row["fund_id"],
            ).first()

            registered = position.participations if position else Decimal("0")
            expected = row["expected"] or Decimal("0")
            diff = registered - expected

            if abs(diff) > tolerance:
                discrepancies += 1
                investor_label = investor.user.get_username() if investor and investor.user else "(sin user)"
                fund_label = fund.name if fund else "(sin fondo)"
                self.stdout.write(
                    f"- Inversor: {investor_label} | Fondo: {fund_label} | "
                    f"Registrado: {registered} | Esperado: {expected} | Diferencia: {diff}"
                )
                if row.get("unknown_types"):
                    self.stdout.write("  * Aviso: hay tipos de transaccion desconocidos.")

        if discrepancies == 0:
            self.stdout.write(self.style.SUCCESS("Sin discrepancias detectadas."))

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("2) Fondo: Fund.participations vs suma InvestorFund"))

        fund_sums = (
            InvestorFund.objects.values("fund_id")
            .annotate(total_positions=Sum("participations"))
        )

        fund_discrepancies = 0
        for row in fund_sums:
            fund = Fund.objects.filter(id=row["fund_id"]).first()
            registered = fund.participations if fund else Decimal("0")
            expected = row["total_positions"] or Decimal("0")
            diff = registered - expected

            if abs(diff) > tolerance:
                fund_discrepancies += 1
                fund_label = fund.name if fund else "(sin fondo)"
                self.stdout.write(
                    f"- Fondo: {fund_label} | "
                    f"Registrado: {registered} | Esperado: {expected} | Diferencia: {diff}"
                )

        if fund_discrepancies == 0:
            self.stdout.write(self.style.SUCCESS("Sin discrepancias detectadas."))
