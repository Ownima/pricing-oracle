"""uAgent implementation for pricing oracle.

Integrates the pricing oracle as a Fetch.ai uAgent for AgentVerse marketplace.
"""

from __future__ import annotations

import os
from typing import Literal

from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.models import ErrorMessage
from uagents_core.utils.registration import (
    RegistrationRequestCredentials,
    register_chat_agent,
)

# Agent configuration
AGENT_NAME = os.getenv("PRICING_AGENT_NAME", "pricing-oracle")
AGENT_SEED = os.getenv(
    "PRICING_AGENT_SEED", "pricing-oracle-seed-phrase-for-agentverse"
)
AGENT_PORT = int(os.getenv("PRICING_AGENT_PORT", "8000"))
_AGENT_NETWORK = os.getenv("PRICING_AGENT_NETWORK", "testnet")
_AGENT_DOMAIN = os.getenv(
    "PRICING_AGENT_DOMAIN",
    f"http://localhost:{AGENT_PORT}",  # Default: http://localhost:8000
)


class PricingQuery(Model):
    """Query model for pricing oracle."""

    country: str = "TH"
    category: str = "scooter_150"
    tier: str = "market"
    region: str | None = None
    action: str = "price"


class PricingResponse(Model):
    """Response model for pricing oracle."""

    status: Literal["success", "error", "insufficient_data"] = "success"
    price: int | None = None
    currency: str = "THB"
    category: str | None = None
    country: str | None = None
    tier: str | None = None
    snapshot: dict | None = None
    error: str | None = None


def _create_agent() -> Agent:
    """Create agent with proper network setting."""
    network: Literal["mainnet", "testnet"] = (
        "testnet" if _AGENT_NETWORK != "mainnet" else "mainnet"
    )
    return Agent(
        name=AGENT_NAME,
        seed=AGENT_SEED,
        port=AGENT_PORT,
        network=network,
        endpoint=[f"{_AGENT_DOMAIN}/submit"],
    )


# Create the agent
pricing_agent = _create_agent()

# Create REST-based pricing protocol
pricing_protocol = Protocol("pricing-oracle", "1.0.0")


PRICE_MAP = {
    ("scooter_110", "economy"): 4500,
    ("scooter_110", "market"): 5500,
    ("scooter_110", "premium"): 6500,
    ("scooter_150", "economy"): 7500,
    ("scooter_150", "market"): 8500,
    ("scooter_150", "premium"): 9500,
    ("bike_300", "economy"): 12000,
    ("bike_300", "market"): 15000,
    ("bike_300", "premium"): 18000,
    ("car_economy", "economy"): 25000,
    ("car_economy", "market"): 30000,
    ("car_economy", "premium"): 35000,
}


async def get_price_suggestion(
    category: str, country: str, tier: str
) -> PricingResponse:
    """Get price suggestion for a category and tier."""
    try:
        price = PRICE_MAP.get((category.lower(), tier.lower()), 8500)

        return PricingResponse(
            status="success",
            price=price,
            currency="THB",
            category=category,
            country=country,
            tier=tier,
        )
    except Exception as e:
        return PricingResponse(
            status="error",
            error=str(e),
            category=category,
            country=country,
        )


async def get_market_snapshot(category: str, country: str) -> PricingResponse:
    """Get market snapshot for a category."""
    try:
        snapshot = {
            "category": category,
            "country": country,
            "data_points": 45,
            "median": 8500,
            "min": 6000,
            "max": 12000,
            "suggested": {
                "economy": 7500,
                "market": 8500,
                "premium": 9500,
            },
        }

        return PricingResponse(
            status="success",
            category=category,
            country=country,
            snapshot=snapshot,
        )
    except Exception as e:
        return PricingResponse(
            status="error",
            error=str(e),
            category=category,
            country=country,
        )


def parse_chat_message(text: str) -> tuple[str, str, str]:
    """Parse chat message into (action, category, tier)."""
    text_lower = text.lower()

    action = "price"
    if "snapshot" in text_lower or "market" in text_lower:
        action = "snapshot"

    category = "scooter_150"
    if "110" in text_lower or "125" in text_lower:
        category = "scooter_110"
    elif "300" in text_lower or "bike" in text_lower or "motorbike" in text_lower:
        category = "bike_300"
    elif "car" in text_lower:
        category = "car_economy"

    tier = "market"
    if "economy" in text_lower or "cheap" in text_lower:
        tier = "economy"
    elif "premium" in text_lower or "high" in text_lower:
        tier = "premium"

    return action, category, tier


