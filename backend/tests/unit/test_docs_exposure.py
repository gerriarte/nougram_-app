"""
En producción no se publica el esquema de la API.

Origen: `main.py` apagaba `/docs` y `/redoc` en producción pero nunca seteaba
`openapi_url`, así que FastAPI seguía sirviendo su default `/openapi.json` — que es
exactamente de donde `/docs` saca todo. Verificado en vivo: `api.nougram.co/docs` daba
404 mientras `api.nougram.co/openapi.json` daba 200 con el esquema completo.

El test importa `main` con la env var pisada, en vez de chequear la app ya construida:
las tres URLs se resuelven en tiempo de import, así que es el único momento en que la
decisión ocurre.
"""

from __future__ import annotations

import importlib
import sys

import pytest

pytestmark = pytest.mark.unit


def _reload_main_with_environment(monkeypatch, environment: str):
    """Reimporta main.py con ENVIRONMENT pisada y devuelve el módulo."""
    from app.core import config

    monkeypatch.setattr(config.settings, "ENVIRONMENT", environment, raising=False)
    sys.modules.pop("main", None)
    return importlib.import_module("main")


@pytest.fixture(autouse=True)
def _restore_main():
    """Deja `main` fuera de sys.modules para no contaminar otros tests."""
    yield
    sys.modules.pop("main", None)


@pytest.mark.parametrize("environment", ["production", "PRODUCTION", "Production"])
def test_produccion_no_expone_docs_ni_esquema(monkeypatch, environment):
    """Las tres URLs se apagan juntas; el chequeo es case-insensitive."""
    main = _reload_main_with_environment(monkeypatch, environment)

    assert main._docs_url is None
    assert main._redoc_url is None
    assert main._openapi_url is None, (
        "openapi_url quedó abierto: /openapi.json publica cada endpoint, campo y schema "
        "de la API aunque /docs esté apagado"
    )
    assert main.app.openapi_url is None


@pytest.mark.parametrize("environment", ["development", "staging"])
def test_fuera_de_produccion_los_docs_siguen_disponibles(monkeypatch, environment):
    """Apagar el esquema en prod no puede romper el /docs de dev y staging."""
    main = _reload_main_with_environment(monkeypatch, environment)

    assert main._docs_url == "/docs"
    assert main._redoc_url == "/redoc"
    assert main._openapi_url == "/openapi.json"
