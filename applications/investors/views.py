from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction as db_transaction
from django.db.models import F, Sum, Q, DecimalField, ExpressionWrapper
from django.contrib.auth import get_user_model
from datetime import datetime
from decimal import Decimal

from .models import Investor, InvestorFund, Notification, InvestorFundTransaction
from applications.funds.models import Fund, FundTrade, FundCapitalSnapshot, FundPosition
from applications.investors.services.participations import buy_participations, sell_participations
from .permissions import can_access_investor

User = get_user_model()

def is_staff(user):
    return user.is_staff


@staff_member_required
def investor_list(request):
    investors = Investor.objects.select_related("user")
    return render(
        request,
        "investors/investor_list.html",
        {"investor_funds": investors},
    )


@login_required
def investor_detail(request, pk):
    investor = get_object_or_404(Investor, pk=pk)
    if not can_access_investor(request.user, investor):
        raise PermissionDenied
    positions = investor.fund_positions.select_related("fund")

    current_value = sum(
        pos.participations * (pos.fund.nav_actual or Decimal("0.00"))
        for pos in positions
    ) or Decimal("0.00")

    total_invested = sum(
        pos.participations * (pos.average_price or Decimal("0.00"))
        for pos in positions
    ) or Decimal("0.00")

    result = current_value - total_invested

    # Recuperar el historial completo de transacciones de este inversor
    transactions = investor.fund_transactions.select_related("fund").order_by("-created_at")

    return render(request, "investors/investor_detail.html", {
        "investor": investor,
        "positions": positions,
        "total_invested": total_invested,
        "current_value": current_value,
        "result": result,
        "transactions": transactions,
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
    try:
        investor = Investor.objects.get(user=request.user)
    except Investor.DoesNotExist:
        raise PermissionDenied
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


        InvestorFundTransaction.objects.create(
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
    selected_investor_id = request.GET.get("investor")
    
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
        return redirect("investors:investor_detail", pk=investor_id)

    funds = Fund.objects.all()
    investors = Investor.objects.select_related("user")

    return render(request, "investors/buy_participations.html", {
        "investors": investors,
        "funds": funds,
        "selected_investor_id": selected_investor_id,
    })

@staff_member_required
def sell_participations_view(request):
    if request.method == "POST":
        investor_id = request.POST.get("investor")
        participations = request.POST.get("participations")
        nav_price = request.POST.get("nav_price")

        if not investor_id:
            messages.error(request, "Debe seleccionar un inversor válido.")
            return redirect("investors:sell_participations")

        if not participations or not nav_price:
            messages.error(request, "Debe indicar participaciones y NAV válidos.")
            return redirect("investors:sell_participations")

        investor = get_object_or_404(Investor, pk=investor_id)
        position = investor.fund_positions.first()

        if not position:
            messages.error(request, "El inversor no tiene posiciones activas.")
            return redirect("investors:sell_participations")

        try:
            sell_participations(
                investor=investor,
                fund=position.fund,
                participations=Decimal(participations),
                nav_price=Decimal(nav_price),
                executed_by=request.user.username,
            )
            messages.success(request, "Venta realizada correctamente.")
            return redirect("investors:investor_detail", pk=investor_id)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect("investors:sell_participations")

    investors = Investor.objects.filter(fund_positions__participations__gt=0).distinct().select_related("user")
    funds = Fund.objects.all()

    return render(request, "investors/sell_participations.html", {
        "investors": investors,
        "funds": funds,
    })


@login_required
def notification_list(request):
    investor_id = request.GET.get("investor")

    investor = None
    notifications = Notification.objects.none()

    if investor_id:
        investor = get_object_or_404(Investor, id=investor_id)
        if not can_access_investor(request.user, investor):
            raise PermissionDenied

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


@staff_member_required
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
    if investor is None:
        if not request.user.is_staff and not request.user.is_superuser:
            raise PermissionDenied
    elif not can_access_investor(request.user, investor):
        raise PermissionDenied
    position = investor.get_first_fund_position() if investor else None

    if notification.template == "MONTHLY":
        capital_invertido = position.participations * position.average_price if position else Decimal("0")
        capital_actual = position.current_value() if position else Decimal("0")
        resultado = capital_actual - capital_invertido
        porcentaje = (resultado / capital_invertido * 100) if (position and capital_invertido > 0) else 0
        fund_transactions = investor.fund_transactions.all().order_by("-created_at")[:10]

        notification.content = render_to_string(
            "investors/notifications_monthly.html",
            {
                "investor": investor,
                "fund": position.fund if position else None,
                "capital_invertido": capital_invertido,
                "capital_actual": capital_actual,
                "resultado": resultado,
                "porcentaje": porcentaje,
                "participaciones": position.participations if position else 0,
                "fund_transactions": fund_transactions,
                "is_preview": False,
            }
        )

    context = {
        "notification": notification,
        "investor": investor,
        "fund": position.fund if position else None,
        "participations": position.participations if position else 0,
        "created_at": notification.created_at,
    }

    return render(request, "investors/notifications_detail.html", context)


@staff_member_required
def notification_create_monthly(request):
    investor_id = request.GET.get("investor") or request.POST.get("investor_id")
    investor = get_object_or_404(Investor, id=investor_id)

    position = investor.get_first_fund_position()
    fund = position.fund if position else None

    capital_invertido = position.participations * position.average_price if position else Decimal("0")
    capital_actual = position.current_value() if position else Decimal("0")
    resultado = capital_actual - capital_invertido
    porcentaje = (resultado / capital_invertido * 100) if (position and capital_invertido > 0) else 0

    fund_transactions = investor.fund_transactions.all().order_by("-created_at")[:10]

    context = {
        "investor": investor,
        "fund": fund,
        "capital_invertido": capital_invertido,
        "capital_actual": capital_actual,
        "resultado": resultado,
        "porcentaje": porcentaje,
        "participaciones": position.participations if position else 0,
        "fund_transactions": fund_transactions,
        "is_preview": True,
    }

    if request.method == "POST" and request.POST.get("action") == "save":
        html = render_to_string("investors/notifications_monthly.html", {**context, "is_preview": False})
        
        notification = Notification.objects.create(
            investor=investor,
            title="Informe mensual de participaciones",
            template="MONTHLY",
            content=html,
            status="SENT",
        )
        return redirect("investors:notification_detail", notification.id)

    return render(request, "investors/notifications_preview.html", context)


@staff_member_required
def notification_create_informative(request):
    investor = get_object_or_404(
        Investor, id=request.GET.get("investor") or request.POST.get("investor_id")
    )

    latest_tx = InvestorFundTransaction.objects.filter(investor=investor).order_by("-created_at").first()

    context = {
        "investor": investor,
        "fund": latest_tx.fund if latest_tx else None,
        "importe_aportado": latest_tx.amount if latest_tx else 0,
        "capital_invertido": (latest_tx.amount * Decimal("0.99")) if latest_tx else 0,
        "nav": latest_tx.nav_price if latest_tx else Decimal("10.0000"),
        "participaciones": latest_tx.participations if latest_tx else 0,
    }

    if request.method == "POST" and request.POST.get("action") == "save":
        html = render_to_string(
            "investors/report_informative.html",
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


@login_required
def dashboard(request):
    inversor = getattr(request.user, "investor_profile", None)
    if not inversor:
        return redirect("investors:investor_list")

    positions = InvestorFund.objects.filter(investor=inversor).select_related("fund")
    
    # Transacciones completas del inversor para su Dashboard
    transactions = InvestorFundTransaction.objects.filter(
        investor=inversor
    ).select_related("fund").order_by("-created_at")

    dashboard_funds = []
    for position in positions:
        fund = position.fund
        snapshot = FundCapitalSnapshot.objects.filter(fund=fund).order_by("-date").first()

        capital_total_fondo = snapshot.total_capital if snapshot else Decimal("0")
        nav_actual = fund.nav_actual or Decimal("0")
        date_update = snapshot.date if snapshot else None

        capital_usuario = (position.participations * nav_actual).quantize(Decimal("0.01"))

        # Cálculo de Rendimiento (PnL y ROI)
        avg_price = position.average_price or Decimal("0")
        cost_basis = (position.participations * avg_price).quantize(Decimal("0.01"))
        pnl = (capital_usuario - cost_basis).quantize(Decimal("0.01"))
        roi = (pnl / cost_basis * 100) if cost_basis > 0 else Decimal("0")

        dashboard_funds.append({
            "fund": fund,
            "participations": position.participations,
            "nav_actual": nav_actual.quantize(Decimal("0.0001")),
            "capital_usuario": capital_usuario,
            "capital_total_fondo": capital_total_fondo.quantize(Decimal("0.01")),
            "date_update": date_update,
            "pnl": pnl,
            "roi": roi
        })

    # CÁLCULO DE COMISIONES TOTALES RECIBIDAS (Para el Dashboard del Gestor)
    total_comisiones_recibidas = InvestorFundTransaction.objects.filter(
        investor=inversor,
        reference__icontains="Comisión"
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    total_portfolio_value = sum(item["capital_usuario"] for item in dashboard_funds)

    return render(
        request,
        "investors/dashboard.html",
        {
            "dashboard_funds": dashboard_funds,
            "transactions": transactions,
            "total_portfolio_value": total_portfolio_value,
            "total_comisiones_recibidas": total_comisiones_recibidas,
            "inversor": inversor
        }
    )

@staff_member_required
def transaction_list_full(request):
    """Listado total de operaciones con filtrado avanzado"""
    q = request.GET.get("q", "")
    transactions = InvestorFundTransaction.objects.all().select_related("investor__user", "fund").order_by("-created_at")
    
    if q:
        transactions = transactions.filter(
            Q(investor__user__first_name__icontains=q) |
            Q(investor__user__last_name__icontains=q) |
            Q(investor__document_id__icontains=q) |
            Q(fund__name__icontains=q) |
            Q(reference__icontains=q)
        )

    return render(request, "investors/transaction_list.html", {
        "transactions": transactions,
        "q": q
    })


@staff_member_required
def dashboard_gestor(request):
    funds = Fund.objects.all()
    dashboard_data = []

    for fund in funds:
        snapshot = FundCapitalSnapshot.objects.filter(fund=fund).order_by("-date").first()
        capital_total = snapshot.total_capital if snapshot else Decimal("0.00")
        total_participations = fund.total_participations
        nav_actual = fund.nav_actual or Decimal("0.00")
        aum = fund.aum

        dashboard_data.append({
            "fund": fund,
            "total_participations": total_participations,
            "nav_actual": nav_actual.quantize(Decimal("0.0001")),
            "capital_total": capital_total.quantize(Decimal("0.01")),
            "aum": aum.quantize(Decimal("0.01")),
            "investors_count": fund.investors.count(),
            "fund_positions": FundPosition.objects.filter(fund=fund).select_related("product"),
            "investor_transactions": InvestorFundTransaction.objects.filter(fund=fund).select_related("investor", "investor__user").order_by("-created_at"),
            "fund_trades": FundTrade.objects.filter(fund=fund).select_related("product").order_by("-created_at"),
        })

    all_fund_trades = FundTrade.objects.all().select_related("fund", "product").order_by("-created_at")[:10]

    return render(
        request,
        "investors/dashboard-gestor.html",
        {
            "dashboard_data": dashboard_data,
            "investors": Investor.objects.select_related("user"),
            "funds": funds,
            "all_fund_trades": all_fund_trades,
        }
    )


@staff_member_required
def investor_create(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username", email)
        password = request.POST.get("password")
        document_id = request.POST.get("document_id")
        phone = request.POST.get("phone")
        risk_level = request.POST.get("risk_level", "MEDIUM")
        birth_date = request.POST.get("birth_date") or None

        try:
            with db_transaction.atomic():
                user = User.objects.create_user(
                    username=username, email=email, password=password,
                    first_name=first_name, last_name=last_name
                )
                Investor.objects.create(
                    user=user, document_id=document_id, phone=phone,
                    risk_level=risk_level, birth_date=birth_date
                )
            messages.success(request, f"Inversor {first_name} {last_name} creado con éxito.")
            return redirect("investors:investor_list")
        except Exception as e:
            messages.error(request, f"Error al crear: {str(e)}")

    return render(request, "investors/investor_form.html", {
        "risk_levels": Investor.RISK_LEVELS
    })
