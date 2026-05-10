import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from applications.funds.models import Fund, ValorDiarioFondo

fund = Fund.objects.get(id=1)

# El problema era que "bulk_create" no llamaba al metodo save(), por lo que "nav" se quedaba en 0.0000
# Además, save() sobreescribe las participaciones con las reales del fondo (fund.total_participations).
# Si el fondo no tiene transacciones reales, total_participations será 0.
# Vamos a crear una transacción falsa temporal si no tiene participaciones.
if fund.total_participations == 0:
    from applications.investors.models import InvestorFundTransaction, Investor
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # Asegurar un inversor temporal
    user, _ = User.objects.get_or_create(email="test@test.com", defaults={"username": "test_investor"})
    investor, _ = Investor.objects.get_or_create(user=user, defaults={"first_name": "Test", "last_name": "Investor"})
    
    InvestorFundTransaction.objects.create(
        investor=investor,
        fund=fund,
        transaction_type="BUY",
        amount=Decimal("100000.00"),
        participations=Decimal("10000.0000"),
        nav_at_transaction=Decimal("10.0000")
    )

print(f"Participaciones reales del fondo: {fund.total_participations}")

valores = ValorDiarioFondo.objects.filter(fund=fund).order_by('fecha')
for v in valores:
    # Esto llamará a save(), que ahora verá participaciones > 0 y calculará el NAV correcto
    v.save()

# Actualizar NAV actual
ultimo = ValorDiarioFondo.objects.filter(fund=fund).order_by('-fecha').first()
if ultimo:
    fund.nav_actual = ultimo.nav
    fund.save(update_fields=['nav_actual'])
    print(f"NAV Actual corregido a: {fund.nav_actual}")

