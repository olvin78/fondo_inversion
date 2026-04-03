from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Case, DecimalField, F, IntegerField, Sum, Value, When

from applications.funds.models import Fund
from applications.investors.models import Investor, InvestorFund, InvestorFundTransaction


class Command(BaseCommand):
    help = "Recalcula participaciones desde transacciones (BUY/SELL)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Solo muestra cambios (default si no se usa --apply).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Aplica cambios en la base de datos.",
        )
        parser.add_argument(
            "--tolerance",
            type=Decimal,
            default=Decimal("0.000001"),
            help="Tolerancia para diferencias (default: 0.000001)",
        )

    def handle(self, *args, **options):
        apply_changes = bool(options["apply"])
        tolerance = options["tolerance"]
        dry_run = not apply_changes

        if options["dry_run"] and apply_changes:
            self.stderr.write("No puedes usar --dry-run junto con --apply.")
            return

        mode_label = "DRY-RUN" if dry_run else "APPLY"

        self.stdout.write(self.style.MIGRATE_HEADING("Reconciliacion de participaciones"))
        self.stdout.write(f"Modo: {mode_label}")
        self.stdout.write(f"Tolerancia: {tolerance}")

        unknown_qs = (
            InvestorFundTransaction.objects.exclude(
                transaction_type__in=[
                    InvestorFundTransaction.BUY,
                    InvestorFundTransaction.SELL,
                    InvestorFundTransaction.BONUS,
                ]
            )
            .values("investor_id", "fund_id")
            .annotate(count=Sum(Value(1), output_field=IntegerField()))
        )

        unknown_map = {}
        for row in unknown_qs:
            unknown_map[(row["investor_id"], row["fund_id"])] = row["count"] or 0

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Tipos de transaccion desconocidos"))
        if not unknown_map:
            self.stdout.write(self.style.SUCCESS("Sin tipos desconocidos."))
        else:
            for (investor_id, fund_id), count in unknown_map.items():
                investor = Investor.objects.filter(id=investor_id).select_related("user").first()
                fund = Fund.objects.filter(id=fund_id).first()
                investor_label = investor.user.get_username() if investor and investor.user else "(sin user)"
                fund_label = fund.name if fund else "(sin fondo)"
                self.stdout.write(
                    f"- Inversor: {investor_label} | Fondo: {fund_label} | "
                    f"Desconocidas: {count}"
                )

        tx_sums = (
            InvestorFundTransaction.objects.filter(
                transaction_type__in=[
                    InvestorFundTransaction.BUY,
                    InvestorFundTransaction.SELL,
                    InvestorFundTransaction.BONUS,
                ]
            )
            .values("investor_id", "fund_id")
            .annotate(
                expected=Sum(
                    Case(
                        When(
                            transaction_type=InvestorFundTransaction.BUY,
                            then=F("participations"),
                        ),
                        When(
                            transaction_type=InvestorFundTransaction.BONUS,
                            then=F("participations"),
                        ),
                        When(
                            transaction_type=InvestorFundTransaction.SELL,
                            then=F("participations") * Value(-1),
                        ),
                        default=Value(0),
                        output_field=DecimalField(max_digits=20, decimal_places=6),
                    )
                )
            )
        )

        expected_map = {}
        for row in tx_sums:
            expected_map[(row["investor_id"], row["fund_id"])] = row["expected"] or Decimal("0")

        def write_unknown_notice(investor_id, fund_id):
            count = unknown_map.get((investor_id, fund_id), 0)
            if count:
                self.stdout.write(f"  * Aviso: {count} transaccion(es) con tipo desconocido.")

        updates = []
        creates = []

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("1) InvestorFund desde transacciones"))

        positions = InvestorFund.objects.select_related("investor__user", "fund")
        existing_keys = set()

        for position in positions:
            investor_id = position.investor_id
            fund_id = position.fund_id
            existing_keys.add((investor_id, fund_id))

            expected = expected_map.get((investor_id, fund_id), Decimal("0"))
            registered = position.participations or Decimal("0")
            diff = registered - expected

            if abs(diff) <= tolerance:
                continue

            investor_label = position.investor.user.get_username() if position.investor and position.investor.user else "(sin user)"
            fund_label = position.fund.name if position.fund else "(sin fondo)"
            self.stdout.write(
                f"- Inversor: {investor_label} | Fondo: {fund_label} | "
                f"Registrado: {registered} | Esperado: {expected} | Diferencia: {diff} | Accion: actualizar"
            )
            updates.append((position, expected))
            write_unknown_notice(investor_id, fund_id)

        missing_keys = set(expected_map.keys()) - existing_keys
        for investor_id, fund_id in sorted(missing_keys):
            expected = expected_map.get((investor_id, fund_id), Decimal("0"))
            if abs(expected) <= tolerance:
                continue
            investor = Investor.objects.filter(id=investor_id).select_related("user").first()
            fund = Fund.objects.filter(id=fund_id).first()
            investor_label = investor.user.get_username() if investor and investor.user else "(sin user)"
            fund_label = fund.name if fund else "(sin fondo)"
            diff = Decimal("0") - expected
            self.stdout.write(
                f"- Inversor: {investor_label} | Fondo: {fund_label} | "
                f"Registrado: 0 | Esperado: {expected} | Diferencia: {diff} | Accion: crear"
            )
            creates.append((investor_id, fund_id, expected))
            write_unknown_notice(investor_id, fund_id)

        if not updates and not creates:
            self.stdout.write(self.style.SUCCESS("Sin cambios necesarios en InvestorFund."))

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("2) Fund.participations desde InvestorFund"))

        fund_sums = (
            InvestorFund.objects.values("fund_id")
            .annotate(total_positions=Sum("participations"))
        )
        fund_sum_map = {row["fund_id"]: row["total_positions"] or Decimal("0") for row in fund_sums}

        fund_updates = []

        for fund in Fund.objects.all():
            registered = fund.participations or Decimal("0")
            expected = fund_sum_map.get(fund.id, Decimal("0"))
            diff = registered - expected

            if abs(diff) <= tolerance:
                continue

            self.stdout.write(
                f"- Fondo: {fund.name} | Registrado: {registered} | "
                f"Esperado: {expected} | Diferencia: {diff} | Accion: actualizar"
            )
            fund_updates.append((fund, expected))

        if not fund_updates:
            self.stdout.write(self.style.SUCCESS("Sin cambios necesarios en Fund."))

        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("DRY-RUN: no se aplicaron cambios."))
            return

        with transaction.atomic():
            for position, expected in updates:
                position.participations = expected
                position.save(update_fields=["participations"])

            for investor_id, fund_id, expected in creates:
                InvestorFund.objects.create(
                    investor_id=investor_id,
                    fund_id=fund_id,
                    participations=expected,
                )

            for fund, expected in fund_updates:
                fund.participations = expected
                fund.save(update_fields=["participations"])

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Cambios aplicados."))
