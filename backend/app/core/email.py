"""
Email sending module for quotes and notifications
"""

import base64
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

HTTP_EMAIL_TIMEOUT_SECONDS = 20

NOUGRAM_BRAND_LOGO_URL = "https://www.nougram.co/logo-nougram.png"
NOUGRAM_SITE_URL = "https://www.nougram.co"
NOUGRAM_BRAND_DARK = "#262537"
NOUGRAM_BRAND_ACCENT = "#F35D0A"


def _resend_template_variables(data: dict[str, Any] | None) -> dict[str, Any]:
    """Build Resend `template.variables` object (keys: letters, digits, underscore only)."""
    out: dict[str, Any] = {}
    if not data:
        return out
    for raw_k, v in data.items():
        key = str(raw_k).strip()
        if not key:
            continue
        normalized = []
        for i, c in enumerate(key):
            if c.isalnum() or c == "_":
                normalized.append(c)
            elif c in ("-", " ", "."):
                normalized.append("_")
        k2 = "".join(normalized)
        if not k2:
            continue
        if k2[0].isdigit():
            k2 = f"var_{k2}"
        if isinstance(v, bool):
            out[k2] = "true" if v else "false"
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k2] = v
        else:
            out[k2] = str(v) if v is not None else ""
    return out


def _get_from_identity() -> tuple[str, str]:
    provider = (settings.EMAIL_PROVIDER or "smtp").strip().lower()
    if provider == "mailersend":
        from_email = (settings.MAILERSEND_FROM_EMAIL or settings.SMTP_FROM_EMAIL or "").strip()
        from_name = (settings.MAILERSEND_FROM_NAME or settings.SMTP_FROM_NAME or "Nougram").strip()
        return from_email, from_name
    if provider == "resend":
        from_email = (
            settings.RESEND_FROM_EMAIL
            or settings.MAILERSEND_FROM_EMAIL
            or settings.SMTP_FROM_EMAIL
            or ""
        ).strip()
        from_name = (
            settings.RESEND_FROM_NAME
            or settings.MAILERSEND_FROM_NAME
            or settings.SMTP_FROM_NAME
            or "Nougram"
        ).strip()
        return from_email, from_name
    return (settings.SMTP_FROM_EMAIL or "").strip(), (settings.SMTP_FROM_NAME or "Nougram").strip()


def get_brand_sender_name() -> str:
    """Display name for transactional emails (matches active provider identity)."""
    _, name = _get_from_identity()
    return name if name else "Nougram"


def _read_attachment_bytes(content: object) -> bytes:
    if hasattr(content, "read"):
        data = content.read()
        if hasattr(content, "seek"):
            content.seek(0)
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        return bytes(data)
    if isinstance(content, bytes):
        return content
    if isinstance(content, str):
        return content.encode("utf-8")
    return bytes(content)


async def _send_email_via_mailersend(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
    attachments: list[dict] | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    template_id: str | None = None,
    template_data: dict[str, Any] | None = None,
) -> bool:
    api_key = (settings.MAILERSEND_API_KEY or "").strip()
    from_email, from_name = _get_from_identity()
    if not api_key or not from_email:
        logger.warning(
            "MailerSend not configured. Missing API key or from email.",
            level="warning",
            module=__name__,
            function="_send_email_via_mailersend",
        )
        return False

    payload: dict = {
        "from": {"email": from_email, "name": from_name},
        "to": [{"email": to_email}],
        "subject": subject,
    }
    if template_id:
        payload["template_id"] = template_id
        payload["personalization"] = [
            {
                "email": to_email,
                "data": template_data or {},
            }
        ]
    else:
        payload["html"] = body_html
        if body_text:
            payload["text"] = body_text
    if cc:
        payload["cc"] = [{"email": email} for email in cc if email]
    if bcc:
        payload["bcc"] = [{"email": email} for email in bcc if email]

    if attachments:
        encoded_attachments: list[dict] = []
        for attachment in attachments:
            filename = str(attachment.get("filename") or "attachment")
            content = attachment.get("content")
            if not content:
                continue
            raw_bytes = _read_attachment_bytes(content)
            encoded_attachments.append(
                {
                    "filename": filename,
                    "content": base64.b64encode(raw_bytes).decode("utf-8"),
                }
            )
        if encoded_attachments:
            payload["attachments"] = encoded_attachments

    url = f"{settings.MAILERSEND_BASE_URL.rstrip('/')}/email"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=HTTP_EMAIL_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.status_code in (200, 201, 202):
            logger.info(
                f"Email sent successfully to {to_email}",
                level="info",
                module=__name__,
                function="_send_email_via_mailersend",
                subject=subject,
            )
            return True

        logger.error(
            f"MailerSend request failed for {to_email}",
            level="error",
            module=__name__,
            function="_send_email_via_mailersend",
            status_code=response.status_code,
            response_body=response.text[:800],
        )
        return False
    except Exception as e:
        logger.error(
            f"Error sending email to {to_email} via MailerSend",
            level="error",
            module=__name__,
            function="_send_email_via_mailersend",
            error=str(e),
            exc_info=True,
        )
        return False


