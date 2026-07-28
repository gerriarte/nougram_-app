"""
Tests de arquitectura: una sola implementación por concepto financiero.

La causa raíz de la mayoría de los bugs de dinero de este proyecto no fue una función
mal escrita: fue la MISMA fórmula copiada en varios lugares que después divergieron.
Se llegaron a tener siete copias del multiplicador de cargas sociales, dos cálculos de
BCR que diferían por 3472x, nueve fallbacks silenciosos a USD y cinco copias de la
capacidad mensual (una de ellas con doble descuento de horas).

Estos tests son baratos (grep sobre el árbol) y corren en cada push. No prueban que el
cálculo sea correcto: prueban que hay UN SOLO lugar donde puede estar mal.

Si un test de acá falla, la respuesta correcta casi nunca es agregar una excepción:
es llamar a la implementación única. Si de verdad hace falta una excepción, agregala a
la lista con un comentario que explique por qué.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

APP = Path(__file__).resolve().parents[2] / "app"


def _archivos_python(excluir: set[str]) -> list[Path]:
    """Todos los .py de app/, menos los dueños del concepto."""
    return [
        p
        for p in APP.rglob("*.py")
        if "__pycache__" not in p.parts and p.relative_to(APP).as_posix() not in excluir
    ]


def _lineas_de_codigo(path: Path) -> list[tuple[int, str]]:
    """Líneas no vacías que no son comentario (evita falsos positivos en docs)."""
    out = []
    for i, linea in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        out.append((i, linea))
    return out


def _buscar(patron: str, excluir: set[str]) -> list[str]:
    rx = re.compile(patron)
    hallazgos = []
    for path in _archivos_python(excluir):
        for numero, linea in _lineas_de_codigo(path):
            if rx.search(linea):
                hallazgos.append(f"{path.relative_to(APP).as_posix()}:{numero}: {linea.strip()}")
    return hallazgos


def test_la_capacidad_mensual_se_calcula_en_un_solo_lugar():
    """
    `billable_hours_per_week × semanas` solo puede vivir en app/core/capacity.py.

    Origen: H49. Cinco copias de la fórmula, y una volvía a descontar el % no facturable
    sobre un campo que la UI ya declara como facturable, inflando el BCR.
    """
    duenios = {
        "core/capacity.py",
        # Convierte horas MENSUALES del onboarding a semanales para persistirlas.
        # Es la operación inversa, no un cálculo de capacidad.
        "services/onboarding_service.py",
        # Suma en SQL (func.sum) sobre la columna: no puede llamar al helper de Python.
        # Sin doble descuento, así que es consistente con capacity.py.
        "api/v1/endpoints/insights.py",
    }
    hallazgos = _buscar(r"billable_hours_per_week.*4\.33|4\.33.*billable_hours_per_week", duenios)

    assert not hallazgos, "Capacidad recalculada fuera de capacity.py:\n" + "\n".join(hallazgos)


def test_no_queda_ningun_descuento_de_horas_no_facturables_en_capacidad():
    """
    Nadie puede multiplicar por `(1 - non_billable_hours_percentage)`.

    Decisión de producto 2026-07-27: `billable_hours_per_week` YA es facturable.
    """
    # capacity.py es el dueño del concepto y documenta la regla en su docstring.
    hallazgos = _buscar(r"1\s*\)?\s*-\s*.*non_billable", {"core/capacity.py"})

    assert not hallazgos, "Doble descuento de horas reintroducido:\n" + "\n".join(hallazgos)


def test_la_moneda_primaria_se_resuelve_en_un_solo_lugar():
    """
    Nadie puede hacer `get("primary_currency", "USD")`: hay que usar resolve_primary_currency.

    Origen: nueve fallbacks silenciosos a USD dispersos hacían que una agencia colombiana
    con todos sus datos en COP cotizara en USD dividiendo por 4000.
    """
    hallazgos = _buscar(
        r'get\(\s*["\']primary_currency["\']\s*,\s*["\']USD["\']\s*\)', {"core/currency.py"}
    )

    assert not hallazgos, "Fallback silencioso a USD reintroducido:\n" + "\n".join(hallazgos)


# Deuda conocida: módulos que todavía leen el dict de floats EXCHANGE_RATES_TO_USD en
# vez de convert_currency / EXCHANGE_RATES_TO_USD_DECIMAL. Cada uno hace round-trip por
# float sobre una tasa que ya existe en Decimal, violando el estándar de dinero.
# Es un TRINQUETE: el número solo puede bajar. Al migrar un módulo, sacalo de acá.
DEUDA_TASAS_EN_FLOAT = {
    "services/exchange_rate_service.py",
    "services/onboarding_service.py",
    "services/settings_service.py",
    "api/v1/endpoints/costs.py",
}


def test_las_tasas_de_cambio_no_se_leen_en_modulos_nuevos():
    """
    La tabla de tasas es de app/core/currency.py; nadie NUEVO puede importarla.

    Origen: tasas hardcodeadas con un comentario que decía "update with real rates",
    consumidas desde varios módulos y convertidas ida y vuelta por float.

    Los 4 módulos de DEUDA_TASAS_EN_FLOAT ya lo hacían antes de este trabajo y migrarlos
    excede el alcance de este cambio. Este test evita que la lista CREZCA, que es lo que
    importa: la deuda que no crece se termina pagando.
    """
    duenios = {"core/currency.py", "core/config.py"} | DEUDA_TASAS_EN_FLOAT
    hallazgos = _buscar(r"EXCHANGE_RATES_TO_USD\b(?!_DECIMAL)", duenios)

    assert not hallazgos, (
        "Módulo NUEVO leyendo tasas en float (usá convert_currency o "
        "EXCHANGE_RATES_TO_USD_DECIMAL):\n" + "\n".join(hallazgos)
    )


def test_la_deuda_de_tasas_en_float_no_crece():
    """
    Trinquete: si migrás un módulo, este test te obliga a achicar DEUDA_TASAS_EN_FLOAT.

    Sin esto, la lista de excepciones se vuelve un cementerio que nadie limpia.
    """
    rx = re.compile(r"EXCHANGE_RATES_TO_USD\b(?!_DECIMAL)")
    ya_migrados = set()
    for modulo in DEUDA_TASAS_EN_FLOAT:
        path = APP / modulo
        if not path.exists():
            ya_migrados.add(f"{modulo} (el archivo ya no existe)")
            continue
        if not any(rx.search(linea) for _, linea in _lineas_de_codigo(path)):
            ya_migrados.add(modulo)

    assert not ya_migrados, (
        "Estos módulos ya no usan tasas en float: sacalos de DEUDA_TASAS_EN_FLOAT\n"
        + "\n".join(sorted(ya_migrados))
    )
