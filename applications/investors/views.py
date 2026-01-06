# Create your views here.
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.template.loader import render_to_string

from .models import Investor, InvestorFund, Notification
from applications.funds.models import Fund
from applications.transactions.models import InvestorTransaction
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

from applications.investors.services.participations import buy_participations, sell_participations

from datetime import datetime


def investor_list(request):
    investors = Investor.objects.select_related("user")
    return render(
        request,
        "investors/investor_list.html",
        {"investor_funds": investors},
    )


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

@staff_member_required
def buy_participations_view(request):
    if request.method == "POST":
        investor_id = request.POST.get("investor")
        fund_id = request.POST.get("fund")
        amount = request.POST.get("amount")
        nav_price = request.POST.get("nav_price")

        investor = Investor.objects.get(pk=investor_id)
        fund = Fund.objects.get(pk=fund_id)

        buy_participations(
            investor=investor,
            fund=fund,
            amount=Decimal(amount),
            nav_price=Decimal(nav_price),
            executed_by=request.user.username,
        )

        messages.success(request, "Compra de participaciones realizada correctamente.")
        return redirect("client:dashboard")

    return render(request, "investors/buy_participations.html", {
        "investors": Investor.objects.select_related("user"),
        "funds": Fund.objects.all(),
    })

@staff_member_required
def sell_participations_view(request):
    if request.method == "POST":
        position_id = request.POST.get("position")
        participations = request.POST.get("participations")
        nav_price = request.POST.get("nav_price")

        position = InvestorFund.objects.select_related("investor", "fund").get(
            pk=position_id
        )

        try:
            sell_participations(
                investor=position.investor,
                fund=position.fund,
                participations=Decimal(participations),
                nav_price=Decimal(nav_price),
                executed_by=request.user.username,
            )
            messages.success(request, "Venta realizada correctamente.")
            return redirect("client:dashboard")

        except ValueError as e:
            messages.error(request, str(e))

    positions = InvestorFund.objects.filter(participations__gt=0)

    return render(request, "investors/sell_participations.html", {
        "positions": positions,
    })


@login_required
def notification_list(request):
    investor_id = request.GET.get("investor")

    investor = None
    notifications = Notification.objects.none()

    if investor_id:
        investor = get_object_or_404(Investor, id=investor_id)

        notifications = Notification.objects.filter(
            investor=investor
        ).order_by("-created_at")

    return render(
        request,
        "investors/notification_list.html",
        {
            "notifications": notifications,
            "investor": investor,
        }
    )


@login_required
def notification_create(request):
    investor_id = request.GET.get("investor") or request.POST.get("investor_id")

    if not investor_id:
        return redirect("investors:investor_list")

    if request.method == "POST":
        template_type = request.POST.get("template_type")

        if template_type == "INFO":
            return redirect(
                f"{reverse('investors:notification_create_info')}?investor={investor_id}"
            )

        if template_type == "MONTHLY_REPORT":
            return redirect(
                f"{reverse('investors:notification_create_monthly')}?investor={investor_id}"
            )

    return render(
        request,
        "investors/notifications_create.html",
        {
            "investor_id": investor_id,
        }
    )




@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk)

    investor = notification.investor
    position = investor.get_first_fund_position() if investor else None

    context = {
        "notification": notification,
        "investor": investor,
        "fund": position.fund if position else None,
        "participations": position.participations if position else 0,
        "created_at": notification.created_at,
    }

    return render(
        request,
        "investors/notifications_detail.html",
        context
    )


@login_required
def notification_create_monthly(request):
    investor_id = request.GET.get("investor") or request.POST.get("investor_id")
    investor = get_object_or_404(Investor, id=investor_id)

    position = investor.get_first_fund_position()
    fund = position.fund if position else None

    # 👉 AQUÍ VAN TUS CÁLCULOS REALES
    capital_invertido = ...
    capital_actual = ...
    resultado = capital_actual - capital_invertido
    porcentaje = (resultado / capital_invertido * 100) if capital_invertido else 0

    html = render_to_string(
        "investors/notifications_monthly.html",
        {
            "investor": investor,
            "fund": fund,
            "capital_invertido": capital_invertido,
            "capital_actual": capital_actual,
            "resultado": resultado,
            "porcentaje": porcentaje,
            "participaciones": position.participations if position else 0,
        }
    )

    notification = Notification.objects.create(
        investor=investor,
        title="Informe mensual de participaciones",
        template="MONTHLY",
        content=html,
        status="SENT",
    )

    return redirect(
        "investors:notification_detail",
        notification.id
    )


@login_required
def notification_create_informative(request):
    investor = get_object_or_404(
        Investor, id=request.GET.get("investor") or request.POST.get("investor_id")
    )

    position = investor.get_first_fund_position()
    fund = position.fund if position else None

    context = {
        "investor": investor,
        "fund": fund,
        "participaciones": position.participations if position else 0,
    }

    if request.method == "POST" and request.POST.get("action") == "save":
        html = render_to_string(
            "investors/_sheet_informative.html",
            context
        )

        notification = Notification.objects.create(
            investor=investor,
            title="Documento informativo de bienvenida",
            template="INFO",
            content=html,
            status="SENT",
        )

        return redirect("investors:notification_detail", notification.id)

    return render(
        request,
        "investors/notification_create_Informative.html",
        context
    )
