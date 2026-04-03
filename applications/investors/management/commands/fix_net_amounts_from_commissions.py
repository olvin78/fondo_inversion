from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.investors.models import InvestorFundTransaction
from core.utils.decimal import round4


class Command(BaseCommand):
    help = "Ajusta importes netos a partir de comisiones (1%)"

    def handle(self, *args, **options):
        net_qs = InvestorFundTransaction.objects.filter(
            reference__icontains="Compra neta (99%)"
        ).select_related("investor", "fund")

        updated = 0
        skipped = 0

        with transaction.atomic():
            for tx in net_qs:
                investor_name = tx.investor.user.username
                fee_tx = InvestorFundTransaction.objects.filter(
                    reference__icontains=f"Comisión 1% de la transacción de {investor_name}",
                    fund=tx.fund,
                    created_at__date=tx.created_at.date(),
                ).order_by("-created_at").first()

                if not fee_tx:
                    skipped += 1
                    continue

                expected_net = round4(fee_tx.amount * Decimal("99"))
                if tx.amount == expected_net:
                    continue

                tx.amount = expected_net
                tx.save(update_fields=["amount"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Actualizados: {updated} | Sin comisión asociada: {skipped}"
        ))
