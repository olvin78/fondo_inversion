# Create your views here.
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Investor, InvestorFund
from applications.funds.models import Fund
from applications.transactions.models import InvestorTransaction
from django.http import HttpResponse


def investor_list(request):
    investors = InvestorFund.objects.all()
    return render(request, "investors/investor_list.html", {"investor_funds": investors})





def investor_detail(request, pk):
    investor = get_object_or_404(Investor, pk=pk)
    positions = investor.fund_positions.select_related("fund")

    capital = sum(
        pos.participations * (pos.fund.nav_actual or Decimal("0.00"))
        for pos in positions
    ) or Decimal("0.00")
    navs = {
        pos.fund.id: pos.fund.nav_actual
        for pos in positions
    }

    return render(request, "investors/investor_detail.html", {
        "investor": investor,
        "positions": positions,
        "capital": capital,
        "navs": navs,
    })

def current_value(self) -> Decimal:
    latest_nav = self.fund.nav_history.first()
    if not latest_nav:
        return Decimal("0.00")
    return self.participations * latest_nav.nav_value





@login_required
def invest(request):
    """
    Invertir en el fondo (de momento: primer fondo).
    Requiere que exista Investor asociado al usuario logueado.
    """
    investor = get_object_or_404(Investor, user=request.user)
    fund = Fund.objects.first()

    if not fund:
        return render(request, "investors/invest.html", {
            "error": "No hay ningún fondo creado todavía."
        })

    if request.method == "POST":
        amount_str = request.POST.get("amount", "").strip()
        try:
            amount = Decimal(amount_str)
        except Exception:
            amount = Decimal("0")

        if amount <= 0:
            return render(request, "investors/invest.html", {
                "fund": fund,
                "error": "El importe debe ser mayor que 0."
            })

        participation_value = fund.participation_value()
        participations = amount / participation_value

        position, _ = InvestorFund.objects.get_or_create(
            investor=investor,
            fund=fund,
            defaults={"participations": Decimal("0")}
        )
        position.participations += participations
        position.save()

        InvestorTransaction.objects.create(
            investor=investor,
            fund=fund,
            amount=amount,
            participations=participations,
            participation_value=participation_value,
            transaction_type="IN"
        )

        # vuelve al detalle del inversor para ver su posición
        return redirect("investors:investor_detail", pk=investor.pk)

    return render(request, "investors/invest.html", {"fund": fund})
