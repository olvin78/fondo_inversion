import os
import django
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from applications.funds.models import Fund, ValorDiarioFondo, FundDiversification

# Asegurarse de que exista el fondo 1
try:
    fund = Fund.objects.get(id=1)
except Fund.DoesNotExist:
    fund = Fund.objects.create(name="Fondo Muestra", description="Fondo de prueba", currency="EUR")

print(f"Agregando datos simulados al fondo: {fund.name}")

# Limpiar datos antiguos para evitar duplicados en la misma fecha
ValorDiarioFondo.objects.filter(fund=fund).delete()
FundDiversification.objects.filter(fund=fund).delete()

# 1. Crear Historial de Valores Diarios (NAV) para los últimos 30 días
today = timezone.now().date()
base_capital = 100000.0  # 100k iniciales
nav_base = 10.0

valores_creados = []
for i in range(30, -1, -1):
    fecha = today - timedelta(days=i)
    
    # Simular un crecimiento fluctuante (subidas y bajadas suaves)
    fluctuacion = random.uniform(-0.015, 0.02)  # Entre -1.5% y +2.0%
    base_capital = base_capital * (1 + fluctuacion)
    
    val = ValorDiarioFondo(
        fund=fund,
        fecha=fecha,
        capital_interactive_broker=Decimal(str(base_capital * 0.6)), # 60% en IBKR
        capital_binance=Decimal(str(base_capital * 0.4)),            # 40% en Binance
        participaciones=Decimal("10000.0000") # 10k participaciones fijas
    )
    valores_creados.append(val)

ValorDiarioFondo.objects.bulk_create(valores_creados)
print(f"✅ Se agregaron {len(valores_creados)} valores diarios.")

# 2. Crear Diversificación (Gráfico de Tarta)
diversificaciones = [
    {"name": "Acciones Tecnológicas", "type": "STOCK", "pct": "45.0", "color": "#1e3a8a"},
    {"name": "Bonos Gubernamentales", "type": "BOND", "pct": "25.0", "color": "#3b82f6"},
    {"name": "Criptoactivos (BTC/ETH)", "type": "CRYPTO", "pct": "15.0", "color": "#d97706"},
    {"name": "Materias Primas", "type": "COMMODITY", "pct": "10.0", "color": "#059669"},
    {"name": "Liquidez (Cash)", "type": "CASH", "pct": "5.0", "color": "#94a3b8"},
]

for idx, div in enumerate(diversificaciones):
    FundDiversification.objects.create(
        fund=fund,
        name=div["name"],
        product_type=div["type"],
        percentage=Decimal(div["pct"]),
        color=div["color"],
        order=idx
    )
print(f"✅ Se agregaron {len(diversificaciones)} sectores de diversificación.")

# Actualizar el NAV actual del fondo para que coincida con el último día
ultimo_valor = ValorDiarioFondo.objects.filter(fund=fund).order_by('-fecha').first()
if ultimo_valor:
    fund.nav_actual = ultimo_valor.nav
    fund.save(update_fields=['nav_actual'])

print("🚀 ¡Datos mock agregados con éxito! Refresca la página para ver las gráficas.")