async def _send_email_via_resend(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
    attachments: list[dict] | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    template_id: str | None = None,
    template_data: dict[str, Any] | None = None,
    resend_template_id: str | None = None,
) -> bool:
    """Send via Resend. Use either dashboard template (resend_template_id) or HTML body, not both."""
    api_key = (settings.RESEND_API_KEY or "").strip()
    from_email, from_name = _get_from_identity()
    if not api_key or not from_email:
        logger.warning(
            "Resend not configured. Missing API key or from email.",
            level="warning",
            module=__name__,
            function="_send_email_via_resend",
        )
        return False

    from_field = f"{from_name} <{from_email}>" if from_name else from_email
    rtid = (resend_template_id or "").strip()

    if rtid:
        payload: dict[str, Any] = {
            "from": from_field,
            "to": [to_email],
            "subject": subject,
            "template": {
                "id": rtid,
                "variables": _resend_template_variables(template_data),
            },
        }
        if cc:
            payload["cc"] = [e for e in cc if e]
        if bcc:
            payload["bcc"] = [e for e in bcc if e]
    else:
        if template_id:
            logger.info(
                "MailerSend template_id ignored when sending via Resend without resend_template_id; using HTML body.",
                level="info",
                module=__name__,
                function="_send_email_via_resend",
                template_id=template_id,
            )
        payload = {
            "from": from_field,
            "to": [to_email],
            "subject": subject,
            "html": body_html,
        }
        if body_text:
            payload["text"] = body_text
        if cc:
            payload["cc"] = [e for e in cc if e]
        if bcc:
            payload["bcc"] = [e for e in bcc if e]

        if attachments:
            encoded_attachments: list[dict] = []
            for attachment in attachments:
                filename = str(attachment.get("filename") or "attachment")
                content = attachment.get("content")
                if not content:
                    continue
                raw_bytes = _read_attachment_bytes(content)
                encoded_attachments.append(
                    {
                        "filename": filename,
                        "content": base64.b64encode(raw_bytes).decode("utf-8"),
                    }
                )
            if encoded_attachments:
                payload["attachments"] = encoded_attachments

    url = f"{settings.RESEND_BASE_URL.rstrip('/')}/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=HTTP_EMAIL_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload, headers=headers)
        if response.status_code in (200, 201):
            resend_email_id: str | None = None
            try:
                body = response.json()
                if isinstance(body, dict):
                    raw_id = body.get("id")
                    resend_email_id = str(raw_id) if raw_id else None
            except Exception:
                pass
            logger.info(
                f"Email accepted by Resend API for {to_email}",
                subject=subject,
                resend_template=bool(rtid),
                resend_email_id=resend_email_id,
            )
            return True

        logger.error(
            f"Resend request failed for {to_email}",
            level="error",
            module=__name__,
            function="_send_email_via_resend",
            status_code=response.status_code,
            response_body=response.text[:800],
        )
        return False
    except Exception as e:
        logger.error(
            f"Error sending email to {to_email} via Resend",
            level="error",
            module=__name__,
            function="_send_email_via_resend",
            error=str(e),
            exc_info=True,
        )
        return False


async def _send_email_via_smtp(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
    attachments: list[dict] | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
) -> bool:
    # Check if email is configured
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("Email not configured. SMTP settings missing.")
        return False

    from_email, from_name = _get_from_identity()
    if not from_email:
        logger.warning("Email not configured. SMTP_FROM_EMAIL missing.")
        return False

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = ", ".join(cc)

        # Add body
        if body_text:
            part1 = MIMEText(body_text, "plain")
            msg.attach(part1)

        part2 = MIMEText(body_html, "html")
        msg.attach(part2)

        # Add attachments
        if attachments:
            for attachment in attachments:
                filename = attachment.get("filename", "attachment")
                content = attachment.get("content")

                if content:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(_read_attachment_bytes(content))
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {filename}")
                    msg.attach(part)

        # Get all recipients
        recipients = [to_email]
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)

        # Send email
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
            recipients=recipients,
        )

        logger.info(
            f"Email sent successfully to {to_email}",
            level="info",
            module=__name__,
            function="_send_email_via_smtp",
            subject=subject,
        )
        return True

    except Exception as e:
        logger.error(
            f"Error sending email to {to_email} via SMTP",
            level="error",
            module=__name__,
            function="_send_email_via_smtp",
            error=str(e),
            exc_info=True,
        )
        return False


