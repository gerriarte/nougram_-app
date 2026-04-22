"""
Onboarding View - Data transformation for onboarding responses
"""

from typing import Any

from app.schemas.onboarding import (
    BenchmarksResponse,
    CompleteOnboardingResponse,
    ProfileBenchmark,
    TemporaryBCRResponse,
)


class OnboardingView:
    """View for transforming onboarding data to response schemas"""

    def to_benchmarks_response(self, data: dict[str, Any]) -> BenchmarksResponse:
        """
        Transform service data to BenchmarksResponse

        Args:
            data: Dictionary from OnboardingService.get_benchmarks()

        Returns:
            BenchmarksResponse instance
        """
        benchmarks = ProfileBenchmark(
            profile_type=data["profile_type"],
            avg_monthly_income=data["benchmarks"].get("avg_monthly_income"),
            avg_margin=data["benchmarks"].get("avg_margin"),
            avg_hours_per_month=data["benchmarks"].get("avg_hours_per_month"),
            avg_team_size=data["benchmarks"].get("avg_team_size"),
            avg_salary=data["benchmarks"].get("avg_salary"),
            avg_clients=data["benchmarks"].get("avg_clients"),
        )

        return BenchmarksResponse(
            profile_type=data["profile_type"],
            country=data["country"],
            currency=data["currency"],
            benchmarks=benchmarks,
            source=data["source"],
        )

    def to_complete_response(self, data: dict[str, Any]) -> CompleteOnboardingResponse:
        """
        Transform service data to CompleteOnboardingResponse

        Args:
            data: Dictionary from OnboardingService.complete_onboarding()

        Returns:
            CompleteOnboardingResponse instance
        """
        return CompleteOnboardingResponse(
            success=data["success"],
            message=data["message"],
            organization_id=data["organization_id"],
            team_members_created=data["team_members_created"],
            expenses_created=data["expenses_created"],
            bcr_calculated=data.get("bcr_calculated"),
            organization=data["organization"],
        )

    def to_temporary_bcr_response(self, data: dict[str, Any]) -> TemporaryBCRResponse:
        """
        Transform service data to TemporaryBCRResponse

        Args:
            data: Dictionary from OnboardingService.calculate_temporary_bcr()

        Returns:
            TemporaryBCRResponse instance
        """
        return TemporaryBCRResponse(
            blended_cost_rate=data["blended_cost_rate"],
            total_monthly_costs=data["total_monthly_costs"],
            total_fixed_overhead=data["total_fixed_overhead"],
            total_salaries=data["total_salaries"],
            total_monthly_hours=data["total_monthly_hours"],
            team_members_count=data["team_members_count"],
            currency=data["currency"],
            note=data["note"],
        )
