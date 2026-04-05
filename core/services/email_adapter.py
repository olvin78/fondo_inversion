from core.services.email_service import send_email_brevo


def send_mail(subject, message, from_email, recipient_list, html_message=None):
    html_content = html_message or message

    return send_email_brevo(
        to=recipient_list,
        subject=subject,
        html_content=html_content,
        text_content=message,
    )
