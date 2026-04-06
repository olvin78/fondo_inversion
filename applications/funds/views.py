from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from .models import FundTrade
from .forms import FundTradeForm, FundForm
from decimal import Decimal, InvalidOperation
from core.utils.decimal import round4
from applications.funds.models import (
    Fund,
    FundPosition,
    FundDiversification,
    ValorDiarioFondo,
)
from applications.investors.models import Investor


@staff_member_required
def fund_list(request):
    funds = Fund.objects.all().order_by("name")
    return render(request, "funds/fund_list.html", {"funds": funds})


@staff_member_required
def fund_create(request):
    if request.method == "POST":
        form = FundForm(request.POST)
        if form.is_valid():
            fund = form.save(commit=False)
            fund.created_by = request.user
            fund.save()
            messages.success(request, "Fondo creado correctamente.")
            return redirect("funds:create")
    else:
        form = FundForm()

    return render(request, "funds/fund_create.html", {"form": form})


@staff_member_required
def fund_detail(request, pk):
    fund = get_object_or_404(Fund, pk=pk)

    # =========================
    # POSICIONES DEL FONDO
    # =========================
    positions_qs = (
        FundPosition.objects
        .filter(fund=fund)
        .select_related("product")
    )

    total_fund_value = Decimal("0.0000")
    for p in positions_qs:
        total_fund_value = round4(total_fund_value + (p.quantity * p.avg_price))

    positions = []
    for p in positions_qs:
        position_value = round4(p.quantity * p.avg_price)

        weight = (
            round4((position_value / total_fund_value) * Decimal("100"))
            if total_fund_value > 0
            else Decimal("0.0000")
        )

        positions.append({
            "product": p.product,
            "weight": round4(weight),
        })

    # =========================
    # HISTÓRICO DE NAV (CLAVE)
    # =========================
    range_key = request.GET.get("range", "30d")
    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    today = timezone.now().date()

    start_date = None
    end_date = None

    if start_param or end_param:
        try:
            if start_param:
                start_date = timezone.datetime.fromisoformat(start_param).date()
            if end_param:
                end_date = timezone.datetime.fromisoformat(end_param).date()
        except ValueError:
            start_date = None
            end_date = None

    if not start_date or not end_date:
        if range_key == "today":
            start_date = today
            end_date = today
        elif range_key == "7d":
            start_date = today - timezone.timedelta(days=6)
            end_date = today
        elif range_key == "15d":
            start_date = today - timezone.timedelta(days=14)
            end_date = today
        elif range_key == "6m":
            start_date = today - timezone.timedelta(days=183)
            end_date = today
        elif range_key == "1y":
            start_date = today - timezone.timedelta(days=365)
            end_date = today
        else:
            start_date = today - timezone.timedelta(days=30)
            end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    valores_diarios = (
        fund.valores_diarios
        .filter(fecha__gte=start_date, fecha__lte=end_date)
        .order_by("fecha")
    )

    # =========================
    # OTROS DATOS DEL FONDO
    # =========================
    buy_transactions = (
        FundTrade.objects
        .filter(
            fund=fund,
            transaction_type="BUY"
        )
        .select_related("product")
    )

    investors = fund.investors.count()

    diversification = (
        FundDiversification.objects
        .filter(is_active=True)
    )

    return render(
        request,
        "funds/fund_detail.html",
        {
            "fund": fund,
            "positions": positions,          # ← pesos (%)
            "valores_diarios": valores_diarios,      # ← gráfico NAV
            "buy_transactions": buy_transactions,
            "investors": investors,
            "diversification": diversification,
            "range_key": range_key,
            "range_start": start_date.strftime("%Y-%m-%d"),
            "range_end": end_date.strftime("%Y-%m-%d"),
        }
    )


@staff_member_required
def fund_evolution_data(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    range_key = request.GET.get("range", "30d")
    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    today = timezone.now().date()

    start_date = None
    end_date = None

    if start_param or end_param:
        try:
            if start_param:
                start_date = timezone.datetime.fromisoformat(start_param).date()
            if end_param:
                end_date = timezone.datetime.fromisoformat(end_param).date()
        except ValueError:
            start_date = None
            end_date = None

    if not start_date or not end_date:
        if range_key == "today":
            start_date = today
            end_date = today
        elif range_key == "7d":
            start_date = today - timezone.timedelta(days=6)
            end_date = today
        elif range_key == "15d":
            start_date = today - timezone.timedelta(days=14)
            end_date = today
        elif range_key == "6m":
            start_date = today - timezone.timedelta(days=183)
            end_date = today
        elif range_key == "1y":
            start_date = today - timezone.timedelta(days=365)
            end_date = today
        else:
            start_date = today - timezone.timedelta(days=30)
            end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    valores_diarios = (
        fund.valores_diarios
        .filter(fecha__gte=start_date, fecha__lte=end_date)
        .order_by("fecha")
    )

    labels = [v.fecha.strftime("%d/%m") for v in valores_diarios]
    data = [float(round4(v.nav)) for v in valores_diarios]

    return JsonResponse({
        "labels": labels,
        "data": data,
    })


@staff_member_required
def transaction_list(request):
    transactions = FundTrade.objects.all().order_by("-created_at")
    return render(request, "funds/fundTrade_list.html", {"transactions": transactions})


@staff_member_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(FundTrade, pk=pk)
    return render(request, "funds/fundTrade_detail.html", {"transaction": transaction})


@staff_member_required
def transaction_create(request):
    product_id = request.GET.get("product")
    product = None
    if product_id:
        from applications.products.models import Product
        product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = FundTradeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("funds:transaction_list")
    else:
        # Pre-poblar el producto si se proporciona
        initial = {}
        if product:
            initial['product'] = product
        form = FundTradeForm(initial=initial)
    
    return render(request, "funds/fundTrade_form.html", {
        "form": form,
        "product": product
    })


@staff_member_required
def crear_valor_diario(request):
    if request.method != "POST":
        return redirect("investors:dashboard-gestor")

    fund_id = request.POST.get("fund_id")
    fecha_str = request.POST.get("fecha")
    capital_ibkr_raw = request.POST.get("capital_ibkr", "0")
    capital_binance_raw = request.POST.get("capital_binance", "0")

    fund = get_object_or_404(Fund, pk=fund_id)

    try:
        capital_ibkr = Decimal(capital_ibkr_raw or "0")
        capital_binance = Decimal(capital_binance_raw or "0")
    except InvalidOperation:
        messages.error(request, "Valores de capital no válidos.")
        return redirect("investors:dashboard-gestor")

    fecha = timezone.now().date()
    if fecha_str:
        try:
            fecha = timezone.datetime.fromisoformat(fecha_str).date()
        except ValueError:
            messages.error(request, "Fecha no válida.")
            return redirect("investors:dashboard-gestor")

    ValorDiarioFondo.objects.update_or_create(
        fund=fund,
        fecha=fecha,
        defaults={
            "capital_interactive_broker": capital_ibkr,
            "capital_binance": capital_binance,
            "creado_por": request.user,
        }
    )

    messages.success(request, "Valor diario actualizado correctamente.")
    return redirect("investors:dashboard-gestor")
