"""
Contingencia e impuestos de un presupuesto — IMPLEMENTACIÓN ÚNICA.

ESTÁNDAR NOUGRAM: todo en Decimal.

La regla (una sola, para todos los caminos de lectura)
------------------------------------------------------
El impuesto grava el precio SIN la contingencia; la contingencia se suma DESPUÉS.
Así lo calcula el preview en ``POST /quotes/calculate`` y así se persiste el total.

El problema es que la tabla ``quotes`` NO persiste el impuesto: cada lectura lo
recalcula sobre ``quote.total_client_price``, que ya viene contingenciado. Gravar
ese número entero infla el impuesto en ``tasa × contingencia``. Con 1.000.000 +
10% de contingencia + IVA 19%, el PDF que recibía el cliente decía 1.309.000 y la
pantalla decía 1.290.000: el mismo presupuesto valía distinto según dónde se lo
mirara. Como ``contingency_type`` y ``contingency_value`` sí están persistidos, la
base imponible se reconstruye exactamente, sin migración.

Este módulo vive en ``core`` y no importa nada de ``services`` a propósito: sus
consumidores son los generadores de documentos (``pdf_generator``,
``docx_generator``), ``calculations`` y los endpoints, y cualquiera de esas
dependencias hacia ``services.project_service`` sería circular.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

# Valores que representan "no hay contingencia" en la columna contingency_type.
_SIN_CONTINGENCIA = (None, "", "none")


def _to_decimal(value: Any) -> Decimal:
    """Decimal tolerante: cualquier cosa no convertible vale 0 en vez de reventar."""
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def normalize_contingency(
    contingency_type: str | None,
    contingency_value: Decimal | float | None,
) -> tuple[str | None, Decimal]:
    """Devuelve (tipo, valor) sanitizados; tipo None significa 'sin contingencia'."""
    if contingency_type is None or contingency_value is None:
        return None, Decimal("0")
    if str(contingency_type).strip().lower() in _SIN_CONTINGENCIA:
        return None, Decimal("0")
    value = _to_decimal(contingency_value)
    if value <= 0:
        return None, Decimal("0")
    return contingency_type, value


def add_contingency_to_price(
    base_price: Decimal,
    contingency_type: str | None,
    contingency_value: Decimal | float | None,
) -> Decimal:
    """Precio final = base gravable + contingencia. Versión Decimal de la regla del preview."""
    ctype, value = normalize_contingency(contingency_type, contingency_value)
    if ctype is None:
        return base_price
    if ctype == "fixed":
        return base_price + value
    return base_price + (base_price * (value / Decimal("100")))


def quote_taxable_base(
    total_client_price: Decimal | float | None,
    contingency_type: str | None,
    contingency_value: Decimal | float | None,
) -> Decimal:
    """
    Base imponible de un presupuesto ya guardado: el precio SIN la contingencia.

    Es la inversa exacta de add_contingency_to_price().
    """
    price = _to_decimal(total_client_price)

    ctype, value = normalize_contingency(contingency_type, contingency_value)
    if ctype is None:
        return price

    if ctype == "fixed":
        base = price - value
    else:
        divisor = Decimal("1") + (value / Decimal("100"))
        if divisor <= 0:
            return price
        base = price / divisor

    return base if base > 0 else Decimal("0")


def compute_quote_tax_lines(
    total_client_price: Decimal | float | None,
    contingency_type: str | None,
    contingency_value: Decimal | float | None,
    taxes: list[Any],
) -> tuple[list[dict[str, Any]], Decimal, Decimal]:
    """
    Detalle por impuesto + agregados, para los caminos que imprimen cada línea.

    Cada elemento de `taxes` es un modelo Tax (o cualquier objeto con name/code/
    percentage). El importe de cada línea se calcula sobre la base sin contingencia,
    igual que compute_quote_tax_totals(), de modo que el desglose siempre suma el
    total: si cada línea se calculara sobre otra base, el PDF se contradiría solo.

    Returns:
        (líneas, total_taxes, total_with_taxes)
    """
    price = _to_decimal(total_client_price)
    taxable_base = quote_taxable_base(price, contingency_type, contingency_value)

    lines: list[dict[str, Any]] = []
    total_taxes = Decimal("0")
    for tax in taxes or []:
        percentage = getattr(tax, "percentage", None)
        if percentage is None:
            continue
        amount = (taxable_base * _to_decimal(percentage)) / Decimal("100")
        total_taxes += amount
        lines.append(
            {
                "name": getattr(tax, "name", None),
                "code": getattr(tax, "code", None),
                "percentage": percentage,
                "amount": amount,
            }
        )

    return lines, total_taxes, price + total_taxes


def compute_quote_tax_totals(
    total_client_price: Decimal | float | None,
    contingency_type: str | None,
    contingency_value: Decimal | float | None,
    tax_percentages: list[Decimal | float | None],
) -> tuple[Decimal, Decimal]:
    """
    (total_taxes, total_with_taxes) para un presupuesto persistido.

    Los impuestos gravan la base sin contingencia; la contingencia se suma después.
    """
    price = _to_decimal(total_client_price)
    taxable_base = quote_taxable_base(price, contingency_type, contingency_value)

    total_taxes = Decimal("0")
    for percentage in tax_percentages:
        if percentage is None:
            continue
        total_taxes += (taxable_base * _to_decimal(percentage)) / Decimal("100")

    return total_taxes, price + total_taxes
