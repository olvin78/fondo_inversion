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
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone

from .models import Investor, InvestorFund, Notification, InvestorFundTransaction
from applications.funds.models import Fund, FundTrade, ValorDiarioFondo, FundPosition
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
    positions_qs = investor.fund_positions.select_related("fund")
    positions_by_fund = {pos.fund_id: pos for pos in positions_qs}

    transactions_qs = investor.fund_transactions.select_related("fund").order_by("created_at")

    tx_stats = {}
    for tx in transactions_qs:
        stats = tx_stats.setdefault(tx.fund_id, {
            "fund": tx.fund,
            "participations": Decimal("0"),
            "invested": Decimal("0"),
        })
        sign = Decimal("1") if tx.transaction_type == InvestorFundTransaction.BUY else Decimal("-1")
        stats["participations"] += sign * tx.participations
        stats["invested"] += sign * tx.amount

    positions_data = []
    current_value = Decimal("0.00")
    total_invested = Decimal("0.00")
    nav_deviation_detected = False
    nav_deviation_details = []

    for fund_id, stats in tx_stats.items():
        fund = stats["fund"]
        valor = fund.valores_diarios.first()
        nav = valor.nav if valor else Decimal("0")

        participations = stats["participations"]
        invested = stats["invested"]
        average_price = (invested / participations) if participations > 0 else Decimal("0")

        patrimonio = (participations * nav).quantize(Decimal("0.01"))
        current_value += patrimonio
        total_invested += invested

        stored_pos = positions_by_fund.get(fund_id)
        stored_participations = stored_pos.participations if stored_pos else Decimal("0")
        stored_patrimonio = (stored_participations * nav).quantize(Decimal("0.01"))
        if abs(patrimonio - stored_patrimonio) > Decimal("0.01"):
            nav_deviation_detected = True
            nav_deviation_details.append({
                "fund": fund,
                "expected": patrimonio,
                "actual": stored_patrimonio,
            })

        positions_data.append({
            "fund": fund,
            "participations": participations,
            "average_price": average_price,
            "nav": nav,
            "current_value": patrimonio,
        })

    result = current_value - total_invested

    transactions = transactions_qs.order_by("-created_at")

    # Serie de evolución (últimos 30 días)
    funds = [stats["fund"] for stats in tx_stats.values()]
    if funds:
        start_date = timezone.now().date() - timedelta(days=30)
        valores_qs = ValorDiarioFondo.objects.filter(
            fund__in=funds,
            fecha__gte=start_date,
        ).order_by("fecha")
    else:
        valores_qs = ValorDiarioFondo.objects.none()

    fund_valores = {}
    fechas_set = set()
    for valor in valores_qs:
        fund_valores.setdefault(valor.fund_id, {})[valor.fecha] = valor.nav
        fechas_set.add(valor.fecha)

    fund_txs = {}
    for tx in transactions_qs:
        fund_txs.setdefault(tx.fund_id, []).append({
            "date": tx.created_at.date(),
            "delta": tx.participations if tx.transaction_type == InvestorFundTransaction.BUY else -tx.participations,
        })

    fechas_sorted = sorted(fechas_set)
    totals_by_date = {fecha: Decimal("0") for fecha in fechas_sorted}

    for fund_id, tx_list in fund_txs.items():
        tx_list_sorted = sorted(tx_list, key=lambda x: x["date"])
        idx = 0
        acumulado = Decimal("0")
        for fecha in fechas_sorted:
            while idx < len(tx_list_sorted) and tx_list_sorted[idx]["date"] <= fecha:
                acumulado += tx_list_sorted[idx]["delta"]
                idx += 1
            nav = fund_valores.get(fund_id, {}).get(fecha)
            if nav is None:
                continue
            totals_by_date[fecha] += (acumulado * nav)

    chart_labels = [fecha.strftime("%d/%m") for fecha in fechas_sorted]
    chart_data = [totals_by_date[fecha].quantize(Decimal("0.01")) for fecha in fechas_sorted]

    return render(request, "investors/investor_detail.html", {
        "investor": investor,
        "positions": positions_data,
        "total_invested": total_invested,
        "current_value": current_value,
        "result": result,
        "transactions": transactions,
        "nav_deviation_detected": nav_deviation_detected,
        "nav_deviation_details": nav_deviation_details,
        "evolution_labels": chart_labels,
        "evolution_data": chart_data,
    })