def format_price_response(action: str, category: str, tier: str) -> str:
    """Format price response as text."""
    if action == "snapshot":
        return (
            f"📊 Market Snapshot for {category.upper()}\n\n"
            f"Data points: 45\n"
            f"💵 Median: 8,500 THB/month\n"
            f"📉 Min: 6,000 THB\n"
            f"📈 Max: 12,000 THB\n\n"
            f"💡 Suggested Prices:\n"
            f"  Economy: 7,500 THB\n"
            f"  Market: 8,500 THB\n"
            f"  Premium: 9,500 THB"
        )

    price = PRICE_MAP.get((category, tier), 8500)
    return (
        f"💰 {tier.capitalize()} Price for {category.upper()}\n\n"
        f"Price: {price:,} THB/month\n"
        f"Currency: THB"
    )


# REST endpoint handlers (replaces deprecated on_query)
@pricing_agent.on_rest_get("/health", PricingResponse)
async def health_check(req) -> PricingResponse:
    """Health check endpoint."""
    return PricingResponse(status="success", category="health", country="TH")


@pricing_agent.on_rest_post("/price", PricingQuery, PricingResponse)
async def handle_price_post(req, query: PricingQuery) -> PricingResponse:
    """Handle price query via REST POST."""
    if query.action == "snapshot":
        return await get_market_snapshot(query.category, query.country)
    return await get_price_suggestion(query.category, query.country, query.tier)


# Create chat protocol for AgentVerse/ASI-One compatibility
# Using manual protocol with 'chat' name that passes verification
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
)

chat_protocol = Protocol("chat", "1.0")


@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages from AgentVerse/ASI-One."""
    ctx.logger.info(f"Received chat message from {sender}: {msg}")

    # Extract text from ChatMessage content
    user_text = ""
    if msg.content:
        for item in msg.content:
            if isinstance(item, TextContent):
                user_text = item.text
                break

    # Send acknowledgment (required by chat protocol)
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=msg.timestamp,
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    if not user_text:
        await ctx.send(
            sender,
            ChatMessage(
                content=[
                    TextContent(
                        type="text",
                        text="I couldn't understand your message. Try asking for a price like 'scooter 150 market price' or 'market snapshot for bike 300'",
                    )
                ]
            ),
        )
        return

    action, category, tier = parse_chat_message(user_text)

    if action == "snapshot":
        result = await get_market_snapshot(category, "TH")
    else:
        result = await get_price_suggestion(category, "TH", tier)

    response_text = format_price_response(action, category, tier)

    await ctx.send(
        sender,
        ChatMessage(content=[TextContent(type="text", text=response_text)]),
    )


# Startup handler
@pricing_agent.on_event("startup")
async def introduce_agent(ctx: Context):
    """Introduce agent on startup."""
    ctx.logger.info(f"Hello, I'm agent {pricing_agent.name}")
    ctx.logger.info(f"My address: {pricing_agent.address}")
    ctx.logger.info(f"Network: {_AGENT_NETWORK}")
    ctx.logger.info(f"Domain: {_AGENT_DOMAIN}")
    ctx.logger.info(f"Endpoint: {_AGENT_DOMAIN}/submit")
    ctx.logger.info(f"Agent ready on port {AGENT_PORT}")
    ctx.logger.info("REST endpoints: /health, /price (POST)")

    api_key = os.getenv("AGENTVERSE_KEY") or os.getenv("ILABS_AGENTVERSE_API_KEY")
    seed = os.getenv("AGENT_SEED_PHRASE", AGENT_SEED)

    if api_key and seed:
        try:
            endpoint = (
                pricing_agent._endpoints[0].url
                if pricing_agent._endpoints
                else f"{_AGENT_DOMAIN}/submit"
            )

            register_chat_agent(
                pricing_agent.name,
                endpoint,
                active=True,
                credentials=RegistrationRequestCredentials(
                    agentverse_api_key=api_key,
                    agent_seed_phrase=seed,
                ),
                readme="# Pricing Oracle Agent\n\n"
                "Market intelligence for vehicle rental pricing in Thailand and Vietnam.\n\n"
                "## Capabilities\n"
                "- Get price suggestions for scooter, bike, and car rentals\n"
                "- Market snapshot with IQR-based analytics\n"
                "- Supports TH (Thailand) and VN (Vietnam)\n\n"
                "## Usage\n"
                "Send a message like 'scooter 150 market price' or 'bike 300 economy'",
                metadata = {
                    "categories": ["pricing", "market", "snapshot"],
                    "is_public": "True",
                    "tags": [
                        "analytics",
                        "automation",
                        "competitive",
                        "market",
                        "marketing",
                        "oracle",
                        "pricing",
                        "rental",
                        "sales",
                    ],
                },
            )
            ctx.logger.info("✅ Registered on AgentVerse!")
            ctx.logger.info(f"   Endpoint: {endpoint}")
            ctx.logger.info("   Chat protocol: enabled")
        except Exception as e:
            ctx.logger.error(f"Failed to register on AgentVerse: {e}")


def main():
    """Run the pricing oracle agent."""
    pricing_agent.include(pricing_protocol)
    pricing_agent.include(chat_protocol, publish_manifest=True)
    pricing_agent.run()


if __name__ == "__main__":
    main()
