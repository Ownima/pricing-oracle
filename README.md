# Pricing Oracle

> Market intelligence for vehicle rental pricing in Thailand and Vietnam.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Pricing Oracle is a standalone service that provides competitive pricing intelligence for vehicle rental businesses. It collects data from multiple sources, analyzes market trends, and provides price suggestions via REST API, A2A protocol, and Fetch.ai uAgent.

## Features

- **Multi-source data collection**: Tilda, Telegram, Telethon, Vietnam websites
- **Market analysis**: IQR-based outlier detection, statistical modeling
- **REST API**: Simple integration with existing systems
- **A2A Protocol**: Agent-to-agent communication
- **Fetch.ai uAgent**: AgentVerse marketplace integration
- **EIP-712 Auth**: Wallet-based authentication

## Supported Categories

| Category | Description | Example |
|----------|-------------|---------|
| `scooter_110` | Scooter 110cc | "scooter 110 economy" |
| `scooter_150` | Scooter 150cc | "scooter 150 market" |
| `bike_300` | Motorcycle 300cc+ | "bike 300 premium" |
| `car_economy` | Economy cars | "car economy" |

## Supported Countries

- Thailand (TH) - Production
- Vietnam (VN) - Coming soon

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
- "info" or "help" - Get documentation
- "what markets do you support?" - List supported markets
- "what vehicles do you support?" - List vehicle types

## Response Tiers

- **Economy**: Budget-friendly pricing (25% below median)
- **Market**: Competitive median pricing
- **Premium**: Premium service pricing (25% above median)

## Installation

```bash
uv sync
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://postgres:postgres@localhost:5432/pricing_oracle` |
| `PRICING_AGENT_NETWORK` | Network (testnet/mainnet) | `testnet` |
| `PRICING_AGENT_DOMAIN` | Agent domain | `http://localhost:8000` |
| `AGENTVERSE_KEY` | AgentVerse API key | - |
| `AGENT_SEED_PHRASE` | Agent seed phrase | pricing-oracle-seed-phrase-for-agentverse |

## Usage

### uAgent (AgentVerse)

```bash
# Start the uAgent
uv run pricing-oracle-uagent

# Register on AgentVerse (run separately after agent starts)
uv run pricing-oracle-register
```

### REST API

```bash
# Start the API server
uv run pricing-oracle-api

# Get price suggestion (POST)
curl -X POST http://localhost:8000/price \
  -H "Content-Type: application/json" \
  -d '{"category": "scooter_150", "tier": "market", "country": "TH"}'

# Health check
curl http://localhost:8000/health
```

### CLI Demo

```bash
uv run pricing-oracle
```

## API Endpoints

### POST /price

Get price suggestion for a vehicle category.

**Request:**
```json
{
  "category": "scooter_150",
  "tier": "market",
  "country": "TH",
  "action": "price"
}
```

**Response:**
```json
{
  "status": "success",
  "price": 8500,
  "currency": "THB",
  "category": "scooter_150",
  "country": "TH",
  "tier": "market"
}
```

### GET /health

Health check.

**Response:**
```json
{
  "status": "success"
}
```

## AgentVerse Integration

The Pricing Oracle is registered as a Fetch.ai uAgent on AgentVerse:

- **Protocol**: AgentChatProtocol v0.3.0
- **Network**: Fetch.ai Testnet
- **Endpoint**: `/submit`

### Registration

Registration is handled separately to avoid timing issues:

```bash
# 1. Start the agent
uv run pricing-oracle-uagent

# 2. Wait for agent to initialize (5+ seconds)

# 3. Register separately
uv run pricing-oracle-register
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Pricing Oracle                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Adapters  │  │   Service    │  │     API      │ │
│  │  (Data In)  │  │  (Analysis)  │  │  (REST/A2A)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                         │                             │
│              ┌──────────▼──────────┐                │
│              │   PostgreSQL DB     │                │
│              └─────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

## Deployment

### Docker Compose

```bash
# Start all services
docker-compose up -d

# Start only API
docker-compose up api

# Start uAgent
AGENTVERSE_KEY=your_key docker-compose up uagent
```

### Environment Variables for Production

```bash
DATABASE_URL=postgresql://user:pass@host:5432/pricing_oracle
PRICING_AGENT_NETWORK=mainnet
PRICING_AGENT_DOMAIN=https://pricing.yourdomain.com
AGENTVERSE_KEY=your_agentverse_key
AGENT_SEED_PHRASE=your_seed_phrase
```

## Development

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=pricing_oracle

# Fast tests only
uv run pytest -m "unit"
```

### Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy pricing_oracle
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Website: https://ownima.com
- Email: dev@ownima.com
