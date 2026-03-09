# Pricing Oracle

> Market intelligence for vehicle rental pricing in Thailand and Vietnam.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Pricing Oracle is a standalone service that provides competitive pricing intelligence for vehicle rental businesses. It collects data from multiple sources, analyzes market trends, and provides price suggestions.

## Features

- **Multi-source data collection**: Tilda, Telegram, Telethon, Vietnam websites
- **Market analysis**: IQR-based outlier detection, statistical modeling
- **REST API**: Simple integration with existing systems
- **A2A Protocol**: Agent-to-agent communication
- **Fetch.ai uAgent**: AgentVerse marketplace integration
- **EIP-712 Auth**: Wallet-based authentication

## Supported Categories

| Category | Description |
|----------|-------------|
| `SCOOTER_110_125CC` | Scooter 110-125cc |
| `SCOOTER_150_300CC` | Scooter 150-300cc |
| `BIKE_300CC_PLUS` | Motorcycle 300cc+ |
| `CAR_ECONOMY` | Economy cars |

## Supported Countries

- Thailand (TH) - Production
- Vietnam (VN) - Coming soon

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

## Usage

### REST API

```bash
# Start the API server
uv run uvicorn pricing_oracle.api.main:app --reload

# Get market snapshot
curl "http://localhost:8000/v1/market/snapshot?country=TH&category=SCOOTER_150_300CC"

# Get price suggestion
curl "http://localhost:8000/v1/pricing/suggest?country=TH&category=SCOOTER_150_300CC&tier=market"
```

### uAgent (AgentVerse)

```bash
# Start the uAgent
AGENTVERSE_KEY=your_key uv run python -m pricing_oracle.uagent

# Or use docker
docker-compose up uagent
```

### CLI Demo

```bash
uv run python -m pricing_oracle.cli
```

## API Endpoints

### GET /health

Health check.

### GET /v1/market/snapshot

Get market statistics for a category.

**Parameters:**
- `country` (str): Country code (TH, VN)
- `category` (str): Vehicle category
- `region` (str, optional): Region ID

**Response:**
```json
{
  "category": "SCOOTER_150_300CC",
  "count": 45,
  "median": 8500,
  "min": 6000,
  "max": 12000,
  "suggested": {
    "economy": 7500,
    "market": 8500,
    "premium": 9500
  },
  "status": "success"
}
```

### GET /v1/pricing/suggest

Get price suggestion for a tier.

**Parameters:**
- `country` (str): Country code
- `category` (str): Vehicle category
- `tier` (str): Pricing tier (economy/market/premium)
- `region` (str, optional): Region ID

**Response:**
```json
{
  "status": "success",
  "price": 8500,
  "currency": "THB",
  "category": "SCOOTER_150_300CC",
  "country": "TH",
  "tier": "market"
}
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
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Website: https://ownima.com
- Email: dev@ownima.com
