import os
import django
import sys
from decimal import Decimal
from datetime import timedelta

# Add current directory to path
sys.path.append(os.getcwd())

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from applications.funds.models import Fund, FundRiskLevel, FundNAV, FundDiversification, FundTrade, FundPosition
from applications.products.models import Product, Currency, AssetClass, Sector, Country, Region
from applications.investors.models import Investor, InvestorFund, InvestorFundTransaction

def populate():
    print("🚀 Iniciando carga de datos de prueba...")
    
    # 1. Región y Países
    region_world, _ = Region.objects.get_or_create(code="GLOBAL", name="Mercado Global")
    country_us, _ = Country.objects.get_or_create(iso_code="US", defaults={"name": "USA", "region": region_world, "currency": "USD"})
    country_es, _ = Country.objects.get_or_create(iso_code="ES", defaults={"name": "España", "region": region_world, "currency": "EUR"})
    
    # 2. Divisas
    curr_eur, _ = Currency.objects.get_or_create(code="EUR", defaults={"name": "Euro", "symbol": "€"})
    curr_usd, _ = Currency.objects.get_or_create(code="USD", defaults={"name": "Dólar", "symbol": "$"})
    
    # 3. Categorías de Activos
    ac_equity, _ = AssetClass.objects.get_or_create(code="EQUITY", defaults={"name": "Renta Variable"})
    ac_crypto, _ = AssetClass.objects.get_or_create(code="CRYPTO", defaults={"name": "Criptoactivos"})
    
    # 4. Sectores
    sec_tech, _ = Sector.objects.get_or_create(code="TECH", defaults={"name": "Tecnología"})
    sec_fin, _ = Sector.objects.get_or_create(code="FIN", defaults={"name": "Finanzas"})

    # 5. Niveles de Riesgo
    risk_low, _ = FundRiskLevel.objects.get_or_create(name="Conservador", defaults={"level": 1, "description": "Baja volatilidad, preservación de capital."})
    risk_mid, _ = FundRiskLevel.objects.get_or_create(name="Equilibrado", defaults={"level": 3, "description": "Balance entre renta fija y variable."})
    risk_high, _ = FundRiskLevel.objects.get_or_create(name="Agresivo", defaults={"level": 5, "description": "Alta exposición a renta variable y activos volátiles."})

    # 6. Productos (Acciones)
    p1, _ = Product.objects.get_or_create(
        name="Apple Inc.", 
        defaults={
            "asset_class": ac_equity, 
            "ticker": "AAPL", 
            "country": country_us, 
            "sector": sec_tech, 
            "currency": curr_usd
        }
    )
    p2, _ = Product.objects.get_or_create(
        name="Microsoft Corp.", 
        defaults={
            "asset_class": ac_equity, 
            "ticker": "MSFT", 
            "country": country_us, 
            "sector": sec_tech, 
            "currency": curr_usd
        }
    )
    p3, _ = Product.objects.get_or_create(
        name="Bitcoin Core", 
        defaults={
            "asset_class": ac_crypto, 
            "ticker": "BTC", 
            "currency": curr_usd
        }
    )

    # 7. Fondos
    f1, _ = Fund.objects.get_or_create(
        name="Fondo Tech Global Alpha",
        defaults={
            "manager": "Elena Rodriguez",
            "currency": "EUR",
            "risk_level": risk_mid,
            "description": "Fondo centrado en el crecimiento sostenido de empresas tecnológicas líderes.",
            "nav_actual": Decimal("132.45"),
            "participations": Decimal("0.0000")
        }
    )

    f2, _ = Fund.objects.get_or_create(
        name="Estrategia Digital Bitcoin",
        defaults={
            "manager": "Roberto Garcia",
            "currency": "EUR",
            "risk_level": risk_high,
            "description": "Fondo de alta convicción en la adopción institucional de criptoactivos.",
            "nav_actual": Decimal("95.80"),
            "participations": Decimal("0.0000")
        }
    )

    # 8. Diversificación (Gráficos)
    FundDiversification.objects.update_or_create(fund=f1, product_type="STOCK", defaults={"name": "Acciones Tech", "percentage": Decimal("75.00"), "color": "#3b82f6"})
    FundDiversification.objects.update_or_create(fund=f1, product_type="CASH", defaults={"name": "Liquidez", "percentage": Decimal("25.00"), "color": "#94a3b8"})
    
    FundDiversification.objects.update_or_create(fund=f2, product_type="CRYPTO", defaults={"name": "Criptodivisas", "percentage": Decimal("90.00"), "color": "#f59e0b"})
    FundDiversification.objects.update_or_create(fund=f2, product_type="CASH", defaults={"name": "Liquidez", "percentage": Decimal("10.00"), "color": "#94a3b8"})

    # 9. Histórico de NAV (Gráficos rendimiento)
    today = timezone.now().date()
    for i in range(15):
        day = today - timedelta(days=15-i)
        # Fondo 1 subiendo suave
        nav1 = Decimal("130.00") + (Decimal(str(i)) * Decimal("0.25"))
        FundNAV.objects.update_or_create(fund=f1, date=day, defaults={"nav_value": nav1})
        # Fondo 2 volátil
        nav2 = Decimal("90.00") + (Decimal(str(i)) * Decimal("0.50")) if i % 2 == 0 else Decimal("90.00") - (Decimal(str(i)) * Decimal("0.10"))
        FundNAV.objects.update_or_create(fund=f2, date=day, defaults={"nav_value": nav2})

    # 10. Operaciones de Mercado (Fund Trades)
    FundTrade.objects.get_or_create(fund=f1, product=p1, transaction_type="BUY", defaults={"quantity": Decimal("250.00"), "price": Decimal("175.40")})
    FundTrade.objects.get_or_create(fund=f1, product=p2, transaction_type="BUY", defaults={"quantity": Decimal("150.00"), "price": Decimal("320.10")})
    FundTrade.objects.get_or_create(fund=f2, product=p3, transaction_type="BUY", defaults={"quantity": Decimal("1.25"), "price": Decimal("62500.00")})

    # 11. Usuarios e Inversores
    # Usuario 1
    u1, _ = User.objects.get_or_create(username="elena_inversora", defaults={"first_name": "Elena", "last_name": "Gomez", "email": "elena@fondocapital.com"})
    if u1.pk is None or not u1.has_usable_password():
        u1.set_password("pass1234")
        u1.save()
    i1, _ = Investor.objects.get_or_create(user=u1, defaults={"document_id": "12345678W"})

    # Usuario 2
    u2, _ = User.objects.get_or_create(username="roberto_patrimonio", defaults={"first_name": "Roberto", "last_name": "Sanz", "email": "roberto@fondocapital.com"})
    if u2.pk is None or not u2.has_usable_password():
        u2.set_password("pass1234")
        u2.save()
    i2, _ = Investor.objects.get_or_create(user=u2, defaults={"document_id": "87654321Q"})

    # 12. Transacciones de Inversores (esto crea automáticamente las participaciones via el método save de InvestorFundTransaction)
    InvestorFundTransaction.objects.get_or_create(
        investor=i1, 
        fund=f1, 
        transaction_type="BUY", 
        participations=Decimal("450"), 
        defaults={"nav_price": Decimal("130.00")}
    )
    
    InvestorFundTransaction.objects.get_or_create(
        investor=i2, 
        fund=f1, 
        transaction_type="BUY", 
        participations=Decimal("120"), 
        defaults={"nav_price": Decimal("130.00")}
    )
    
    InvestorFundTransaction.objects.get_or_create(
        investor=i2, 
        fund=f2, 
        transaction_type="BUY", 
        participations=Decimal("350"), 
        defaults={"nav_price": Decimal("90.00")}
    )

    print("✅ Carga de datos de prueba finalizada con éxito.")

if __name__ == "__main__":
    populate()
