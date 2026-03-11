"""Registration constants and helpers for pricing oracle agent."""

from __future__ import annotations

AGENT_README = """# Pricing Oracle Agent

Market intelligence for vehicle rental pricing in Thailand and Vietnam.

## Capabilities

- **Price Suggestions**: Get competitive pricing for scooter, bike, and car rentals
- **Market Analytics**: IQR (Interquartile Range) based pricing analysis
- **Multi-Market Support**: Thailand (TH) and Vietnam (VN)
- **Vehicle Categories**:
  - Scooters: 110cc, 150cc
  - Bikes: 300cc
  - Cars: Economy, Standard, Premium

## Supported Commands

### Price Queries
- "scooter 110 economy" - Get economy price for 110cc scooter
- "scooter 150 market price" - Get market price for 150cc scooter
- "bike 300 premium" - Get premium price for 300cc bike
- "car economy" - Get economy price for car rental

### Market Analytics
- "market snapshot" - Get full market analytics with IQR
- "market snapshot for bike 300" - Get analytics for specific category

### General
- "info" or "help" - Get this documentation
- "what markets do you support?" - List supported markets
- "what vehicles do you support?" - List supported vehicles

## API Endpoints

### REST API
- `POST /price` - Get price suggestion
  - Request: `{"category": "scooter_150", "tier": "market", "country": "TH"}`
  - Response: `{"status": "success", "price": 8500, "currency": "THB"}`

- `GET /health` - Health check
  - Response: `{"status": "success"}`

### Agent Protocol
- Chat protocol (AgentChatProtocol v0.3.0)
- Send text messages for price queries

## Response Tiers

- **Economy**: Budget-friendly pricing (25% below median)
- **Market**: Competitive median pricing
- **Premium**: Premium service pricing (25% above median)

## Technical Details

- Protocol: AgentChatProtocol v0.3.0
- Network: Fetch.ai Testnet
- Authentication: EIP-712 for wallet-based authentication

## Contact

- Website: https://ownima.com
- Supported Regions: Thailand, Vietnam
- Vehicle Types: Scooter, Bike, Car
"""

AGENT_DESCRIPTION = (
    "Market intelligence for vehicle rental pricing across Thailand and Vietnam. "
    "Get competitive analysis, price suggestions, and market analytics via A2A protocol. "
    "Supports scooter (110cc, 150cc), bike (300cc), and car rentals. "
    "Uses IQR-based analytics for accurate pricing recommendations."
)

AGENT_METADATA = {
    "categories": [
        "pricing",
        "market",
        "analytics",
        "vehicle",
        "rental",
        "thailand",
        "vietnam",
    ],
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
        "vehicle",
    ],
}
