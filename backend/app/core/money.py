"""
Money handling utilities using Decimal for precision
ESTÁNDAR NOUGRAM: Precisión financiera grado bancario
"""

from decimal import ROUND_HALF_UP, Decimal

from app.core.logging import get_logger

logger = get_logger(__name__)

# Precisión estándar: 4 decimales para cálculos internos, 2 para display
INTERNAL_PRECISION = Decimal("0.0001")
DISPLAY_PRECISION = Decimal("0.01")

# COP no usa decimales en display pero sí en cálculos internos
COP_DISPLAY_PRECISION = Decimal("1")  # Sin decimales
COP_INTERNAL_PRECISION = Decimal("0.01")  # Precisión interna para cálculos

# ESTÁNDAR NOUGRAM: Usar ROUND_HALF_UP (no banker's rounding ROUND_HALF_EVEN)
# Esto asegura consistencia con Dinero.js que usa "round half up"
# Python usa ROUND_HALF_EVEN por defecto, debemos especificar explícitamente
ROUNDING_MODE = ROUND_HALF_UP  # NO ROUND_HALF_EVEN


class Money:
    """
    Clase inmutable para representar dinero con precisión Decimal
    ESTÁNDAR NOUGRAM: Todas las operaciones generan nuevas instancias
    """

    def __init__(self, amount: float | int | str | Decimal, currency: str = "USD"):
        if isinstance(amount, Decimal):
            self._amount = amount
        elif isinstance(amount, str):
            self._amount = Decimal(amount)
        else:
            # Convertir float a string primero para evitar pérdida de precisión
            self._amount = Decimal(str(amount))

        self._currency = currency.upper()

        # Validar que el monto no sea negativo (a menos que sea explícitamente permitido)
        if self._amount < 0:
            logger.warning(f"Negative amount detected: {self._amount} {self._currency}")

    @property
    def amount(self) -> Decimal:
        """Retorna el monto como Decimal"""
        return self._amount

    @property
    def currency(self) -> str:
        """Retorna la moneda"""
        return self._currency

    def to_float(self) -> float:
        """Convierte a float (usar solo para compatibilidad con API)"""
        return float(self._amount)

    def to_int_cents(self) -> int:
        """Convierte a centavos/subunidades (para API)"""
        if self._currency == "COP":
            # COP ya está en unidades enteras
            return int(self._amount)
        # Otras monedas: multiplicar por 100
        return int(self._amount * 100)

    def quantize(self, precision: Decimal | None = None) -> "Money":
        """Redondea a la precisión especificada usando ROUND_HALF_UP"""
        if precision is None:
            precision = DISPLAY_PRECISION if self._currency != "COP" else COP_DISPLAY_PRECISION

        quantized = self._amount.quantize(precision, rounding=ROUNDING_MODE)
        return Money(quantized, self._currency)

    def add(self, other: "Money") -> "Money":
        """Suma dos montos (debe ser misma moneda)"""
        if self._currency != other._currency:
            raise ValueError(f"Cannot add {self._currency} and {other._currency}")
        return Money(self._amount + other._amount, self._currency)

    def subtract(self, other: "Money") -> "Money":
        """Resta dos montos (debe ser misma moneda)"""
        if self._currency != other._currency:
            raise ValueError(f"Cannot subtract {self._currency} and {other._currency}")
        return Money(self._amount - other._amount, self._currency)

    def multiply(self, multiplier: float | Decimal) -> "Money":
        """Multiplica un monto por un escalar"""
        if isinstance(multiplier, float):
            multiplier = Decimal(str(multiplier))
        result = self._amount * multiplier
        return Money(result, self._currency)

    def divide(self, divisor: float | Decimal) -> "Money":
        """Divide un monto por un escalar"""
        if isinstance(divisor, float):
            divisor = Decimal(str(divisor))
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        result = self._amount / divisor
        return Money(result, self._currency)

    def apply_percentage(self, percentage: float | Decimal) -> "Money":
        """Aplica un porcentaje (ej: 19% de IVA)"""
        if isinstance(percentage, float):
            percentage = Decimal(str(percentage))
        multiplier = percentage / Decimal("100")
        return self.multiply(multiplier)

    def apply_margin(self, margin_percentage: float | Decimal) -> "Money":
        """
        Calcula precio con margen: cost / (1 - margin)
        Ejemplo: cost = $100, margin = 40% → price = $100 / (1 - 0.40) = $166.67
        """
        # #region agent log
        import json
        import os

        try:
            log_data = {
                "location": "money.py:116",
                "message": "apply_margin called",
                "data": {
                    "margin_percentage": str(margin_percentage),
                    "margin_percentage_type": str(type(margin_percentage).__name__),
                    "amount": str(self._amount),
                    "currency": self._currency,
                },
                "timestamp": __import__("time").time() * 1000,
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
            }
            log_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".cursor", "debug.log"
            )
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion

        if isinstance(margin_percentage, float):
            margin_percentage = Decimal(str(margin_percentage))

        # #region agent log
        try:
            log_data = {
                "location": "money.py:140",
                "message": "after float conversion",
                "data": {
                    "margin_percentage": str(margin_percentage),
                    "margin_percentage_type": str(type(margin_percentage).__name__),
                },
                "timestamp": __import__("time").time() * 1000,
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion

        if margin_percentage >= 100:
            raise ValueError("Margin cannot be >= 100%")

        # #region agent log
        try:
            log_data = {
                "location": "money.py:155",
                "message": "before division",
                "data": {
                    "margin_percentage": str(margin_percentage),
                    "margin_percentage_type": str(type(margin_percentage).__name__),
                    "dividing_by": "100 (Decimal)",
                },
                "timestamp": __import__("time").time() * 1000,
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion

        margin_decimal = margin_percentage / Decimal("100")
        divisor = Decimal("1") - margin_decimal

        if divisor == 0:
            raise ValueError("Cannot apply 100% margin (division by zero)")

        result = self._amount / divisor
        return Money(result, self._currency).quantize()

    def __eq__(self, other):
        if not isinstance(other, Money):
            return False
        return self._amount == other._amount and self._currency == other._currency

    def __lt__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        if self._currency != other._currency:
            raise ValueError(f"Cannot compare {self._currency} and {other._currency}")
        return self._amount < other._amount

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    def __repr__(self):
        return f"Money({self._amount}, '{self._currency}')"

    def __str__(self):
        return f"{self._amount} {self._currency}"


# Funciones helper para compatibilidad
def to_money(value: float | int | str | Decimal, currency: str = "USD") -> Money:
    """Convierte un valor a Money"""
    return Money(value, currency)


def from_api(value: float, currency: str = "USD") -> Money:
    """Crea Money desde un valor de API (float)"""
    return Money(value, currency)


def to_api(money: Money) -> float:
    """Convierte Money a float para enviar a API"""
    return money.to_float()


def sum_money(amounts: list[Money]) -> Money | None:
    """Suma una lista de Money (debe ser misma moneda)"""
    if not amounts:
        return None

    currency = amounts[0].currency
    total = Decimal("0")

    for amount in amounts:
        if amount.currency != currency:
            raise ValueError(f"All amounts must be in {currency}")
        total += amount.amount

    return Money(total, currency)
