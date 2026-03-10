"""Pricing Oracle models."""

from __future__ import annotations

import enum
import hashlib
import uuid
from datetime import datetime
from typing import Literal

from sqlmodel import Field, Index, SQLModel


class CategoryEnum(enum.Enum):
    """Vehicle category for pricing."""

    SCOOTER_110_125CC = "SCOOTER_110_125CC"
    SCOOTER_150_300CC = "SCOOTER_150_300CC"
    BIKE_300CC_PLUS = "BIKE_300CC_PLUS"
    CAR_ECONOMY = "CAR_ECONOMY"


class SourceTypeEnum(enum.Enum):
    """Source of the competitor listing data."""

    TELEGRAM = "TELEGRAM"
    WEB = "WEB"
    MANUAL = "MANUAL"


class Country(SQLModel, table=True):
    """Supported countries for pricing oracle."""

    __tablename__ = "countries"

    id: str = Field(primary_key=True, max_length=2)
    name: str = Field(max_length=100)
    currency: str = Field(default="THB", max_length=3)
    locale: str = Field(max_length=5)
    enabled: bool = Field(default=True)


class Region(SQLModel, table=True):
    """Geographic regions within a country."""

    __tablename__ = "regions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    country_id: str = Field(foreign_key="countries.id", max_length=2)
    name: str = Field(max_length=100)
    enabled: bool = Field(default=True)

    __table_args__ = (Index("ix_regions_country", "country_id"),)


class CompetitorListing(SQLModel, table=True):
    """Competitor vehicle listing for pricing analysis."""

    __tablename__ = "competitor_listings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    model: str | None = Field(default=None, max_length=200)
    category: CategoryEnum = Field(index=True)
    source_type: SourceTypeEnum
    source_name: str = Field(max_length=200)
    price_day: float | None = Field(default=None)
    price_3day: float | None = Field(default=None)
    price_week: float | None = Field(default=None)
    price_month: float
    deposit: float | None = Field(default=None)
    currency: str = Field(default="THB", max_length=3)
    location: str | None = Field(default=None, max_length=100)
    country_id: str = Field(default="TH", max_length=2)
    region_id: uuid.UUID | None = Field(default=None, foreign_key="regions.id")
    listing_hash: str = Field(unique=True, index=True, max_length=64)
    engine_cc: int | None = Field(default=None)
    extracted_confidence: float = Field(default=1.0)
    extracted_model: str | None = Field(default=None, max_length=200)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_competitor_listings_country_region_cat",
            "country_id",
            "region_id",
            "category",
            "ingested_at",
        ),
    )

    @staticmethod
    def compute_hash(
        category: str,
        price_month: float,
        source_name: str | None,
        location: str | None,
        model: str | None = None,
        country_id: str = "TH",
    ) -> str:
        """Compute hash for deduplication."""
        raw = f"{country_id}:{category}:{price_month}:{source_name or ''}:{location or ''}:{model or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()


class MarketSnapshot:
    """Market analysis snapshot."""

    def __init__(
        self,
        category: CategoryEnum,
        count: int,
        median: float,
        min_price: float,
        max_price: float,
        suggested: SuggestedPrices | None = None,
        status: Literal["success", "insufficient_data"] = "success",
        warning: str | None = None,
    ):
        self.category = category
        self.count = count
        self.median = median
        self.min = min_price
        self.max = max_price
        self.suggested = suggested
        self.status = status
        self.warning = warning

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "count": self.count,
            "median": self.median,
            "min": self.min,
            "max": self.max,
            "suggested": self.suggested.to_dict() if self.suggested else None,
            "status": self.status,
            "warning": self.warning,
        }


class SuggestedPrices:
    """Suggested pricing tiers."""

    def __init__(self, economy: float, market: float, premium: float):
        self.economy = economy
        self.market = market
        self.premium = premium

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "economy": self.economy,
            "market": self.market,
            "premium": self.premium,
        }