async def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
    attachments: list[dict] | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    template_id: str | None = None,
    template_data: dict[str, Any] | None = None,
    resend_template_id: str | None = None,
) -> bool:
    """
    Send an email using the configured provider (SMTP, MailerSend API, or Resend API).

    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML email body
        body_text: Plain text email body (optional, will be generated from HTML if not provided)
        attachments: List of attachments with 'filename' and 'content' keys
        cc: List of CC email addresses
        bcc: List of BCC email addresses

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    provider = (settings.EMAIL_PROVIDER or "smtp").strip().lower()
    if provider == "mailersend":
        return await _send_email_via_mailersend(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            attachments=attachments,
            cc=cc,
            bcc=bcc,
            template_id=template_id,
            template_data=template_data,
        )
    if provider == "resend":
        return await _send_email_via_resend(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            attachments=attachments,
            cc=cc,
            bcc=bcc,
            template_id=template_id,
            template_data=template_data,
            resend_template_id=resend_template_id,
        )

    return await _send_email_via_smtp(
        to_email=to_email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        attachments=attachments,
        cc=cc,
        bcc=bcc,
    )


def generate_quote_email_html(
    project_name: str,
    client_name: str,
    quote_version: int,
    total_with_taxes: float,
    currency: str = "USD",
    notes: str | None = None,
    agency_name: str = "Nougram",
) -> str:
    """
    Generate HTML email template for quote

    Args:
        project_name: Project name
        client_name: Client name
        quote_version: Quote version number
        total_with_taxes: Total amount with taxes
        currency: Currency code
        notes: Optional notes
        agency_name: Agency name

    Returns:
        str: HTML email body
    """
    currency_symbols = {"USD": "$", "COP": "$", "ARS": "$", "EUR": "€"}
    symbol = currency_symbols.get(currency, "$")
    formatted_amount = f"{symbol} {total_with_taxes:,.2f}"

    notes_block = f"<p><strong>Notes:</strong><br>{notes}</p>" if notes else ""
    d, a, logo, site = NOUGRAM_BRAND_DARK, NOUGRAM_BRAND_ACCENT, NOUGRAM_BRAND_LOGO_URL, NOUGRAM_SITE_URL
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin:0;padding:0;background-color:#ebebf0;font-family:Arial,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#ebebf0;padding:24px 16px;"><tr><td align="center">
    <table role="presentation" width="100%" style="max-width:600px;background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #d4d4dc;"><tr>
    <td style="padding:20px 24px;text-align:center;background:{d};">
    <a href="{site}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-block;">
    <img src="{logo}" alt="Nougram" width="140" style="display:block;margin:0 auto;border:0;max-width:140px;width:140px;height:auto;" /></a></td></tr><tr>
    <td style="background:{d};color:#ffffff;padding:20px 24px;text-align:center;border-top:1px solid rgba(243,93,10,.25);">
    <h1 style="margin:0;font-size:18px;font-weight:600;">{agency_name}</h1>
    <p style="margin:8px 0 0;font-size:14px;opacity:.92;">Quote #{quote_version}</p></td></tr><tr>
    <td style="padding:24px;color:{d};line-height:1.6;font-size:15px;">
    <p style="margin:0 0 12px;">Dear {client_name},</p>
    <p style="margin:0 0 16px;">Thank you for your interest. Please find attached the quote for <strong>{project_name}</strong>.</p>
    <table role="presentation" width="100%" style="background:#fafafa;border-left:4px solid {a};margin:16px 0;padding:14px 16px;"><tr><td>
    <p style="margin:0 0 6px;font-size:14px;"><strong>Project:</strong> {project_name}</p>
    <p style="margin:0;font-size:14px;"><strong>Quote Version:</strong> {quote_version}</p></td></tr></table>
    <div style="text-align:center;padding:20px 16px;margin:16px 0;background:#f4f4f6;border-radius:8px;border:1px solid #e8e8ec;">
    <p style="margin:0;font-size:22px;font-weight:700;color:{d};">Total: {formatted_amount}</p></div>
    {notes_block}
    <p style="margin:20px 0 8px;">The detailed quote is attached as a PDF document. Please review it and let us know if you have any questions.</p>
    <p style="margin:0 0 8px;">This quote is valid for 30 days from the date of issue.</p>
    <p style="margin:0;">Best regards,<br><strong>{agency_name}</strong></p></td></tr><tr>
    <td style="padding:16px 24px;border-top:1px solid #e8e8ec;text-align:center;font-size:11px;color:#5c5d70;">Automated message · please do not reply directly</td></tr>
    </table></td></tr></table>
    </body>
    </html>
    """
    return html


