from decimal import Decimal
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from applications.investors.models import InvestorFundTransaction


class Command(BaseCommand):
    help = "Actualiza InvestorFundTransaction por ID con datos de Excel"

    DATA = {
        28: {
            "amount": "450.0000",
            "nav_price": "10.0000",
            "participations": "45.0000",
            "created_at": "2025-11-01",
        },
        29: {
            "amount": "1787.8788",
            "nav_price": "10.0000",
            "participations": "178.7879",
            "created_at": "2025-11-01",
        },
        30: {
            "amount": "100.0000",
            "nav_price": "9.8552",
            "participations": "10.0455",
            "created_at": "2026-01-04",
        },
        31: {
            "amount": "70.6691",
            "nav_price": "9.6792",
            "participations": "7.3011",
            "created_at": "2026-01-31",
        },
        32: {
            "amount": "9.77697",
            "nav_price": "9.6792",
            "participations": "1.0101",
            "created_at": "2026-02-01",
        },
        33: {
            "amount": "9.77697",
            "nav_price": "9.6792",
            "participations": "1.0101",
            "created_at": "2026-02-01",
        },
        34: {
            "amount": "9.77697",
            "nav_price": "9.6792",
            "participations": "1.0101",
            "created_at": "2026-02-01",
        },
        35: {
            "amount": "100.0000",
            "nav_price": "9.9363",
            "participations": "10.0641",
            "created_at": "2026-03-15",
        },
        36: {
            "amount": "50.0000",
            "nav_price": "9.6266",
            "participations": "5.1420",
            "created_at": "2026-03-15",
        },
        37: {
            "amount": "100.8286",
            "nav_price": "9.6266",
            "participations": "10.3692",
            "created_at": "2026-03-15",
        },
        38: {
            "amount": "9.7238",
            "nav_price": "9.6266",
            "participations": "1.0100",
            "created_at": "2026-03-15",
        },
        39: {
            "amount": "9.7238",
            "nav_price": "9.6266",
            "participations": "1.0100",
            "created_at": "2026-03-15",
        },
        40: {
            "amount": "9.7238",
            "nav_price": "9.6266",
            "participations": "1.0100",
            "created_at": "2026-03-15",
        },
    }

    def handle(self, *args, **options):
        ids = sorted(self.DATA.keys())
        qs = InvestorFundTransaction.objects.filter(id__in=ids)
        found_ids = set(qs.values_list("id", flat=True))
        missing = [str(pk) for pk in ids if pk not in found_ids]

        if missing:
            self.stdout.write(self.style.ERROR(
                f"Faltan IDs en la base de datos: {', '.join(missing)}"
            ))
            return

        with transaction.atomic():
            for tx in qs:
                row = self.DATA[tx.id]
                tx.amount = Decimal(row["amount"])
                tx.nav_price = Decimal(row["nav_price"])
                tx.participations = Decimal(row["participations"])
                date_value = datetime.strptime(row["created_at"], "%Y-%m-%d")
                tx.created_at = timezone.make_aware(date_value)
                tx.save(update_fields=[
                    "amount",
                    "nav_price",
                    "participations",
                    "created_at",
                ])

        self.stdout.write(self.style.SUCCESS(
            f"Actualizados {len(ids)} registros correctamente."
        ))
