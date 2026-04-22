"""
PDF generation module for quotes
"""

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    currency_symbols = {"USD": "$", "COP": "$", "ARS": "$", "EUR": "€"}
    symbol = currency_symbols.get(currency, "$")

    # Format number with thousand separators
    if currency == "COP" or currency == "ARS":
        formatted = f"{amount:,.0f}"
    else:
        formatted = f"{amount:,.2f}"

    return f"{symbol} {formatted}"


def generate_quote_pdf(project, quote, agency_name: str = "Nougram") -> BytesIO:
    """
    Generate a professional PDF quote

    Args:
        project: Project SQLAlchemy model instance
        quote: Quote SQLAlchemy model instance with items and project loaded
        agency_name: Agency name for header

    Returns:
        BytesIO buffer containing the PDF
    """
    # Extract data from models
    project_name = project.name
    client_name = project.client_name
    client_email = project.client_email
    quote_version = quote.version
    currency = project.currency
    notes = quote.notes
    total_client_price = quote.total_client_price or 0
    margin_percentage = quote.margin_percentage or 0

    # Calculate taxes
    taxes = []
    total_taxes = 0
    if hasattr(project, "taxes") and project.taxes:
        for tax in project.taxes:
            tax_amount = (total_client_price * tax.percentage / 100) if tax.percentage else 0
            taxes.append(
                {
                    "name": tax.name,
                    "code": tax.code,
                    "percentage": tax.percentage,
                    "amount": tax_amount,
                }
            )
            total_taxes += tax_amount

    total_with_taxes = total_client_price + total_taxes

    # Extract quote items
    quote_items = []
    if hasattr(quote, "items") and quote.items:
        for item in quote.items:
            service_name = item.custom_service_name or (
                item.service.name if item.service else "Unknown Service"
            )
            hours = item.estimated_hours or 0
            client_price = item.client_price or 0

            quote_items.append(
                {
                    "service_name": service_name,
                    "estimated_hours": hours,
                    "client_price": client_price,
                }
            )

    # Extract expenses (Sprint 15)
    quote_expenses = []
    if hasattr(quote, "expenses") and quote.expenses:
        for expense in quote.expenses:
            quote_expenses.append(
                {
                    "name": expense.name,
                    "description": expense.description,
                    "cost": expense.cost,
                    "markup_percentage": expense.markup_percentage,
                    "client_price": expense.client_price,
                    "category": expense.category,
                    "quantity": expense.quantity,
                }
            )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=12,
        fontName="Helvetica-Bold",
    )

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#34495e"),
        spaceAfter=6,
    )

    # Header
    header_data = [
        [Paragraph(f"<b>{agency_name}</b>", title_style)],
        [Paragraph("Professional Quote", styles["Normal"])],
    ]
    header_table = Table(header_data, colWidths=[7 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
                ("FONTSIZE", (0, 0), (0, 0), 24),
                ("FONTSIZE", (0, 1), (0, 1), 10),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Quote info section
    quote_date = datetime.now().strftime("%B %d, %Y")
    quote_info_data = [
        ["Quote Date:", quote_date],
        ["Project:", project_name],
        ["Client:", client_name],
    ]

    if client_email:
        quote_info_data.append(["Email:", client_email])

    quote_info_data.append(["Quote Version:", f"v{quote_version}"])

    quote_info_table = Table(quote_info_data, colWidths=[2 * inch, 5 * inch])
    quote_info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecf0f1")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("FONTSIZE", (1, 0), (1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
            ]
        )
    )
    elements.append(quote_info_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Services table
    elements.append(Paragraph("Services", heading_style))

    # Table header
    table_data = [["Service", "Hours", "Rate", "Subtotal"]]

    # Add quote items
    for item in quote_items:
        service_name = item.get("service_name", "Unknown Service")
        hours = item.get("estimated_hours", 0)
        subtotal = item.get("client_price", 0)
        rate = subtotal / hours if hours > 0 else 0

        table_data.append(
            [
                service_name,
                f"{hours:.1f}",
                format_currency(rate, currency),
                format_currency(subtotal, currency),
            ]
        )

    # Create table
    services_table = Table(table_data, colWidths=[3.5 * inch, 1 * inch, 1.25 * inch, 1.25 * inch])
    services_table.setStyle(
        TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
                # Data rows
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                ("TOPPADDING", (0, 1), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                # Alternating row colors
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ]
        )
    )
    elements.append(services_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Expenses table (Sprint 15)
    if quote_expenses:
        elements.append(Paragraph("Third-Party Expenses", heading_style))

        expenses_table_data = [["Expense", "Category", "Cost", "Qty", "Markup", "Subtotal"]]

        for expense in quote_expenses:
            expenses_table_data.append(
                [
                    expense.get("name", "Unknown"),
                    expense.get("category", "-") or "-",
                    format_currency(expense.get("cost", 0), currency),
                    f"{expense.get('quantity', 1):.0f}",
                    f"{(expense.get('markup_percentage', 0) * 100):.1f}%",
                    format_currency(expense.get("client_price", 0), currency),
                ]
            )

        expenses_table = Table(
            expenses_table_data,
            colWidths=[2 * inch, 1 * inch, 1 * inch, 0.75 * inch, 0.75 * inch, 1.25 * inch],
        )
        expenses_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    # Data rows
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                    ("TOPPADDING", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                    # Alternating row colors
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f8f9fa")],
                    ),
                ]
            )
        )
        elements.append(expenses_table)
        elements.append(Spacer(1, 0.3 * inch))

    # Totals section
    elements.append(Paragraph("Summary", heading_style))

    totals_data = [["Subtotal:", format_currency(total_client_price, currency)]]

    # Add taxes if any
    if taxes and total_taxes > 0:
        for tax in taxes:
            tax_name = tax.get("name", "Tax")
            tax_amount = tax.get("amount", 0)
            totals_data.append([f"{tax_name}:", format_currency(tax_amount, currency)])

    totals_data.append(["<b>Total:</b>", f"<b>{format_currency(total_with_taxes, currency)}</b>"])

    totals_table = Table(totals_data, colWidths=[5 * inch, 2 * inch])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, -2), (-1, -2), 1, colors.HexColor("#34495e")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 12),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#2c3e50")),
            ]
        )
    )
    elements.append(totals_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Notes section
    if notes:
        elements.append(Paragraph("Notes", heading_style))
        notes_para = Paragraph(notes.replace("\n", "<br/>"), normal_style)
        elements.append(notes_para)
        elements.append(Spacer(1, 0.2 * inch))

    # Footer
    footer_text = f"This quote is valid for 30 days from the date of issue. Margin: {(margin_percentage * 100):.1f}%"
    footer_para = Paragraph(
        footer_text,
        ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#7f8c8d"),
            alignment=TA_CENTER,
            spaceBefore=20,
        ),
    )
    elements.append(footer_para)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
