from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from applications.investors.models import Investor, InvestorFund
from applications.transactions.models import InvestorTransaction
from applications.funds.models import Fund


@login_required
def dashboard(request):
    # 1. Usuario → Investor
    investor = Investor.objects.filter(user=request.user).first()

    # 2. Fondo (por ahora uno solo)
    fund = Fund.objects.first()

    # Valores por defecto (SIEMPRE existen)
    capital_invertido = Decimal("0")
    valor_actual = Decimal("0")
    resultado = Decimal("0")
    resultado_pct = Decimal("0")
    fund_position = None
    products = []
    movements = []

    if investor and fund:
        # 3. Posición del inversor en el fondo
        fund_position = InvestorFund.objects.filter(
            investor=investor,
            fund=fund
        ).first()

        # 4. Capital invertido (desde transacciones)
        capital_invertido = sum(
            (t.amount for t in InvestorTransaction.objects.filter(
                investor=investor,
                transaction_type="IN"
            )),
            Decimal("0")
        )

        # 5. Valor actual
        if fund_position:
            participation_value = fund.participation_value()
            valor_actual = fund_position.participations * participation_value

        # 6. Resultado
        resultado = valor_actual - capital_invertido

        if capital_invertido > 0:
            resultado_pct = (resultado / capital_invertido) * 100

        # 7. Activos del fondo
        products = fund.products.all()

        # 8. Últimos movimientos
        movements = InvestorTransaction.objects.filter(
            investor=investor
        ).order_by("-created_at")[:5]

    return render(request, "client/dashboard.html", {
        "capital_invertido": capital_invertido,
        "valor_actual": valor_actual,
        "resultado": resultado,
        "resultado_pct": resultado_pct,
        "fund": fund,
        "fund_position": fund_position,
        "products": products,
        "movements": movements,
    })


@login_required
def invest(request):
    fund = Fund.objects.first()

    return render(request, "client/invest.html", {
        "fund": fund,
    })
