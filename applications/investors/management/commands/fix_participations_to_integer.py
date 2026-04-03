from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.investors.models import InvestorFundTransaction


class Command(BaseCommand):
    help = "Corrige participations a enteros (1.0000) por ID"

    IDS = [40, 39, 38, 34, 33, 32]

    def handle(self, *args, **options):
        qs = InvestorFundTransaction.objects.filter(id__in=self.IDS)
        found_ids = set(qs.values_list("id", flat=True))
        missing = [str(pk) for pk in self.IDS if pk not in found_ids]

        if missing:
            self.stdout.write(self.style.ERROR(
                f"Faltan IDs en la base de datos: {', '.join(missing)}"
            ))
            return

        with transaction.atomic():
            for tx in qs:
                tx.participations = Decimal("1.0000")
                tx.save(update_fields=["participations"])

        self.stdout.write(self.style.SUCCESS(
            f"Actualizados {len(self.IDS)} registros correctamente."
        ))