def generate_quote_email_text(
    project_name: str,
    client_name: str,
    quote_version: int,
    total_with_taxes: float,
    currency: str = "USD",
    notes: str | None = None,
    agency_name: str = "Nougram",
) -> str:
    """
    Generate plain text email template for quote

    Args:
        project_name: Project name
        client_name: Client name
        quote_version: Quote version number
        total_with_taxes: Total amount with taxes
        currency: Currency code
        notes: Optional notes
        agency_name: Agency name

    Returns:
        str: Plain text email body
    """
    currency_symbols = {"USD": "$", "COP": "$", "ARS": "$", "EUR": "€"}
    symbol = currency_symbols.get(currency, "$")
    formatted_amount = f"{symbol} {total_with_taxes:,.2f}"

    text = f"""
{agency_name} - Quote #{quote_version}

Dear {client_name},

Thank you for your interest in our services. Please find attached the quote for {project_name}.

Project: {project_name}
Quote Version: {quote_version}
Total: {formatted_amount}

{f"Notes: {notes}" if notes else ""}

The detailed quote is attached as a PDF document. Please review it and let us know if you have any questions.

This quote is valid for 30 days from the date of issue.

Best regards,
{agency_name} Team

---
This is an automated email. Please do not reply directly to this message.
    """
    return text.strip()


def generate_welcome_email_html(
    full_name: str,
    organization_name: str,
    login_url: str,
) -> str:
    """Generate HTML welcome email template."""
    d, a, logo, site = NOUGRAM_BRAND_DARK, NOUGRAM_BRAND_ACCENT, NOUGRAM_BRAND_LOGO_URL, NOUGRAM_SITE_URL
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin:0;padding:0;background-color:#ebebf0;font-family:Arial,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#ebebf0;padding:24px 16px;"><tr><td align="center">
    <table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #d4d4dc;"><tr>
    <td style="padding:20px 24px;text-align:center;background:{d};">
    <a href="{site}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-block;">
    <img src="{logo}" alt="Nougram" width="140" style="display:block;margin:0 auto;border:0;max-width:140px;width:140px;height:auto;" /></a></td></tr><tr>
    <td style="background:{d};color:#fff;padding:24px 24px 28px;text-align:center;border-top:1px solid rgba(243,93,10,.25);">
    <h1 style="margin:0;font-size:22px;font-weight:600;">Bienvenido a Nougram</h1></td></tr><tr>
    <td style="padding:28px 24px;color:{d};line-height:1.6;font-size:15px;">
    <p style="margin:0 0 16px;">Hola <strong>{full_name}</strong>,</p>
    <p style="margin:0 0 16px;">Tu organización <strong>{organization_name}</strong> fue creada exitosamente.</p>
    <p style="margin:0 0 24px;">Ya puedes ingresar y completar tu configuración inicial.</p>
    <table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 auto;"><tr>
    <td style="border-radius:8px;background:{a};">
    <a href="{login_url}" style="display:inline-block;padding:12px 24px;color:#ffffff !important;text-decoration:none;font-weight:600;font-size:15px;">Ir a Nougram</a>
    </td></tr></table>
    <p style="margin:28px 0 0;font-size:12px;color:#5c5d70;">Si no reconoces este registro, contacta soporte.</p>
    </td></tr></table></td></tr></table>
    </body>
    </html>
    """


def generate_welcome_email_text(
    full_name: str,
    organization_name: str,
    login_url: str,
) -> str:
    """Generate plain-text welcome email template."""
    return f"""
Hola {full_name},

Tu organización {organization_name} fue creada exitosamente en Nougram.

Puedes ingresar aquí:
{login_url}

