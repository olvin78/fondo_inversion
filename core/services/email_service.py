import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_email_brevo(to, subject, html_content, text_content=None, reply_to=None):
    logger.info("Enviando email a %s con asunto %s", to, subject)
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": "Fondo Capital",
            "email": "info@fondocapital.olvinduarte.com",
        },
        "to": [{"email": email} for email in to],
        "subject": subject,
        "htmlContent": html_content,
    }

    if text_content:
        payload["textContent"] = text_content

    if reply_to:
        payload["replyTo"] = {"email": reply_to}

    response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=15)

    if response.status_code not in (200, 201):
        raise Exception(f"Error enviando email con Brevo: {response.text}")

    return response.json()
