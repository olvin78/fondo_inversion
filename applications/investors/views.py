from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction as db_transaction
from django.http import JsonResponse
from django.db.models import F, Sum, Q, DecimalField, ExpressionWrapper
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from core.utils.decimal import round4

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
            "participations": Decimal("0.0000"),
            "invested": Decimal("0.0000"),
        })
        if tx.transaction_type in (InvestorFundTransaction.BUY, InvestorFundTransaction.BONUS):
            sign = Decimal("1")
        elif tx.transaction_type == InvestorFundTransaction.SELL:
            sign = Decimal("-1")
        else:
            sign = Decimal("0")
        stats["participations"] = round4(stats["participations"] + (sign * tx.participations))
        stats["invested"] = round4(stats["invested"] + (sign * tx.amount))

    positions_data = []
    current_value = Decimal("0.0000")
    total_invested = Decimal("0.0000")
    nav_deviation_detected = False
    nav_deviation_details = []

    for fund_id, stats in tx_stats.items():
        fund = stats["fund"]
        valor = fund.valores_diarios.first()
        nav = valor.nav if valor else Decimal("0.0000")

        participations = stats["participations"]
        invested = stats["invested"]
        average_price = round4(invested / participations) if participations > 0 else Decimal("0.0000")

        patrimonio = round4(participations * nav)
        current_value = round4(current_value + patrimonio)
        total_invested = round4(total_invested + invested)

        stored_pos = positions_by_fund.get(fund_id)
        stored_participations = stored_pos.participations if stored_pos else Decimal("0.0000")
        stored_patrimonio = round4(stored_participations * nav)
        if abs(patrimonio - stored_patrimonio) > Decimal("0.0001"):
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

    result = round4(current_value - total_invested)

    transactions = transactions_qs.order_by("-created_at")

    # Serie de evolución (rango configurable)
    range_key = request.GET.get("range", "30d")
    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    today = timezone.now().date()

    start_date = None
    end_date = None

    if start_param or end_param:
        try:
            if start_param:
                start_date = datetime.strptime(start_param, "%Y-%m-%d").date()
            if end_param:
                end_date = datetime.strptime(end_param, "%Y-%m-%d").date()
        except ValueError:
            start_date = None
            end_date = None

    if not start_date or not end_date:
        if range_key == "today":
            start_date = today
            end_date = today
        elif range_key == "7d":
            start_date = today - timedelta(days=6)
            end_date = today
        elif range_key == "15d":
            start_date = today - timedelta(days=14)
            end_date = today
        elif range_key == "6m":
            start_date = today - timedelta(days=183)
            end_date = today
        elif range_key == "1y":
            start_date = today - timedelta(days=365)
            end_date = today
        else:
            start_date = today - timedelta(days=30)
            end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    funds = [stats["fund"] for stats in tx_stats.values()]

    fechas_sorted = [start_date + timedelta(days=offset) for offset in range((end_date - start_date).days + 1)]
    totals_by_date = {fecha: Decimal("0.0000") for fecha in fechas_sorted}

    if funds:
        valores_qs = ValorDiarioFondo.objects.filter(
            fund__in=funds,
            fecha__lte=end_date,
        ).order_by("fecha")
    else:
        valores_qs = ValorDiarioFondo.objects.none()

    fund_valores = {}
    for valor in valores_qs:
        fund_valores.setdefault(valor.fund_id, []).append((valor.fecha, valor.nav))

    fund_txs = {}
    for tx in transactions_qs:
        fund_txs.setdefault(tx.fund_id, []).append({
            "date": tx.created_at.date(),
            "delta": tx.participations if tx.transaction_type in (InvestorFundTransaction.BUY, InvestorFundTransaction.BONUS) else -tx.participations,
        })

    for fund_id in fund_valores.keys():
        nav_series = fund_valores.get(fund_id, [])
        tx_list_sorted = sorted(fund_txs.get(fund_id, []), key=lambda x: x["date"])

        nav_idx = 0
        last_nav = None
        tx_idx = 0
        acumulado = Decimal("0.0000")

        for fecha in fechas_sorted:
            while nav_idx < len(nav_series) and nav_series[nav_idx][0] <= fecha:
                last_nav = nav_series[nav_idx][1]
                nav_idx += 1

            while tx_idx < len(tx_list_sorted) and tx_list_sorted[tx_idx]["date"] <= fecha:
                acumulado += tx_list_sorted[tx_idx]["delta"]
                tx_idx += 1

            if last_nav is None:
                continue

            totals_by_date[fecha] = round4(totals_by_date[fecha] + (acumulado * last_nav))

    chart_labels = [fecha.strftime("%d/%m") for fecha in fechas_sorted]
    chart_data = [round4(totals_by_date[fecha]) for fecha in fechas_sorted]

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
        "range_key": range_key,
        "range_start": start_date.strftime("%Y-%m-%d"),
        "range_end": end_date.strftime("%Y-%m-%d"),
    })