def current_value(self) -> Decimal:
    latest_valor = self.fund.valores_diarios.order_by("-fecha").first()
    if not latest_valor:
        return Decimal("0.00")
    return self.participations * latest_valor.nav

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
        investor_display_name = investor.user.get_full_name() or investor.user.username
        positions = investor.fund_positions.select_related("fund")
        funds_report = []
        total_invertido = Decimal("0")
        total_actual = Decimal("0")
        total_participaciones = Decimal("0")
        report_date = None

        for pos in positions:
            fund = pos.fund
            valor = fund.valores_diarios.first()
            nav = valor.nav if valor else Decimal("0")
            if valor and (report_date is None or valor.fecha > report_date):
                report_date = valor.fecha

            fund_transactions = investor.fund_transactions.filter(
                fund=fund
            ).order_by("created_at")

            participaciones = Decimal("0")
            capital_invertido = Decimal("0")
            for tx in fund_transactions:
                sign = Decimal("1") if tx.transaction_type == InvestorFundTransaction.BUY else Decimal("-1")
                participaciones += sign * tx.participations
                capital_invertido += sign * tx.amount

            capital_actual = (participaciones * nav).quantize(Decimal("0.01"))
            resultado = capital_actual - capital_invertido
            porcentaje = (resultado / capital_invertido * 100) if capital_invertido > 0 else Decimal("0")

            total_invertido += capital_invertido
            total_actual += capital_actual
            total_participaciones += participaciones

            funds_report.append({
                "fund": fund,
                "participaciones": participaciones,
                "nav": nav,
                "capital_invertido": capital_invertido,
                "capital_actual": capital_actual,
                "resultado": resultado,
                "porcentaje": porcentaje,
            })

        if report_date is None:
            report_date = notification.created_at.date()
        report_date_label = report_date.strftime("%d/%m/%Y")

        total_resultado = total_actual - total_invertido
        total_porcentaje = (total_resultado / total_invertido * 100) if total_invertido > 0 else Decimal("0")
        fund_transactions = investor.fund_transactions.all().order_by("-created_at")[:10]

        notification.content = render_to_string(
            "investors/notifications_monthly.html",
            {
                "investor": investor,
                "investor_display_name": investor_display_name,
                "funds_report": funds_report,
                "capital_invertido": total_invertido,
                "capital_actual": total_actual,
                "resultado": total_resultado,
                "porcentaje": total_porcentaje,
                "participaciones": total_participaciones,
                "report_date": report_date,
                "report_date_label": report_date_label,
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
    investor_display_name = investor.user.get_full_name() or investor.user.username

    position = investor.get_first_fund_position()
    positions = investor.fund_positions.select_related("fund")
    funds_report = []
    total_invertido = Decimal("0")
    total_actual = Decimal("0")
    total_participaciones = Decimal("0")
    report_date = None

    for pos in positions:
        fund = pos.fund
        valor = fund.valores_diarios.first()
        nav = valor.nav if valor else Decimal("0")
        if valor and (report_date is None or valor.fecha > report_date):
            report_date = valor.fecha

        fund_transactions = investor.fund_transactions.filter(
            fund=fund
        ).order_by("created_at")

        participaciones = Decimal("0")
        capital_invertido = Decimal("0")
        for tx in fund_transactions:
            sign = Decimal("1") if tx.transaction_type == InvestorFundTransaction.BUY else Decimal("-1")
            participaciones += sign * tx.participations
            capital_invertido += sign * tx.amount

        capital_actual = (participaciones * nav).quantize(Decimal("0.01"))
        resultado = capital_actual - capital_invertido
        porcentaje = (resultado / capital_invertido * 100) if capital_invertido > 0 else Decimal("0")

        total_invertido += capital_invertido
        total_actual += capital_actual
        total_participaciones += participaciones

        funds_report.append({
            "fund": fund,
            "participaciones": participaciones,
            "nav": nav,
            "capital_invertido": capital_invertido,
            "capital_actual": capital_actual,
            "resultado": resultado,
            "porcentaje": porcentaje,
        })

    if report_date is None:
        report_date = timezone.now().date()
    report_date_label = report_date.strftime("%d/%m/%Y")

    total_resultado = total_actual - total_invertido
    total_porcentaje = (total_resultado / total_invertido * 100) if total_invertido > 0 else Decimal("0")
    fund_transactions = investor.fund_transactions.all().order_by("-created_at")[:10]

    context = {
        "investor": investor,
        "investor_display_name": investor_display_name,
        "funds_report": funds_report,
        "capital_invertido": total_invertido,
        "capital_actual": total_actual,
        "resultado": total_resultado,
        "porcentaje": total_porcentaje,
        "participaciones": total_participaciones,
        "report_date": report_date,
        "report_date_label": report_date_label,
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
        valor_diario = ValorDiarioFondo.objects.filter(fund=fund).order_by("-fecha").first()

        capital_total_fondo = valor_diario.valor_total if valor_diario else Decimal("0")
        nav_actual = valor_diario.nav if valor_diario else fund.current_nav()
        date_update = valor_diario.fecha if valor_diario else None

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
        valor_diario = ValorDiarioFondo.objects.filter(fund=fund).order_by("-fecha").first()
        capital_total = valor_diario.valor_total if valor_diario else Decimal("0.00")
        total_participations = fund.total_participations
        nav_actual = valor_diario.nav if valor_diario else fund.current_nav()
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