Si no reconoces este registro, contacta soporte.
    """.strip()


def generate_password_reset_email_html(
    full_name: str,
    reset_url: str,
    expiration_minutes: int,
) -> str:
    """Generate HTML password reset email template."""
    d, a, logo, site = NOUGRAM_BRAND_DARK, NOUGRAM_BRAND_ACCENT, NOUGRAM_BRAND_LOGO_URL, NOUGRAM_SITE_URL
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin:0;padding:0;background:#ebebf0;font-family:Arial,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#ebebf0;padding:24px 16px;"><tr><td align="center">
    <table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:12px;border:1px solid #d4d4dc;overflow:hidden;"><tr>
    <td style="padding:20px 24px;text-align:center;background:{d};">
    <a href="{site}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-block;">
    <img src="{logo}" alt="Nougram" width="140" style="display:block;margin:0 auto;border:0;max-width:140px;width:140px;height:auto;" /></a></td></tr><tr>
    <td style="padding:28px 24px;color:{d};line-height:1.6;font-size:15px;">
    <p style="margin:0 0 16px;">Hola <strong>{full_name}</strong>,</p>
    <p style="margin:0 0 20px;">Recibimos una solicitud para restablecer tu contraseña en Nougram.</p>
    <table role="presentation" cellspacing="0" cellpadding="0"><tr>
    <td style="border-radius:8px;background:{a};">
    <a href="{reset_url}" style="display:inline-block;padding:12px 24px;color:#ffffff !important;text-decoration:none;font-weight:600;font-size:15px;">Restablecer contraseña</a>
    </td></tr></table>
    <p style="margin:24px 0 8px;">Este enlace expira en <strong>{expiration_minutes} minutos</strong>.</p>
    <p style="margin:0;font-size:12px;color:#5c5d70;word-break:break-all;">Si el botón no funciona, copia este enlace:<br>
    <a href="{reset_url}" style="color:{a};">{reset_url}</a></p>
    <p style="margin:20px 0 0;font-size:12px;color:#5c5d70;">Si no solicitaste este cambio, puedes ignorar este correo.</p>
    </td></tr></table></td></tr></table>
    </body>
    </html>
    """


def generate_password_reset_email_text(
    full_name: str,
    reset_url: str,
    expiration_minutes: int,
) -> str:
    """Generate plain-text password reset email template."""
    return f"""
Hola {full_name},

Recibimos una solicitud para restablecer tu contraseña en Nougram.

Usa este enlace para crear una nueva contraseña:
{reset_url}

El enlace expira en {expiration_minutes} minutos.
Si no solicitaste este cambio, puedes ignorar este correo.
    """.strip()


def generate_email_verification_email_html(
    full_name: str,
    verification_url: str,
    expiration_minutes: int,
) -> str:
    """Generate HTML email verification template."""
    d, a, logo, site = NOUGRAM_BRAND_DARK, NOUGRAM_BRAND_ACCENT, NOUGRAM_BRAND_LOGO_URL, NOUGRAM_SITE_URL
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin:0;padding:0;background:#ebebf0;font-family:Arial,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#ebebf0;padding:24px 16px;"><tr><td align="center">
    <table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:12px;border:1px solid #d4d4dc;overflow:hidden;"><tr>
    <td style="padding:20px 24px;text-align:center;background:{d};">
    <a href="{site}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-block;">
    <img src="{logo}" alt="Nougram" width="140" style="display:block;margin:0 auto;border:0;max-width:140px;width:140px;height:auto;" /></a></td></tr><tr>
    <td style="padding:28px 24px;color:{d};line-height:1.6;font-size:15px;">
    <p style="margin:0 0 16px;">Hola <strong>{full_name}</strong>,</p>
    <p style="margin:0 0 20px;">Gracias por registrarte en Nougram. Para activar tu cuenta, confirma tu correo:</p>
    <table role="presentation" cellspacing="0" cellpadding="0"><tr>
    <td style="border-radius:8px;background:{a};">
    <a href="{verification_url}" style="display:inline-block;padding:12px 24px;color:#ffffff !important;text-decoration:none;font-weight:600;font-size:15px;">Verificar correo</a>
    </td></tr></table>
    <p style="margin:24px 0 8px;">Este enlace expira en <strong>{expiration_minutes} minutos</strong>.</p>
    <p style="margin:0;font-size:12px;color:#5c5d70;word-break:break-all;"><a href="{verification_url}" style="color:{a};">{verification_url}</a></p>
    </td></tr></table></td></tr></table>
    </body>
    </html>
    """


def generate_email_verification_email_text(
    full_name: str,
    verification_url: str,
    expiration_minutes: int,
) -> str:
    """Generate plain-text email verification template."""
    return f"""
Hola {full_name},

Gracias por registrarte en Nougram.
Para activar tu cuenta, verifica tu correo con este enlace:
{verification_url}

El enlace expira en {expiration_minutes} minutos.
    """.strip()