@login_required
def investor_evolution_data(request, pk):
    investor = get_object_or_404(Investor, pk=pk)
    if not can_access_investor(request.user, investor):
        raise PermissionDenied

    range_key = request.GET.get("range", "30d")
    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    today = timezone.now().date()

    start_date = None
    end_date = None

    if start_param or end_param:
        try:
            if start_param:
                start_date = datetime.strptime(start_param, "%Y-%m-%d").date()
            if end_param:
                end_date = datetime.strptime(end_param, "%Y-%m-%d").date()
        except ValueError:
            start_date = None
            end_date = None

    if not start_date or not end_date:
        if range_key == "today":
            start_date = today
            end_date = today
        elif range_key == "7d":
            start_date = today - timedelta(days=6)
            end_date = today
        elif range_key == "15d":
            start_date = today - timedelta(days=14)
            end_date = today
        elif range_key == "6m":
            start_date = today - timedelta(days=183)
            end_date = today
        elif range_key == "1y":
            start_date = today - timedelta(days=365)
            end_date = today
        else:
            start_date = today - timedelta(days=30)
            end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    positions = investor.fund_positions.select_related("fund")
    funds = [pos.fund for pos in positions]

    fechas_sorted = [start_date + timedelta(days=offset) for offset in range((end_date - start_date).days + 1)]
    totals_by_date = {fecha: Decimal("0.0000") for fecha in fechas_sorted}

    if funds:
        valores_qs = ValorDiarioFondo.objects.filter(
            fund__in=funds,
            fecha__lte=end_date,
        ).order_by("fecha")
    else:
        valores_qs = ValorDiarioFondo.objects.none()

    fund_valores = {}
    for valor in valores_qs:
        fund_valores.setdefault(valor.fund_id, []).append((valor.fecha, valor.nav))

    transactions_qs = investor.fund_transactions.select_related("fund").order_by("created_at")
    fund_txs = {}
    for tx in transactions_qs:
        fund_txs.setdefault(tx.fund_id, []).append({
            "date": tx.created_at.date(),
            "delta": tx.participations if tx.transaction_type in (InvestorFundTransaction.BUY, InvestorFundTransaction.BONUS) else -tx.participations,
        })

    for fund_id in fund_valores.keys():
        nav_series = fund_valores.get(fund_id, [])
        tx_list_sorted = sorted(fund_txs.get(fund_id, []), key=lambda x: x["date"])

        nav_idx = 0
        last_nav = None
        tx_idx = 0
        acumulado = Decimal("0.0000")

        for fecha in fechas_sorted:
            while nav_idx < len(nav_series) and nav_series[nav_idx][0] <= fecha:
                last_nav = nav_series[nav_idx][1]
                nav_idx += 1

            while tx_idx < len(tx_list_sorted) and tx_list_sorted[tx_idx]["date"] <= fecha:
                acumulado += tx_list_sorted[tx_idx]["delta"]
                tx_idx += 1

            if last_nav is None:
                continue

            totals_by_date[fecha] = round4(totals_by_date[fecha] + (acumulado * last_nav))

    chart_labels = [fecha.strftime("%d/%m") for fecha in fechas_sorted]
    chart_data = [float(round4(totals_by_date[fecha])) for fecha in fechas_sorted]

    return JsonResponse({
        "labels": chart_labels,
        "data": chart_data,
    })

