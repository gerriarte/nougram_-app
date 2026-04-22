"""
Pricing strategies for different pricing types using Strategy Pattern
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from app.models.service import Service


def _to_decimal(value, default: Decimal = Decimal("0")) -> Decimal:
    """Normalize numeric input to Decimal for banking-grade precision."""
    if value is None:
        return default
    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (TypeError, ValueError):
        return default


class PricingStrategy(ABC):
    """
    Abstract base class for pricing strategies
    """

    @abstractmethod
    def calculate(
        self, item: dict, service: Service, blended_cost_rate: float
    ) -> dict[str, Decimal]:
        """
        Calculate internal cost and client price for an item

        Args:
            item: Item dictionary with pricing information
            service: Service model instance
            blended_cost_rate: Current blended cost rate

        Returns:
            Dictionary with 'internal_cost' and 'client_price'
        """
        pass


class HourlyPricingStrategy(PricingStrategy):
    """
    Strategy for hourly pricing: Hours × BCR
    Note: client_price is calculated at quote level using target_margin_percentage
    """

    def calculate(
        self, item: dict, service: Service, blended_cost_rate: float
    ) -> dict[str, Decimal]:
        """
        Calculate pricing for hourly services

        Args:
            item: Must contain 'estimated_hours'
            service: Service model (default_margin_target used as fallback if no quote-level margin)
            blended_cost_rate: Cost per hour

        Returns:
            Dictionary with internal_cost and client_price (client_price uses service margin as fallback)
        """
        estimated_hours = _to_decimal(item.get("estimated_hours", Decimal("0")))
        if estimated_hours <= 0:
            return {"internal_cost": Decimal("0"), "client_price": Decimal("0")}

        bcr = _to_decimal(blended_cost_rate)
        internal_cost = bcr * estimated_hours

        # Calculate client price with service margin (fallback if no quote-level margin)
        # This will be overridden at quote level if target_margin_percentage is provided
        margin_target = _to_decimal(service.default_margin_target)
        if margin_target > 0 and margin_target < 1:
            client_price = internal_cost / (Decimal("1") - margin_target)
        else:
            client_price = internal_cost  # Fallback if margin is invalid

        return {
            "internal_cost": internal_cost,
            "client_price": client_price,  # Will be recalculated at quote level if target_margin_percentage is provided
        }


class FixedPricingStrategy(PricingStrategy):
    """
    Strategy for fixed pricing: fixed_price × quantity
    """

    def calculate(
        self, item: dict, service: Service, blended_cost_rate: float
    ) -> dict[str, Decimal]:
        """
        Calculate pricing for fixed-price services

        Args:
            item: Must contain 'fixed_price' and optionally 'quantity' and 'estimated_hours'
            service: Service with fixed_price fallback
            blended_cost_rate: Cost per hour (for internal cost calculation)

        Returns:
            Dictionary with internal_cost and client_price
        """
        fixed_price = _to_decimal(item.get("fixed_price") or service.fixed_price)
        quantity = _to_decimal(item.get("quantity", Decimal("1")), Decimal("1"))

        if fixed_price <= 0:
            return {"internal_cost": Decimal("0"), "client_price": Decimal("0")}

        client_price = fixed_price * quantity

        # For fixed pricing, internal cost is calculated based on estimated hours if provided
        # Otherwise, we use a conservative estimate
        estimated_hours = _to_decimal(item.get("estimated_hours"))
        if estimated_hours > 0:
            bcr = _to_decimal(blended_cost_rate)
            internal_cost = bcr * estimated_hours * quantity
        else:
            # If no hours provided, assume internal cost is 60% of fixed price (conservative)
            internal_cost = (fixed_price * quantity) * Decimal("0.6")

        return {"internal_cost": internal_cost, "client_price": client_price}


class RecurringPricingStrategy(PricingStrategy):
    """
    Strategy for recurring pricing: recurring_price based on billing frequency
    """

    def calculate(
        self, item: dict, service: Service, blended_cost_rate: float
    ) -> dict[str, Decimal]:
        """
        Calculate pricing for recurring services

        Args:
            item: Must contain 'recurring_price' and optionally 'billing_frequency', 'quantity', 'estimated_hours'
            service: Service with recurring_price and billing_frequency fallbacks
            blended_cost_rate: Cost per hour (for internal cost calculation)

        Returns:
            Dictionary with internal_cost and client_price
        """
        recurring_price = _to_decimal(item.get("recurring_price") or service.recurring_price)
        billing_frequency = item.get("billing_frequency") or service.billing_frequency or "monthly"
        quantity = _to_decimal(item.get("quantity", Decimal("1")), Decimal("1"))

        if recurring_price <= 0:
            return {"internal_cost": Decimal("0"), "client_price": Decimal("0")}

        client_price = recurring_price * quantity

        # For recurring services, internal cost is based on estimated hours if provided
        # Otherwise, estimate based on typical allocation
        estimated_hours = _to_decimal(item.get("estimated_hours"))
        if estimated_hours > 0:
            bcr = _to_decimal(blended_cost_rate)
            internal_cost = bcr * estimated_hours
        else:
            # Estimate: monthly retainer typically uses ~20% of monthly billable hours
            # Assuming 160 billable hours/month, 20% = 32 hours
            estimated_monthly_hours = Decimal("32")
            if billing_frequency == "annual":
                estimated_monthly_hours *= Decimal("12")
            bcr = _to_decimal(blended_cost_rate)
            internal_cost = bcr * estimated_monthly_hours * quantity

        return {"internal_cost": internal_cost, "client_price": client_price}


class ProjectValuePricingStrategy(PricingStrategy):
    """
    Strategy for project value pricing: Custom project value
    """

    def calculate(
        self, item: dict, service: Service, blended_cost_rate: float
    ) -> dict[str, Decimal]:
        """
        Calculate pricing for project value services

        Args:
            item: Must contain 'project_value' or 'fixed_price' and optionally 'quantity' and 'estimated_hours'
            service: Service model (not used for this strategy)
            blended_cost_rate: Cost per hour (for internal cost calculation)

        Returns:
            Dictionary with internal_cost and client_price
        """
        project_value = _to_decimal(item.get("project_value") or item.get("fixed_price"))
        quantity = _to_decimal(item.get("quantity", Decimal("1")), Decimal("1"))

        if project_value <= 0:
            return {"internal_cost": Decimal("0"), "client_price": Decimal("0")}

        client_price = project_value * quantity

        # For project value, internal cost is based on estimated hours if provided
        estimated_hours = _to_decimal(item.get("estimated_hours"))
        if estimated_hours > 0:
            bcr = _to_decimal(blended_cost_rate)
            internal_cost = bcr * estimated_hours * quantity
        else:
            # If no hours, assume internal cost is 50% of project value
            internal_cost = (project_value * quantity) * Decimal("0.5")

        return {"internal_cost": internal_cost, "client_price": client_price}


class PricingStrategyFactory:
    """
    Factory for creating pricing strategies based on pricing type
    """

    _strategies: dict[str, PricingStrategy] = {
        "hourly": HourlyPricingStrategy(),
        "fixed": FixedPricingStrategy(),
        "recurring": RecurringPricingStrategy(),
        "project_value": ProjectValuePricingStrategy(),
    }

    @classmethod
    def get_strategy(cls, pricing_type: str | None) -> PricingStrategy:
        """
        Get pricing strategy for the given pricing type

        Args:
            pricing_type: Type of pricing (hourly, fixed, recurring, project_value)

        Returns:
            PricingStrategy instance (defaults to HourlyPricingStrategy)
        """
        if not pricing_type:
            pricing_type = "hourly"

        return cls._strategies.get(pricing_type, cls._strategies["hourly"])

    @classmethod
    def register_strategy(cls, pricing_type: str, strategy: PricingStrategy):
        """
        Register a new pricing strategy (for extensibility)

        Args:
            pricing_type: Type identifier for the strategy
            strategy: PricingStrategy instance
        """
        cls._strategies[pricing_type] = strategy
