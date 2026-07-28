"""
Invariantes del dominio de dinero.

Estos tests NO verifican una función: verifican PROPIEDADES que deben valer en todo el
sistema, con entradas generadas al azar. La diferencia importa: un test de ejemplo caza
el bug que ya conocés, un invariante caza la clase entera.

Cada invariante de acá salió de un bug real de este proyecto. La referencia está en el
docstring de cada test para que, si alguno se vuelve molesto, se pueda decidir con
contexto si el invariante está mal o si el código volvió a romperse.
"""

from decimal import Decimal

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from app.core.capacity import WEEKS_PER_MONTH, monthly_billable_hours
from app.core.currency import CURRENCY_INFO, convert_currency
from app.core.money import Money, sum_money
from app.core.social_charges import resolve_social_charges_multiplier

pytestmark = pytest.mark.unit

MONEDAS = sorted(CURRENCY_INFO.keys())

# Importes con forma de dinero real: hasta miles de millones (COP), 2 decimales.
importes = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("1e10"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)
monedas = st.sampled_from(MONEDAS)


class _Miembro:
    """Doble mínimo de TeamMember: capacity solo mira estos dos atributos."""

    def __init__(self, billable_hours_per_week, non_billable_hours_percentage=Decimal("0")):
        self.billable_hours_per_week = billable_hours_per_week
        self.non_billable_hours_percentage = non_billable_hours_percentage


# ── Invariante 1 ────────────────────────────────────────────────────────────
@given(monto=importes, moneda=monedas)
def test_convertir_a_la_misma_moneda_es_identidad_exacta(monto, moneda):
    """
    Convertir de una moneda a sí misma NO puede perder precisión ni cambiar el tipo.

    Es el camino feliz de toda organización bien configurada, así que cualquier
    degradación acá contamina el 100% de los cálculos. Origen: H09/W I-4, donde
    `from == to` pasaba por float y devolvía float en vez de Decimal.
    """
    resultado = convert_currency(monto, moneda, moneda)

    assert resultado == monto
    assert isinstance(resultado, Decimal), f"devolvió {type(resultado).__name__}, no Decimal"


# ── Invariante 2 ────────────────────────────────────────────────────────────
@given(monto=importes, moneda=monedas)
def test_convertir_es_reversible_dentro_de_una_tolerancia_relativa(monto, moneda):
    """
    Ida y vuelta entre dos monedas debe recuperar el original salvo redondeo.

    Si esto falla, hay una tasa asimétrica o una pérdida de precisión en el medio.
    """
    assume(monto > Decimal("1"))

    ida = convert_currency(monto, moneda, "USD")
    vuelta = convert_currency(Decimal(str(ida)), "USD", moneda)

    error_relativo = abs(Decimal(str(vuelta)) - monto) / monto
    assert error_relativo < Decimal("0.0001"), f"{monto} {moneda} -> USD -> {vuelta}"


# ── Invariante 3 ────────────────────────────────────────────────────────────
@given(
    montos=st.lists(importes, min_size=1, max_size=8),
    moneda=monedas,
)
def test_sumar_dinero_preserva_la_moneda_y_el_total(montos, moneda):
    """
    sum_money no puede cambiar la moneda ni desviarse de la suma aritmética.

    Origen: el hallazgo transversal de "agregados que mezclan monedas". Un agregado
    que devuelve otra moneda es la firma exacta de una normalización olvidada.
    """
    total = sum_money([Money(m, moneda) for m in montos])

    assert total is not None
    assert total.currency == moneda
    assert total.amount == sum(montos)


# ── Invariante 4 ────────────────────────────────────────────────────────────
@given(
    horas_semana=st.integers(min_value=0, max_value=80),
    no_facturable=st.decimals(min_value=Decimal("0"), max_value=Decimal("0.9"), places=2),
)
def test_la_capacidad_no_depende_del_porcentaje_no_facturable(horas_semana, no_facturable):
    """
    `billable_hours_per_week` YA es facturable: el % no facturable no debe descontarse.

    Origen: H49. Cinco lugares distintos aplicaban `× (1 - non_billable)` sobre un campo
    que la UI rotula "Horas Facturables / Semana", descontando dos veces e inflando el BCR.
    Decisión de producto del 2026-07-27: el campo es solo horas facturables.
    """
    sin_descuento = _Miembro(horas_semana, Decimal("0"))
    con_descuento = _Miembro(horas_semana, no_facturable)

    assert monthly_billable_hours(sin_descuento) == monthly_billable_hours(con_descuento)
    assert monthly_billable_hours(con_descuento) == Decimal(str(horas_semana)) * WEEKS_PER_MONTH


# ── Invariante 5 ────────────────────────────────────────────────────────────
@given(
    total=st.decimals(min_value=Decimal("0"), max_value=Decimal("200"), places=3),
)
def test_el_multiplicador_de_cargas_sociales_nunca_reduce_el_costo(total):
    """
    El recargo patronal SUMA sobre el sueldo: el multiplicador nunca puede ser < 1.

    Un multiplicador menor que 1 significaría que emplear a alguien sale más barato que
    su sueldo bruto, que es imposible. Origen: H37, donde una config legacy daba
    multiplicador 1 en un lado y 1.46852 en otro, y un `None` reventaba el cálculo.
    """
    config = {"enable_social_charges": True, "total_percentage": float(total)}

    multiplicador = resolve_social_charges_multiplier(config)

    assert multiplicador >= Decimal("1")
    assert isinstance(multiplicador, Decimal)


@pytest.mark.parametrize(
    "config",
    [
        None,
        {},
        {"enable_social_charges": False},
        {"enable_social_charges": True},
        {"enable_social_charges": True, "total_percentage": None},
        {"enable_social_charges": True, "total_percentage": 0},
    ],
)
def test_el_multiplicador_tolera_toda_config_degenerada(config):
    """
    Ninguna forma de config —incluida `total_percentage: None`— puede lanzar excepción.

    Origen: H37. `Decimal(str(None))` levantaba decimal.InvalidOperation y tumbaba el
    endpoint entero de proyección anual. Todas estas formas son creables hoy vía API.
    """
    multiplicador = resolve_social_charges_multiplier(config)

    assert isinstance(multiplicador, Decimal)
    assert multiplicador >= Decimal("1")
