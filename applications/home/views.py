# Create your views here.
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from urllib import request as urlrequest
from urllib.parse import urlencode
import json
from core.services.email_service import send_email_brevo
from applications.funds.models import Fund, FundDiversification
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .models import MapElement, MapElementType
def index(request):
    fund = Fund.objects.all()


def index(request):
    fund1 = Fund.objects.filter(id=1)
    diversification1 = FundDiversification.objects.filter(is_active=True, fund=1)
    return render(request, "home/index.html", {
        "fund1": fund1,
        "diversification1": diversification1,
        "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
    })


@require_POST
def contact_submit(request):
    token = request.POST.get("recaptcha_token", "")
    if not token:
        return JsonResponse({"error": "captcha_missing"}, status=400)

    secret_key = settings.RECAPTCHA_SECRET_KEY
    if not secret_key:
        return JsonResponse({"error": "captcha_not_configured"}, status=400)

    payload = urlencode({
        "secret": secret_key,
        "response": token,
        "remoteip": request.META.get("REMOTE_ADDR", ""),
    }).encode("utf-8")

    try:
        with urlrequest.urlopen(
            "https://www.google.com/recaptcha/api/siteverify",
            data=payload,
            timeout=10,
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "captcha_unavailable"}, status=400)

    score = data.get("score", 0)
    action = data.get("action", "")
    if not data.get("success") or score < settings.RECAPTCHA_THRESHOLD or action != "contact":
        return JsonResponse(
            {
                "error": "captcha_failed",
                "score": score,
                "action": action,
                "codes": data.get("error-codes", []),
            },
            status=400,
        )

    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    subject = request.POST.get("subject", "").strip()
    message = request.POST.get("message", "").strip()

    if not name or not email or not message:
        return JsonResponse({"error": "invalid_form"}, status=400)

    email_subject = "Nuevo mensaje de contacto desde Fondo Capital"
    html_body = (
        "<h2>Nuevo mensaje de contacto</h2>"
        "<p>Has recibido un mensaje desde el formulario de contacto de Fondo Capital.</p>"
        "<ul>"
        f"<li><strong>Nombre:</strong> {name}</li>"
        f"<li><strong>Email:</strong> {email}</li>"
        f"<li><strong>Telefono:</strong> {phone}</li>"
        f"<li><strong>Asunto:</strong> {subject}</li>"
        "</ul>"
        f"<p><strong>Mensaje:</strong></p><p>{message}</p>"
    )
    text_body = (
        "Nueva solicitud de contacto\n\n"
        f"Nombre: {name}\n"
        f"Email: {email}\n"
        f"Telefono: {phone}\n"
        f"Asunto: {subject}\n\n"
        f"Mensaje:\n{message}\n"
    )

    recipients = getattr(settings, "CONTACT_RECIPIENTS", ["duarteolvin30@gmail.com"])

    try:
        send_email_brevo(
            to=recipients,
            subject=email_subject,
            html_content=html_body,
            text_content=text_body,
            reply_to=email,
        )
    except Exception as exc:
        return JsonResponse({"error": "email_failed", "detail": str(exc)}, status=400)

    return JsonResponse({"ok": True})

class SimuladorRentabilidadView(TemplateView):
    template_name = "home/simulador-rentabilidad.html"


@method_decorator(staff_member_required, name="dispatch")
class FundMapView(TemplateView):
    template_name = "home/map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund = Fund.objects.first()
        positions = fund.positions.select_related("product") if fund else []
        map_elements = MapElement.objects.filter(
            is_active=True,
            show_in_map=True
        )

        context["fund"] = fund
        context["positions"] = positions
        context["map_elements"] = map_elements

        return context
