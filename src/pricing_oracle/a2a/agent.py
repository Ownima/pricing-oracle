"""A2A Protocol agent for pricing oracle.

Implements the Agent2Agent (A2A) protocol for exposing the pricing oracle
as an agent that can be discovered and called by other agents.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from a2a.types import AgentCard, AgentSkill, Message, TextPart
from pydantic import BaseModel

from pricing_oracle.models import CategoryEnum
from pricing_oracle.service import CompetitorPricingService

logger = logging.getLogger(__name__)


class PricingRequest(BaseModel):
    """Parsed pricing request from A2A message."""

    country: str = "TH"
    region: str | None = None
    category: CategoryEnum | None = None
    tier: str = "market"
    action: str = "snapshot"


def get_agent_card() -> AgentCard:
    """Return the Agent Card for discovery.

    This is the entry point for A2A agent discovery.
    """
    return AgentCard(
        name="Ownima Pricing Oracle",
        description=(
            "Market intelligence for vehicle rental pricing in Thailand and Vietnam. "
            "Get competitive price analysis, suggestions, and market snapshots."
        ),
        url="http://localhost:8000/a2a",
        version="1.0.0",
        capabilities={
            "streaming": True,
            "pushNotifications": False,
        },
        skills=[
            AgentSkill(
                id="get_market_snapshot",
                name="Get Market Snapshot",
                description=(
                    "Get market statistics for a vehicle category in a specific "
                    "country/region. Returns median, min, max prices and sample size."
                ),
                input_modes=["text"],
                output_modes=["text"],
            ),
            AgentSkill(
                id="suggest_price",
                name="Suggest Price",
                description=(
                    "Get suggested rental price for a vehicle category, country, "
                    "and tier (economy/market/premium)."
                ),
                input_modes=["text"],
                output_modes=["text"],
            ),
            AgentSkill(
                id="compare_competitors",
                name="Compare Competitors",
                description=(
                    "Compare pricing across multiple competitors in a region. "
                    "Shows price distribution and outliers."
                ),
                input_modes=["text"],
                output_modes=["text"],
            ),
        ],
    )


class PricingOracleAgent:
    """A2A-compatible Pricing Oracle Agent.

    Handles incoming A2A messages and returns pricing intelligence.
    """

    def __init__(self, session) -> None:
        self.session = session
        self.service = CompetitorPricingService(session)

    async def on_message(self, message: Message) -> dict[str, Any]:
        """Handle incoming A2A message.

        Args:
            message: A2A Message from client agent.

        Returns:
            Response dict with status and artifact.
        """
        try:
            user_message = self._extract_text(message)
            if not user_message:
                return self._error_response("Empty message")

            request = self._parse_request(user_message)

            if request.action == "snapshot":
                return await self._handle_snapshot(request)
            if request.action == "suggest":
                return await self._handle_suggestion(request)
            if request.action == "compare":
                return await self._handle_comparison(request)
            return self._error_response(
                f"Unknown action: {request.action}. Try: snapshot, suggest, or compare"
            )

        except Exception:
            logger.exception("Error handling A2A message")
            return self._error_response("Internal error processing request")

    def _extract_text(self, message: Message) -> str | None:
        """Extract text content from A2A message."""
        if not message.parts:
            return None
        for part in message.parts:
            if isinstance(part, TextPart):
                return part.text
        return None

    def _parse_request(self, text: str) -> PricingRequest:
        """Parse natural language request into PricingRequest.

        Simple keyword-based parsing. Can be enhanced with LLM.
        """
        text_lower = text.lower()

        request = PricingRequest()

        if "snapshot" in text_lower:
            request.action = "snapshot"
        elif "suggest" in text_lower or "price" in text_lower:
            request.action = "suggest"
        elif "compare" in text_lower:
            request.action = "compare"

        if "vietnam" in text_lower or "vn" in text_lower:
            request.country = "VN"
        elif "thailand" in text_lower or "th" in text_lower:
            request.country = "TH"

        if "da nang" in text_lower or "da-nang" in text_lower:
            request.region = "da-nang"
        elif "nha trang" in text_lower or "nha-trang" in text_lower:
            request.region = "nha-trang"
        elif "pattaya" in text_lower:
            request.region = "pattaya"

        if "economy" in text_lower:
            request.tier = "economy"
        elif "premium" in text_lower:
            request.tier = "premium"
        else:
            request.tier = "market"

        category = CategoryEnum.SCOOTER_150_300CC
        if "110" in text_lower or "125" in text_lower:
            category = CategoryEnum.SCOOTER_110_125CC
        elif "300" in text_lower or "bike" in text_lower or "motorbike" in text_lower:
            category = CategoryEnum.BIKE_300CC_PLUS
        elif "car" in text_lower:
            category = CategoryEnum.CAR_ECONOMY

        request.category = category

        return request

    async def _handle_snapshot(self, request: PricingRequest) -> dict[str, Any]:
        """Get market snapshot for category/country."""
        if not request.category:
            return self._error_response("Category required for snapshot")

        snapshot = await self.service.get_market_snapshot(request.category)

        if snapshot.status == "insufficient_data":
            return {
                "status": "completed",
                "artifact": {
                    "parts": [
                        {
                            "type": "text",
                            "text": "📊 Insufficient data for analysis.\n\n"
                            "We need at least 10 data points to generate a market snapshot.\n"
                            "Try again after more competitor data is collected.",
                        }
                    ]
                },
            }

        lines = [
            f"📊 Market Snapshot: {snapshot.category.value}",
            f"Country: {request.country}",
        ]

        if request.region:
            lines.append(f"Region: {request.region}")

        lines.extend(
            [
                "",
                f"📈 Data Points: {snapshot.count}",
                f"💵 Median: {snapshot.median:,.0f} THB/month",
                f"📉 Min: {snapshot.min:,.0f} THB",
                f"📈 Max: {snapshot.max:,.0f} THB",
                "",
                "💡 Suggested Prices (monthly):",
            ]
        )

        if snapshot.suggested:
            lines.extend(
                [
                    f"  Economy: {snapshot.suggested.economy:,} THB",
                    f"  Market: {snapshot.suggested.market:,} THB",
                    f"  Premium: {snapshot.suggested.premium:,} THB",
                ]
            )

        if snapshot.warning:
            lines.extend(["", f"⚠️ {snapshot.warning}"])

        return {
            "status": "completed",
            "artifact": {"parts": [{"type": "text", "text": "\n".join(lines)}]},
        }

    async def _handle_suggestion(self, request: PricingRequest) -> dict[str, Any]:
        """Get price suggestion for tier."""
        if not request.category:
            return self._error_response("Category required for suggestion")

        snapshot = await self.service.get_market_snapshot(request.category)

        if not snapshot.suggested:
            return {
                "status": "completed",
                "artifact": {
                    "parts": [
                        {
                            "type": "text",
                            "text": "💰 Insufficient data for price suggestion.\n\n"
                            "We need more competitor data to generate suggestions.",
                        }
                    ]
                },
            }

        price_map = {
            "economy": snapshot.suggested.economy,
            "market": snapshot.suggested.market,
            "premium": snapshot.suggested.premium,
        }

        price = price_map.get(request.tier, snapshot.suggested.market)

        return {
            "status": "completed",
            "artifact": {
                "parts": [
                    {
                        "type": "text",
                        "text": (
                            f"💰 Suggested {request.tier.capitalize()} Price\n"
                            f"Category: {request.category.value}\n"
                            f"Country: {request.country}\n"
                            f"Price: {price:,} THB/month"
                        ),
                    }
                ]
            },
        }

    async def _handle_comparison(self, request: PricingRequest) -> dict[str, Any]:
        """Compare competitors in region."""
        return {
            "status": "completed",
            "artifact": {
                "parts": [
                    {
                        "type": "text",
                        "text": (
                            "📊 Competitor Comparison\n\n"
                            "Feature coming soon! This will show detailed "
                            "competitor-by-competitor price breakdown."
                        ),
                    }
                ]
            },
        }

    def _error_response(self, error: str) -> dict[str, Any]:
        """Return error response."""
        return {
            "status": "failed",
            "error": error,
        }


def create_task_response(
    message: Message,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Create A2A task response from result."""
    return {
        "task_id": message.task_id or str(uuid.uuid4()),
        "status": result.get("status", "completed"),
        "message": {
            "role": "agent",
            "parts": result.get("artifact", {}).get("parts", []),
        },
    }
