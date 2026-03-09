"""Base protocol for competitor price adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pricing_oracle.models import SourceTypeEnum


@runtime_checkable
class PriceAdapter(Protocol):
    """Protocol that all price source adapters must implement."""

    @property
    def source_name(self) -> str:
        """Human-readable name of the source."""
        ...

    @property
    def source_type(self) -> "SourceTypeEnum":
        """Type of the data source."""
        ...

    @property
    def country_id(self) -> str:
        """Country code (TH, VN, etc.)."""
        ...

    async def fetch(self) -> list["RawListing"]:
        """Fetch and normalize listings from source."""
        ...


class RawListing:
    """Normalized intermediate representation of a price listing."""

    __slots__ = (
        "source_type",
        "source_name",
        "model",
        "engine_cc",
        "price_day",
        "price_3day",
        "price_week",
        "price_month",
        "deposit",
        "currency",
        "location",
        "extracted_confidence",
        "country_id",
    )

    def __init__(
        self,
        source_type: "SourceTypeEnum",
        source_name: str,
        price_month: float,
        model: str | None = None,
        engine_cc: int | None = None,
        price_day: float | None = None,
        price_3day: float | None = None,
        price_week: float | None = None,
        deposit: float | None = None,
        currency: str = "THB",
        location: str | None = None,
        extracted_confidence: float = 1.0,
        country_id: str = "TH",
    ) -> None:
        self.source_type = source_type
        self.source_name = source_name
        self.model = model
        self.engine_cc = engine_cc
        self.price_day = price_day
        self.price_3day = price_3day
        self.price_week = price_week
        self.price_month = price_month
        self.deposit = deposit
        self.currency = currency
        self.location = location
        self.extracted_confidence = extracted_confidence
        self.country_id = country_id
