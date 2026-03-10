"""Competitor pricing service."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Literal

from sqlmodel import Session, func, select

from pricing_oracle.models import (
    CategoryEnum,
    CompetitorListing,
    MarketSnapshot,
    SuggestedPrices,
)

logger = logging.getLogger(__name__)

DEFAULT_MIN_SAMPLE_SIZE = 10
PRICING_TIER_PERCENTILES = {
    "economy": 0.25,
    "market": 0.50,
    "premium": 0.75,
}


class CompetitorPricingService:
    """Service for analyzing competitor pricing data."""

    def __init__(self, session: Session):
        self.session = session

    def get_market_snapshot(
        self,
        category: CategoryEnum,
        country_id: str = "TH",
        region_id: str | None = None,
        min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    ) -> MarketSnapshot:
        """Get market statistics for a category.

        Args:
            category: Vehicle category
            country_id: Country code (TH, VN)
            region_id: Optional region ID
            min_sample_size: Minimum data points required

        Returns:
            MarketSnapshot with statistics
        """
        query = select(CompetitorListing).where(
            CompetitorListing.category == category,
            CompetitorListing.country_id == country_id,
            CompetitorListing.ingested_at >= datetime.utcnow() - timedelta(days=30),
        )

        if region_id:
            query = query.where(CompetitorListing.region_id == region_id)

        listings = self.session.exec(query).all()

        if len(listings) < min_sample_size:
            return MarketSnapshot(
                category=category,
                count=len(listings),
                median=0,
                min_price=0,
                max_price=0,
                status="insufficient_data",
                warning=f"Insufficient data: {len(listings)} (minimum: {min_sample_size})",
            )

        prices = sorted([listing.price_month for listing in listings])

        median = self._percentile(prices, 0.5)
        min_price = min(prices)
        max_price = max(prices)

        suggested = self._calculate_suggested_prices(prices, median)

        return MarketSnapshot(
            category=category,
            count=len(listings),
            median=median,
            min_price=min_price,
            max_price=max_price,
            suggested=suggested,
            status="success",
        )

    def _calculate_suggested_prices(
        self, prices: list[float], median: float
    ) -> SuggestedPrices:
        """Calculate suggested prices using IQR method."""
        if len(prices) < 4:
            margin = 0.1
        return SuggestedPrices(
            economy=int(median * (1 - margin)),
            market=int(median),
            premium=int(median * (1 + margin)),
        )

        q1 = self._percentile(prices, 0.25)
        q3 = self._percentile(prices, 0.75)
        iqr = q3 - q1

        lower_bound = max(0, q1 - 1.5 * iqr)
        upper_bound = q3 + 1.5 * iqr

        filtered = [p for p in prices if lower_bound <= p <= upper_bound]

        if len(filtered) < 3:
            margin = 0.1
            return SuggestedPrices(
                economy=int(median * (1 - margin)),
                market=int(median),
                premium=int(median * (1 + margin)),
            )

        filtered_sorted = sorted(filtered)
        economy = self._percentile(filtered_sorted, 0.20)
        market = self._percentile(filtered_sorted, 0.50)
        premium = self._percentile(filtered_sorted, 0.80)

        return SuggestedPrices(
            economy=int(economy),
            market=int(market),
            premium=int(premium),
        )

    def _percentile(self, sorted_data: list[float], percentile: float) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0

        k = (len(sorted_data) - 1) * percentile
        f = int(k)
        c = f + 1

        if c >= len(sorted_data):
            return sorted_data[f]

        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    def get_price_suggestion(
        self,
        category: CategoryEnum,
        tier: Literal["economy", "market", "premium"],
        country_id: str = "TH",
        region_id: str | None = None,
    ) -> dict[str, Any]:
        """Get price suggestion for a specific tier.

        Args:
            category: Vehicle category
            tier: Pricing tier
            country_id: Country code
            region_id: Optional region

        Returns:
            Dict with price suggestion
        """
        snapshot = self.get_market_snapshot(category, country_id, region_id)

        if snapshot.status == "insufficient_data":
            return {
                "status": "error",
                "error": "Insufficient data for price suggestion",
                "category": category.value,
                "country": country_id,
            }

        if not snapshot.suggested:
            return {
                "status": "error",
                "error": "Could not calculate suggestion",
                "category": category.value,
                "country": country_id,
            }

        price_map = {
            "economy": snapshot.suggested.economy,
            "market": snapshot.suggested.market,
            "premium": snapshot.suggested.premium,
        }

        return {
            "status": "success",
            "price": price_map.get(tier, snapshot.suggested.market),
            "currency": "THB",
            "category": category.value,
            "country": country_id,
            "tier": tier,
        }
