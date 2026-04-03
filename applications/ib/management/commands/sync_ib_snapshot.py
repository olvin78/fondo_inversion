from django.core.management.base import BaseCommand
from applications.ib.services.snapshot_service import sync_ib_snapshot


class Command(BaseCommand):
    help = "Sincroniza snapshot de IB"

    def handle(self, *args, **options):
        sync_ib_snapshot()
        self.stdout.write(self.style.SUCCESS("Snapshot sincronizado"))
