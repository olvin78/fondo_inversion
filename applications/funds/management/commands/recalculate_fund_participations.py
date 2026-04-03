from django.core.management.base import BaseCommand
from applications.funds.models import Fund
from decimal import Decimal

class Command(BaseCommand):
    help = "Recalcula y sincroniza el campo participations de todos los fondos basado en transacciones reales de inversores."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra los cambios sin aplicarlos en la base de datos.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        funds = Fund.objects.all()
        
        self.stdout.write(self.style.MIGRATE_HEADING("Iniciando recalculo de participaciones de fondos..."))
        
        for fund in funds:
            old_value = fund.participations
            new_value = fund.total_participations
            
            if old_value != new_value:
                diff = new_value - old_value
                self.stdout.write(
                    self.style.WARNING(
                        f"Fondo '{fund.name}': Desincronizado. Stored: {old_value} | Calculated: {new_value} (Diff: {diff})"
                    )
                )
                
                if not dry_run:
                    fund.participations = new_value
                    fund.save(update_fields=["participations"])
                    self.stdout.write(self.style.SUCCESS(f"  --> Sincronizado correctamente."))
                else:
                    self.stdout.write(self.style.NOTICE(f"  --> [DRY RUN] No se ha aplicado el cambio."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Fondo '{fund.name}' ya está sincronizado ({new_value})."))
        
        self.stdout.write(self.style.MIGRATE_SUCCESS("Recalculo finalizado."))
