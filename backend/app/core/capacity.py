"""
Capacidad mensual de un miembro del equipo — IMPLEMENTACIÓN ÚNICA.

ESTÁNDAR NOUGRAM: Decimal en todo el camino, nunca float.

Decisión de producto (2026-07-27)
---------------------------------
`team_members.billable_hours_per_week` YA representa horas facturables. La UI lo
rotula así de forma explícita ("Horas Facturables / Semana" en
components/admin/payroll/TeamMemberForm.tsx y "Horas Facturables/Sem" en
components/admin/TeamMemberForm.tsx).

Antes, cinco lugares distintos volvían a multiplicar ese valor por
`(1 - non_billable_hours_percentage)`, descontando dos veces: una implícita en el
dato cargado por el usuario y otra explícita en el cálculo. El efecto era inflar el
BCR (menos horas en el denominador) y subestimar la capacidad del equipo.

Por eso la capacidad es simplemente horas_semanales × semanas_por_mes.

`non_billable_hours_percentage` sigue existiendo como dato informativo del miembro
(y se muestra en la UI como "% Admin"), pero NO participa del cálculo de capacidad.
Si alguna vez se decide lo contrario, el cambio va acá y en ningún otro lado.
"""

from decimal import Decimal
from typing import Any

# Promedio de semanas por mes (52 / 12). Constante compartida por todo el backend.
WEEKS_PER_MONTH = Decimal("4.33")


def monthly_billable_hours(member: Any) -> Decimal:
    """
    Horas facturables al mes de un miembro.

    Tolera `None` y valores no numéricos devolviendo 0: ningún consumidor debería
    romperse por un dato incompleto, y una capacidad de 0 es la lectura conservadora
    (no se le puede asignar trabajo).
    """
    raw = getattr(member, "billable_hours_per_week", None)
    if raw is None:
        return Decimal("0")
    try:
        weekly = Decimal(str(raw))
    except (ArithmeticError, ValueError, TypeError):
        return Decimal("0")
    if weekly <= 0:
        return Decimal("0")
    return weekly * WEEKS_PER_MONTH


def total_monthly_billable_hours(members: list[Any]) -> Decimal:
    """Suma de la capacidad mensual de una lista de miembros (denominador del BCR)."""
    total = Decimal("0")
    for member in members or []:
        total += monthly_billable_hours(member)
    return total
