"""
Regresión: el guardado de cargas sociales no debe pisar `total_percentage`.

`total_percentage` es la fuente de verdad país-agnóstica del recargo patronal
(commit 9e0458e). El desglose por concepto tiene forma colombiana y sus 8 campos
declaran defaults NO nulos en el schema, que suman 46.852%. La versión anterior
derivaba el total a partir de la mera PRESENCIA de esos campos en el dump, y como
`exclude_none=True` los conserva siempre, terminaba sobrescribiendo el valor
explícito del usuario con los defaults colombianos en cada guardado.
"""

import pytest

from app.api.v1.endpoints.organizations import (
    SOCIAL_CHARGES_BREAKDOWN_KEYS,
    resolve_social_charges_config,
)
from app.schemas.organization import SocialChargesConfig

# Suma de los defaults colombianos declarados en SocialChargesConfig.
COLOMBIAN_DEFAULT_TOTAL = pytest.approx(46.852)


@pytest.mark.unit
def test_total_explicito_no_se_pisa_con_el_desglose_por_defecto():
    """Una org no colombiana fija 30% y no manda desglose: debe quedar 30%."""
    config = SocialChargesConfig(enable_social_charges=True, total_percentage=30.0)

    resolved = resolve_social_charges_config(config)

    assert resolved["total_percentage"] == 30.0


@pytest.mark.unit
def test_total_explicito_gana_aunque_se_mande_desglose():
    """Si el usuario manda ambos, manda el total: es la fuente de verdad."""
    config = SocialChargesConfig(
        enable_social_charges=True,
        total_percentage=22.5,
        health_percentage=8.5,
        pension_percentage=12.0,
    )

    resolved = resolve_social_charges_config(config)

    assert resolved["total_percentage"] == 22.5


@pytest.mark.unit
def test_se_deriva_el_total_cuando_solo_se_manda_desglose():
    """Sin total explícito, la suma del desglose enviado es un fallback válido."""
    config = SocialChargesConfig(
        enable_social_charges=True,
        health_percentage=10.0,
        pension_percentage=15.0,
        arl_percentage=0.0,
        parafiscales_percentage=0.0,
        prima_services_percentage=0.0,
        cesantias_percentage=0.0,
        int_cesantias_percentage=0.0,
        vacations_percentage=0.0,
    )

    resolved = resolve_social_charges_config(config)

    assert resolved["total_percentage"] == pytest.approx(25.0)


@pytest.mark.unit
def test_sin_total_ni_desglose_no_se_inventa_un_total_colombiano():
    """
    El caso que rompía todo: el cliente no manda nada del desglose, pero el schema
    lo rellena con valores colombianos. No debe derivarse 46.852% de la nada.
    """
    config = SocialChargesConfig(enable_social_charges=True)

    resolved = resolve_social_charges_config(config)

    assert resolved.get("total_percentage") != COLOMBIAN_DEFAULT_TOTAL


@pytest.mark.unit
def test_guardados_repetidos_son_estables():
    """Guardar dos veces la misma config no debe desplazar el total (idempotencia)."""
    config = SocialChargesConfig(enable_social_charges=True, total_percentage=18.0)

    primero = resolve_social_charges_config(config)
    segundo = resolve_social_charges_config(
        SocialChargesConfig(
            **{k: v for k, v in primero.items() if k != "total_percentage"},
            total_percentage=primero["total_percentage"],
        )
    )

    assert primero["total_percentage"] == 18.0
    assert segundo["total_percentage"] == 18.0


@pytest.mark.unit
def test_los_defaults_del_schema_siguen_siendo_no_nulos():
    """
    Guarda la premisa del bug. Si algún día los defaults pasan a None, esta lógica
    puede simplificarse — y este test avisa.
    """
    config = SocialChargesConfig(enable_social_charges=True)
    dumped = config.model_dump(exclude_none=True)

    assert all(key in dumped for key in SOCIAL_CHARGES_BREAKDOWN_KEYS)
    assert sum(dumped[key] for key in SOCIAL_CHARGES_BREAKDOWN_KEYS) == COLOMBIAN_DEFAULT_TOTAL
