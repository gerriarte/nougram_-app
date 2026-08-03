"""
Resolución canónica del recargo patronal (cargas sociales).

ESTÁNDAR NOUGRAM: todo en Decimal.

Precedencia (país-agnóstica, decidida en el commit 9e0458e y unificada acá):
1. `total_percentage` es la FUENTE DE VERDAD del recargo patronal.
2. El desglose por concepto (health/pension/arl/... estilo Colombia) es
   informativo y solo se usa como fallback para configs legacy que se
   guardaron sin `total_percentage`.

Este módulo existe para que exista UNA sola implementación: antes había cuatro
copias divergentes (calculations.calculate_blended_cost_rate,
calculations.get_organization_cost_breakdown, endpoints/costs.py y
business_health._social_charges_multiplier) y dos de ellas ignoraban
`total_percentage`, con lo que el mismo endpoint se contradecía a sí mismo.
"""

from decimal import Decimal

from app.core.logging import get_logger

logger = get_logger(__name__)

BREAKDOWN_KEYS: tuple[str, ...] = (
    "health_percentage",
    "pension_percentage",
    "arl_percentage",
    "parafiscales_percentage",
    "prima_services_percentage",
    "cesantias_percentage",
    "int_cesantias_percentage",
    "vacations_percentage",
)


# Desvíos ya reportados, para avisar una vez por combinación (total, desglose) y no una vez
# por cada sueldo de cada cálculo. Mismo patrón que _WARNED_PLACEHOLDER_PAIRS en currency.py.
_WARNED_BREAKDOWN_DIVERGENCES: set[tuple[str, str]] = set()

# El desglose de los presets es informativo y NO cuadra con el total por diseño: el preset CO
# declara total 52.852 contra un desglose de 46.852 (11,4% de desvío relativo). Avisar por debajo
# de ese umbral sería ruido permanente en toda org colombiana, así que solo se reporta el desvío
# groseramente mayor, que es el que delata una config editada a mano y desincronizada.
BREAKDOWN_DIVERGENCE_THRESHOLD = Decimal("0.25")


def sum_breakdown_percentage(social_config: dict | None) -> Decimal:
    """Suma del desglose por concepto (health/pension/...), sin mirar `total_percentage`."""
    if not social_config:
        return Decimal("0")
    total = Decimal("0")
    for key in BREAKDOWN_KEYS:
        total += Decimal(str(social_config.get(key, 0) or 0))
    return total


def _warn_if_breakdown_diverges(social_config: dict, total_percentage: Decimal) -> None:
    """
    Avisa cuando `total_percentage` (lo que se cobra) y el desglose (lo que muestra la UI)
    cuentan historias distintas. La precedencia no cambia: total_percentage sigue ganando.
    """
    breakdown = sum_breakdown_percentage(social_config)
    if breakdown <= 0 or total_percentage <= 0:
        return
    divergence = abs(total_percentage - breakdown) / total_percentage
    if divergence < BREAKDOWN_DIVERGENCE_THRESHOLD:
        return
    signature = (str(total_percentage), str(breakdown))
    if signature in _WARNED_BREAKDOWN_DIVERGENCES:
        return
    _WARNED_BREAKDOWN_DIVERGENCES.add(signature)
    logger.warning(
        "social_charges_config: total_percentage y el desglose por concepto divergen; "
        "se usa total_percentage (fuente de verdad) y la UI muestra el desglose.",
        total_percentage=str(total_percentage),
        breakdown_sum=str(breakdown),
        divergence_ratio=str(divergence.quantize(Decimal("0.0001"))),
        module="social_charges",
        function="resolve_social_charges_percentage",
    )


def resolve_social_charges_percentage(social_config: dict | None) -> Decimal:
    """
    Porcentaje total de cargas sociales (ej: Decimal('52.852')).

    Devuelve Decimal('0') si la config es None, está deshabilitada o no tiene datos.
    """
    if not social_config:
        return Decimal("0")

    if not social_config.get("enable_social_charges", False):
        return Decimal("0")

    total_percentage = Decimal(str(social_config.get("total_percentage", 0) or 0))

    if total_percentage == 0:
        # Fallback legacy: sumar el desglose si no hay total guardado.
        total_percentage = sum_breakdown_percentage(social_config)
    else:
        _warn_if_breakdown_diverges(social_config, total_percentage)

    if total_percentage < 0:
        return Decimal("0")

    return total_percentage


def resolve_social_charges_multiplier(social_config: dict | None) -> Decimal:
    """
    Multiplicador a aplicar sobre el sueldo bruto: 1 + (total_percentage / 100).

    Devuelve Decimal('1') (exacto, sin escala decimal) cuando no hay cargas sociales
    configuradas o habilitadas, para no alterar la escala de los importes que multiplica.
    """
    total_percentage = resolve_social_charges_percentage(social_config)
    if total_percentage <= 0:
        return Decimal("1")
    return Decimal("1") + (total_percentage / Decimal("100"))
