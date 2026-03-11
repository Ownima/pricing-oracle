"""Competitor pricing service."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Literal

from sqlmodel import Session, select

from pricing_oracle.models import (
    CategoryEnum,
    CompetitorListing,
    MarketSnapshot,
    SuggestedPrices,
)

logger = logging.getLogger(__name__)

# Mock market data fallback (Thailand - Pattaya area)
MOCK_MARKET_DATA: dict[str, dict] = {
    "SCOOTER_110_125CC": {
        "count": 50,
        "median": 4500,
        "min": 3000,
        "max": 8000,
        "suggested": {"economy": 3800, "market": 4500, "premium": 6000},
    },
    "SCOOTER_150_300CC": {
        "count": 35,
        "median": 6000,
        "min": 4000,
        "max": 12000,
        "suggested": {"economy": 5000, "market": 6000, "premium": 9000},
    },
    "BIKE_300CC_PLUS": {
        "count": 20,
        "median": 10000,
        "min": 7000,
        "max": 18000,
        "suggested": {"economy": 8500, "market": 10000, "premium": 15000},
    },
    "CAR_ECONOMY": {
        "count": 25,
        "median": 12000,
        "min": 8000,
        "max": 20000,
        "suggested": {"economy": 10000, "market": 12000, "premium": 16000},
    },
}


# Owner API configuration
OWNIMA_API_URL = os.getenv("OWNIMA_API_URL", "")
OWNIMA_API_KEY = os.getenv("OWNIMA_API_KEY", "")


async def fetch_market_snapshot_from_owner_api(
    category: CategoryEnum,
    country: str = "TH",
) -> dict[str, Any] | None:
    """Fetch market snapshot from owner-api.

    Returns None if API is not configured or unavailable.
    """
    if not OWNIMA_API_URL or not OWNIMA_API_KEY:
        logger.info("Owner API not configured - using local data")
        return None

    import httpx

    # Map category to owner-api format
    category_map = {
        "scooter_110": "SCOOTER_110_125CC",
        "scooter_150": "SCOOTER_150_300CC",
        "bike_300": "BIKE_300CC_PLUS",
        "car_economy": "CAR_ECONOMY",
    }
    owner_category = category_map.get(category.value, category.value)

    url = f"{OWNIMA_API_URL}/competitor/v1/market/{owner_category}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers={"X-API-Key": OWNIMA_API_KEY},
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Fetched market snapshot from owner-api: {category.value}")
                return data
            else:
                logger.warning(
                    f"Owner API returned {response.status_code}: {response.text}"
                )
                return None
    except Exception as e:
        logger.warning(f"Failed to fetch from owner-api: {e}")
        return None


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

    async def get_market_snapshot(
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
        # Try owner-api first if configured
        owner_data = await fetch_market_snapshot_from_owner_api(category, country_id)

        if owner_data:
            # Convert owner-api response to our format
            suggested = owner_data.get("suggested")
            return MarketSnapshot(
                category=category,
                count=owner_data.get("count", 0),
                median=owner_data.get("median", 0),
                min_price=owner_data.get("min", 0),
                max_price=owner_data.get("max", 0),
                suggested=SuggestedPrices(
                    economy=suggested.get("economy", 0) if suggested else 0,
                    market=suggested.get("market", 0) if suggested else 0,
                    premium=suggested.get("premium", 0) if suggested else 0,
                ),
                status=owner_data.get("status", "success"),
            )

        # Fall back to local database
        query = select(CompetitorListing).where(
            CompetitorListing.category == category,
            CompetitorListing.country_id == country_id,
            CompetitorListing.ingested_at >= datetime.utcnow() - timedelta(days=30),
        )

        if region_id:
            query = query.where(CompetitorListing.region_id == region_id)

        listings = self.session.exec(query).all()

        if len(listings) < min_sample_size:
            # Fall back to mock data if available
            mock_data = MOCK_MARKET_DATA.get(category.value)
            if mock_data:
                logger.info(f"Using mock data for {category.value}")
                return MarketSnapshot(
                    category=category,
                    count=mock_data["count"],
                    median=mock_data["median"],
                    min_price=mock_data["min"],
                    max_price=mock_data["max"],
                    suggested=SuggestedPrices(
                        economy=mock_data["suggested"]["economy"],
                        market=mock_data["suggested"]["market"],
                        premium=mock_data["suggested"]["premium"],
                    ),
                    status="success",
                )

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

    async def get_price_suggestion(
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
        snapshot = await self.get_market_snapshot(category, country_id, region_id)

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
