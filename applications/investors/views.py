from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import F, Sum, Q, DecimalField, ExpressionWrapper
from django.contrib.auth import get_user_model
from datetime import datetime
from decimal import Decimal

from .models import Investor, InvestorFund, Notification, InvestorFundTransaction
from applications.funds.models import Fund, FundTrade, FundCapitalSnapshot, FundPosition
from applications.investors.services.participations import buy_participations, sell_participations

User = get_user_model()

def is_staff(user):
    return user.is_staff


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

    current_value = sum(
        pos.participations * (pos.fund.nav_actual or Decimal("0.00"))
        for pos in positions
    ) or Decimal("0.00")

    total_invested = sum(
        pos.participations * (pos.average_price or Decimal("0.00"))
        for pos in positions
    ) or Decimal("0.00")

    result = current_value - total_invested

    return render(request, "investors/investor_detail.html", {
        "investor": investor,
        "positions": positions,
        "total_invested": total_invested,
        "current_value": current_value,
        "result": result,
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

    funds = Fund.objects.all()
    investors = Investor.objects.select_related("user")

    return render(request, "investors/buy_participations.html", {
        "investors": investors,
        "funds": funds,
    })

@staff_member_required
def sell_participations_view(request):
    if request.method == "POST":
        investor_id = request.POST.get("investor")
        participations = request.POST.get("participations")
        nav_price = request.POST.get("nav_price")
        
        # Hardcoded for now: we need to know the fund. In a real scenario, the investor has positions.
        # We find the position for that investor.
        investor = get_object_or_404(Investor, pk=investor_id)
        position = investor.fund_positions.first() # Getting the first active position for simplicity in this proto

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
            return redirect("investors:dashboard-gestor")

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



@login_required
def dashboard(request):

    inversor = getattr(request.user, "investor_profile", None)

    positions = (
        InvestorFund.objects
        .filter(investor=inversor)
        .select_related("fund")
    )

    dashboard_funds = []

    for position in positions:
        fund = position.fund

        snapshot = (
            FundCapitalSnapshot.objects
            .filter(fund=fund)
            .order_by("-date")
            .first()
        )

        capital_total_fondo = snapshot.total_capital if snapshot else Decimal("0")
        nav_actual = fund.nav_actual or Decimal("0")
        date_update =snapshot.date

        capital_usuario = (
            position.participations * nav_actual
        ).quantize(Decimal("0.01"))

        dashboard_funds.append({
            "fund": fund,
            "participations": position.participations,
            "nav_actual": nav_actual.quantize(Decimal("0.0001")),
            "capital_usuario": capital_usuario,
            "capital_total_fondo": capital_total_fondo.quantize(Decimal("0.01")),
            "date_update": date_update
        })

    transactions = (
        InvestorFundTransaction.objects
        .filter(investor=inversor)
        .select_related("fund")
        .order_by("-created_at")
    )

    total_portfolio_value = sum(item["capital_usuario"] for item in dashboard_funds)

    return render(
        request,
        "investors/dashboard.html",
        {
            "dashboard_funds": dashboard_funds,
            "transactions": transactions,
            "total_portfolio_value": total_portfolio_value,
        }
    )



from django.contrib.auth.decorators import login_required, user_passes_test
from decimal import Decimal


@login_required
@user_passes_test(lambda u: u.is_staff)
def dashboard_gestor(request):

    funds = Fund.objects.all()
    dashboard_data = []

    for fund in funds:

        # -----------------------------
        # 1. Último snapshot de capital
        # -----------------------------
        snapshot = (
            FundCapitalSnapshot.objects
            .filter(fund=fund)
            .order_by("-date")
            .first()
        )

        capital_total = snapshot.total_capital if snapshot else Decimal("0.00")

        # -----------------------------
        # 2. Datos base del fondo
        # -----------------------------
        total_participations = fund.participations
        nav_actual = fund.nav_actual or Decimal("0.00")

        # -----------------------------
        # 3. Limpieza visual
        # -----------------------------
        capital_total = capital_total.quantize(Decimal("0.01"))
        nav_actual = nav_actual.quantize(Decimal("0.0001"))

        dashboard_data.append({
            "fund": fund,
            "total_participations": total_participations,
            "nav_actual": nav_actual,
            "capital_total": capital_total,
            "investors_count": fund.investors.count(),

            # 👇 POSICIONES ACTUALES DEL FONDO
            "fund_positions": (
                FundPosition.objects
                .filter(fund=fund)
                .select_related("product")
            ),

            # 👇 HISTÓRICO INVERSORES
            "investor_transactions": (
                InvestorFundTransaction.objects
                .filter(fund=fund)
                .select_related("investor", "investor__user")
                .order_by("-created_at")
            ),

            # 👇 HISTÓRICO OPERACIONES DEL FONDO
            "fund_trades": (
                FundTrade.objects
                .filter(fund=fund)
                .select_related("product")
                .order_by("-created_at")
            ),
        })

    # 👇 ÚLTIMAS 10 OPERACIONES GLOBALES (PARA EL LIBRO DE ACTIVIDAD)
    all_fund_trades = (
        FundTrade.objects.all()
        .select_related("fund", "product")
        .order_by("-created_at")[:10]
    )

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



@login_required
def invest(request):
    fund = Fund.objects.first()

    return render(request, "investors/invest.html", {
        "fund": fund,
    })

@staff_member_required
def investor_create(request):
    """
    Creación manual de nuevos inversores por parte del gestor.
    """
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
                # Crear Usuario
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Crear Perfil de Inversor
                Investor.objects.create(
                    user=user,
                    document_id=document_id,
                    phone=phone,
                    risk_level=risk_level,
                    birth_date=birth_date
                )
            
            messages.success(request, f"Inversor {first_name} {last_name} creado con éxito.")
            return redirect("investors:investor_list")
            
        except Exception as e:
            messages.error(request, f"Error al crear: {str(e)}")

    return render(request, "investors/investor_form.html", {
        "risk_levels": Investor.RISK_LEVELS
    })