def current_value(self) -> Decimal:
    latest_valor = self.fund.valores_diarios.order_by("-fecha").first()
    if not latest_valor:
        return Decimal("0.0000")
    return round4(self.participations * latest_valor.nav)

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
            amount = round4(Decimal(amount_str))
        except Exception:
            amount = Decimal("0.0000")

        if amount <= 0:
            return render(request, "investors/invest.html", {
                "fund": fund,
                "error": "El importe debe ser mayor que 0."
            })

        participation_value = round4(fund.participation_value())
        participations = round4(amount / participation_value)

        position, _ = InvestorFund.objects.get_or_create(
            investor=investor,
            fund=fund,
            defaults={"participations": Decimal("0.0000")}
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

        if template_type == "BUY_REPORT":
            return redirect(
                f"{reverse('investors:notification_create_buy')}?investor={investor_id}"
            )

        if template_type == "SELL_REPORT":
            return redirect(
                f"{reverse('investors:notification_create_sell')}?investor={investor_id}"
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
        total_invertido = Decimal("0.0000")
        total_actual = Decimal("0.0000")
        total_participaciones = Decimal("0.0000")
        report_date = None

        for pos in positions:
            fund = pos.fund
            valor = fund.valores_diarios.first()
            nav = valor.nav if valor else Decimal("0.0000")
            if valor and (report_date is None or valor.fecha > report_date):
                report_date = valor.fecha

            fund_transactions = investor.fund_transactions.filter(
                fund=fund
            ).order_by("created_at")

            participaciones = Decimal("0.0000")
            capital_invertido = Decimal("0.0000")
            for tx in fund_transactions:
                if tx.transaction_type in (InvestorFundTransaction.BUY, InvestorFundTransaction.BONUS):
                    sign = Decimal("1")
                elif tx.transaction_type == InvestorFundTransaction.SELL:
                    sign = Decimal("-1")
                else:
                    sign = Decimal("0")
                participaciones = round4(participaciones + (sign * tx.participations))
                capital_invertido = round4(capital_invertido + (sign * tx.amount))

            capital_actual = round4(participaciones * nav)
            resultado = round4(capital_actual - capital_invertido)
            porcentaje = round4((resultado / capital_invertido) * Decimal("100")) if capital_invertido > 0 else Decimal("0.0000")

            total_invertido = round4(total_invertido + capital_invertido)
            total_actual = round4(total_actual + capital_actual)
            total_participaciones = round4(total_participaciones + participaciones)

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

        total_resultado = round4(total_actual - total_invertido)
        total_porcentaje = round4((total_resultado / total_invertido) * Decimal("100")) if total_invertido > 0 else Decimal("0.0000")
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
    total_invertido = Decimal("0.0000")
    total_actual = Decimal("0.0000")
    total_participaciones = Decimal("0.0000")
    report_date = None

    for pos in positions:
        fund = pos.fund
        valor = fund.valores_diarios.first()
        nav = valor.nav if valor else Decimal("0.0000")
        if valor and (report_date is None or valor.fecha > report_date):
            report_date = valor.fecha

        fund_transactions = investor.fund_transactions.filter(
            fund=fund
        ).order_by("created_at")

        participaciones = Decimal("0.0000")
        capital_invertido = Decimal("0.0000")
        for tx in fund_transactions:
            if tx.transaction_type in (InvestorFundTransaction.BUY, InvestorFundTransaction.BONUS):
                sign = Decimal("1")
            elif tx.transaction_type == InvestorFundTransaction.SELL:
                sign = Decimal("-1")
            else:
                sign = Decimal("0")
            participaciones = round4(participaciones + (sign * tx.participations))
            capital_invertido = round4(capital_invertido + (sign * tx.amount))

        capital_actual = round4(participaciones * nav)
        resultado = round4(capital_actual - capital_invertido)
        porcentaje = round4((resultado / capital_invertido) * Decimal("100")) if capital_invertido > 0 else Decimal("0.0000")

        total_invertido = round4(total_invertido + capital_invertido)
        total_actual = round4(total_actual + capital_actual)
        total_participaciones = round4(total_participaciones + participaciones)

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

    total_resultado = round4(total_actual - total_invertido)
    total_porcentaje = round4((total_resultado / total_invertido) * Decimal("100")) if total_invertido > 0 else Decimal("0.0000")
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

    fund_id = request.GET.get("fund") or request.POST.get("fund")
    tx_qs = InvestorFundTransaction.objects.filter(
        investor=investor,
        transaction_type=InvestorFundTransaction.BUY,
    ).select_related("fund").order_by("-created_at")

    funds = Fund.objects.filter(id__in=tx_qs.values_list("fund_id", flat=True)).order_by("name")

    latest_tx = None
    if fund_id:
        latest_tx = tx_qs.filter(fund_id=fund_id).first()
    else:
        latest_tx = tx_qs.first()

    fund = latest_tx.fund if latest_tx else funds.first() if funds.exists() else None

    fee_amount = Decimal("0.0000")
    gross_amount = Decimal("0.0000")
    net_amount = Decimal("0.0000")
    nav_value = Decimal("10.0000")
    participations = Decimal("0.0000")

    if latest_tx:
        net_amount = round4(latest_tx.amount)
        nav_value = round4(latest_tx.nav_price)
        participations = round4(latest_tx.participations)

        fee_tx = InvestorFundTransaction.objects.filter(
            investor__user__username="admin",
            fund=latest_tx.fund,
            reference__icontains=f"Comisión 1% de la transacción de {investor.user.username}",
            created_at__date=latest_tx.created_at.date(),
        ).order_by("-created_at").first()

        if fee_tx:
            fee_amount = round4(fee_tx.amount)
            gross_amount = round4(net_amount + fee_amount)
        else:
            gross_amount = round4(net_amount / Decimal("0.99")) if net_amount > 0 else Decimal("0.0000")
            fee_amount = round4(gross_amount - net_amount)

    context = {
        "investor": investor,
        "fund": fund,
        "funds": funds,
        "selected_fund_id": int(fund.id) if fund else None,
        "importe_aportado": gross_amount,
        "comision_entrada": fee_amount,
        "capital_invertido": net_amount,
        "nav": nav_value,
        "participaciones": participations,
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


@staff_member_required
def notification_create_buy(request):
    investor = get_object_or_404(
        Investor, id=request.GET.get("investor") or request.POST.get("investor_id")
    )

    tx_id = request.GET.get("tx_id") or request.POST.get("tx_id")
    tx_date = request.GET.get("tx_date") or request.POST.get("tx_date")

    tx_qs = InvestorFundTransaction.objects.filter(
        investor=investor,
        transaction_type=InvestorFundTransaction.BUY,
    ).order_by("-created_at")

    selected_tx = None
    if tx_id:
        selected_tx = tx_qs.filter(id=tx_id).first()
    elif tx_date:
        selected_tx = tx_qs.filter(created_at__date=tx_date).first()
    else:
        selected_tx = tx_qs.first()

    context = {
        "investor": investor,
        "transaction": selected_tx,
        "transactions": tx_qs,
        "tx_date": tx_date,
        "report_title": "Reporte de Compra",
        "report_subtitle": "Confirmación de suscripción",
        "report_label": "Compra",
    }

    if request.method == "POST" and request.POST.get("action") == "save":
        if not selected_tx:
            messages.error(request, "No hay transacción de compra para generar el reporte.")
            return redirect(request.path + f"?investor={investor.id}")

        html = render_to_string("investors/report_transaction.html", context)

        notification = Notification.objects.create(
            investor=investor,
            title="Reporte de Compra",
            template="BUY_REPORT",
            content=html,
            status="SENT",
        )

        return redirect("investors:notification_detail", notification.id)

    return render(request, "investors/notification_create_transaction.html", context)


@staff_member_required
def notification_create_sell(request):
    investor = get_object_or_404(
        Investor, id=request.GET.get("investor") or request.POST.get("investor_id")
    )

    tx_id = request.GET.get("tx_id") or request.POST.get("tx_id")
    tx_date = request.GET.get("tx_date") or request.POST.get("tx_date")

    tx_qs = InvestorFundTransaction.objects.filter(
        investor=investor,
        transaction_type=InvestorFundTransaction.SELL,
    ).order_by("-created_at")

    selected_tx = None
    if tx_id:
        selected_tx = tx_qs.filter(id=tx_id).first()
    elif tx_date:
        selected_tx = tx_qs.filter(created_at__date=tx_date).first()
    else:
        selected_tx = tx_qs.first()

    context = {
        "investor": investor,
        "transaction": selected_tx,
        "transactions": tx_qs,
        "tx_date": tx_date,
        "report_title": "Reporte de Venta",
        "report_subtitle": "Confirmación de reembolso",
        "report_label": "Venta",
    }

    if request.method == "POST" and request.POST.get("action") == "save":
        if not selected_tx:
            messages.error(request, "No hay transacción de venta para generar el reporte.")
            return redirect(request.path + f"?investor={investor.id}")

        html = render_to_string("investors/report_transaction.html", context)

        notification = Notification.objects.create(
            investor=investor,
            title="Reporte de Venta",
            template="SELL_REPORT",
            content=html,
            status="SENT",
        )

        return redirect("investors:notification_detail", notification.id)

    return render(request, "investors/notification_create_transaction.html", context)


@login_required
def dashboard(request):
    inversor = getattr(request.user, "investor_profile", None)
    if not inversor:
        inversor, _ = Investor.objects.get_or_create(user=request.user)

    if request.user.is_staff:
        investor_id = request.GET.get("investor")
        if investor_id:
            inversor = get_object_or_404(Investor, id=investor_id)

    positions = InvestorFund.objects.filter(investor=inversor).select_related("fund")
    
    # Transacciones completas del inversor para su Dashboard
    transactions = InvestorFundTransaction.objects.filter(
        investor=inversor
    ).select_related("fund").order_by("-created_at")

    dashboard_funds = []
    for position in positions:
        fund = position.fund
        valor_diario = ValorDiarioFondo.objects.filter(fund=fund).order_by("-fecha").first()

        capital_total_fondo = valor_diario.valor_total if valor_diario else Decimal("0.0000")
        nav_actual = valor_diario.nav if valor_diario else fund.current_nav()
        date_update = valor_diario.fecha if valor_diario else None

        capital_usuario = round4(position.participations * nav_actual)

        # Cálculo de Rendimiento (PnL y ROI)
        avg_price = position.average_price or Decimal("0.0000")
        cost_basis = round4(position.participations * avg_price)
        pnl = round4(capital_usuario - cost_basis)
        roi = round4((pnl / cost_basis) * Decimal("100")) if cost_basis > 0 else Decimal("0.0000")

        dashboard_funds.append({
            "fund": fund,
            "participations": position.participations,
            "nav_actual": round4(nav_actual),
            "capital_usuario": capital_usuario,
            "capital_total_fondo": round4(capital_total_fondo),
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
    )["total"] or Decimal("0.0000")
    total_comisiones_recibidas = round4(total_comisiones_recibidas)

    total_portfolio_value = round4(sum(item["capital_usuario"] for item in dashboard_funds))

    investors_list = None
    if request.user.is_staff:
        investors_list = Investor.objects.select_related("user").order_by("user__username")
    else:
        investors_list = [inversor]

    return render(
        request,
        "investors/dashboard.html",
        {
            "dashboard_funds": dashboard_funds,
            "transactions": transactions,
            "total_portfolio_value": total_portfolio_value,
            "total_comisiones_recibidas": total_comisiones_recibidas,
            "inversor": inversor,
            "investors_list": investors_list,
        }
    )


@staff_member_required
def convert_honorarios_view(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    investor_id = request.POST.get("investor_id")
    if not investor_id:
        return JsonResponse({"success": False, "error": "Inversor requerido"}, status=400)

    investor = get_object_or_404(Investor, id=investor_id)

    fund = Fund.objects.filter(is_open=True).first() or Fund.objects.first()
    if not fund:
        return JsonResponse({"success": False, "error": "No hay fondos disponibles"}, status=400)

    valor_diario = ValorDiarioFondo.objects.filter(fund=fund).order_by("-fecha").first()
    nav_actual = valor_diario.nav if valor_diario else fund.current_nav()
    nav_actual = round4(nav_actual)

    if nav_actual <= 0:
        return JsonResponse({"success": False, "error": "NAV actual inválido"}, status=400)

    honorarios_qs = InvestorFundTransaction.objects.filter(
        investor=investor,
        reference__icontains="Comisión",
    )
    honorarios = honorarios_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.0000")
    honorarios = round4(honorarios)

    if honorarios <= 0:
        return JsonResponse({"success": False, "error": "Sin honorarios para convertir"}, status=400)

    participations = round4(honorarios / nav_actual)

    with db_transaction.atomic():
        InvestorFundTransaction.objects.create(
            investor=investor,
            fund=fund,
            transaction_type=InvestorFundTransaction.BONUS,
            participations=participations,
            nav_price=nav_actual,
            reference=f"Conversión honorarios - {request.user.username}",
        )

        honorarios_qs.update(reference="Honorarios convertidos")

    return JsonResponse({"success": True})

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
        capital_total = valor_diario.valor_total if valor_diario else Decimal("0.0000")
        total_participations = fund.total_participations
        nav_actual = valor_diario.nav if valor_diario else fund.current_nav()
        aum = fund.aum

        dashboard_data.append({
            "fund": fund,
            "total_participations": total_participations,
            "nav_actual": round4(nav_actual),
            "capital_total": round4(capital_total),
            "aum": round4(aum),
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
