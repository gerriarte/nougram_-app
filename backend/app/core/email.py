"""
Email sending module for quotes and notifications
"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from io import BytesIO

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
    attachments: Optional[List[dict]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> bool:
    """
    Send an email using SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML email body
        body_text: Plain text email body (optional, will be generated from HTML if not provided)
        attachments: List of attachments with 'filename' and 'content' (BytesIO) keys
        cc: List of CC email addresses
        bcc: List of BCC email addresses
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Check if email is configured
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("Email not configured. SMTP settings missing.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if cc:
            msg['Cc'] = ', '.join(cc)
        
        # Add body
        if body_text:
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)
        
        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                filename = attachment.get('filename', 'attachment')
                content = attachment.get('content')
                
                if content:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(content.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
                    content.seek(0)  # Reset for potential reuse
        
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
            recipients=recipients
        )
        
        logger.info(f"Email sent successfully to {to_email}", subject=subject)
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {to_email}", error=str(e), exc_info=True)
        return False


def generate_quote_email_html(
    project_name: str,
    client_name: str,
    quote_version: int,
    total_with_taxes: float,
    currency: str = "USD",
    notes: Optional[str] = None,
    agency_name: str = "Nougram"
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
    currency_symbols = {
        "USD": "$",
        "COP": "$",
        "ARS": "$",
        "EUR": "€"
    }
    symbol = currency_symbols.get(currency, "$")
    formatted_amount = f"{symbol} {total_with_taxes:,.2f}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                background-color: #f9f9f9;
                padding: 20px;
                border: 1px solid #ddd;
            }}
            .quote-info {{
                background-color: white;
                padding: 15px;
                margin: 15px 0;
                border-left: 4px solid #3498db;
            }}
            .total {{
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                text-align: center;
                padding: 20px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                color: #7f8c8d;
                font-size: 12px;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{agency_name}</h1>
            <p>Quote #{quote_version}</p>
        </div>
        <div class="content">
            <p>Dear {client_name},</p>
            <p>Thank you for your interest in our services. Please find attached the quote for <strong>{project_name}</strong>.</p>
            
            <div class="quote-info">
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Quote Version:</strong> {quote_version}</p>
            </div>
            
            <div class="total">
                Total: {formatted_amount}
            </div>
            
            {f'<p><strong>Notes:</strong><br>{notes}</p>' if notes else ''}
            
            <p>The detailed quote is attached as a PDF document. Please review it and let us know if you have any questions.</p>
            
            <p>This quote is valid for 30 days from the date of issue.</p>
            
            <p>Best regards,<br>{agency_name} Team</p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply directly to this message.</p>
        </div>
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
    notes: Optional[str] = None,
    agency_name: str = "Nougram"
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
    currency_symbols = {
        "USD": "$",
        "COP": "$",
        "ARS": "$",
        "EUR": "€"
    }
    symbol = currency_symbols.get(currency, "$")
    formatted_amount = f"{symbol} {total_with_taxes:,.2f}"
    
    text = f"""
{agency_name} - Quote #{quote_version}

Dear {client_name},

Thank you for your interest in our services. Please find attached the quote for {project_name}.

Project: {project_name}
Quote Version: {quote_version}
Total: {formatted_amount}

{f'Notes: {notes}' if notes else ''}

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
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                border: 1px solid #e5e7eb;
                border-top: none;
                padding: 24px;
                border-radius: 0 0 8px 8px;
                background-color: #ffffff;
            }}
            .button {{
                display: inline-block;
                margin-top: 16px;
                padding: 10px 16px;
                background-color: #2563eb;
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            .footer {{
                margin-top: 20px;
                color: #6b7280;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Bienvenido a Nougram</h2>
        </div>
        <div class="content">
            <p>Hola <strong>{full_name}</strong>,</p>
            <p>Tu organización <strong>{organization_name}</strong> fue creada exitosamente.</p>
            <p>Ya puedes ingresar y completar tu configuración inicial.</p>
            <p>
                <a class="button" href="{login_url}">Ir a Nougram</a>
            </p>
            <p class="footer">Si no reconoces este registro, responde a este correo o contacta soporte.</p>
        </div>
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
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 24px;
                background-color: #ffffff;
            }}
            .button {{
                display: inline-block;
                margin: 16px 0;
                padding: 10px 16px;
                background-color: #2563eb;
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            .small {{
                color: #6b7280;
                font-size: 12px;
                word-break: break-word;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p>Hola <strong>{full_name}</strong>,</p>
            <p>Recibimos una solicitud para restablecer tu contraseña en Nougram.</p>
            <p>
                <a class="button" href="{reset_url}">Restablecer contraseña</a>
            </p>
            <p>Este enlace expira en <strong>{expiration_minutes} minutos</strong>.</p>
            <p class="small">Si el botón no funciona, copia este enlace en tu navegador:</p>
            <p class="small">{reset_url}</p>
        </div>
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












