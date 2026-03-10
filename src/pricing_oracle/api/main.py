"""FastAPI application for Pricing Oracle."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from sqlmodel import SQLModel, create_engine

from src.pricing_oracle.models import CategoryEnum
from src.pricing_oracle.service import CompetitorPricingService

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/pricing_oracle",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Pricing Oracle API",
    description="Market intelligence for vehicle rental pricing",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/v1/market/snapshot")
async def get_market_snapshot(
    country: str = Query("TH", description="Country code (TH, VN)"),
    category: str = Query(..., description="Vehicle category"),
    region: str | None = Query(None, description="Region ID"),
):
    """Get market snapshot for a category."""
    try:
        cat_enum = CategoryEnum(category)
    except ValueError:
        return {"error": f"Invalid category: {category}"}

    engine = create_engine(DATABASE_URL)
    from sqlmodel import Session

    with Session(engine) as session:
        service = CompetitorPricingService(session)
        snapshot = service.get_market_snapshot(cat_enum, country, region)

    return snapshot.to_dict()


@app.get("/v1/pricing/suggest")
async def suggest_price(
    country: str = Query("TH", description="Country code"),
    category: str = Query(..., description="Vehicle category"),
    tier: str = Query("market", description="Pricing tier (economy/market/premium)"),
    region: str | None = Query(None, description="Region ID"),
):
    """Get price suggestion for a tier."""
    try:
        cat_enum = CategoryEnum(category)
    except ValueError:
        return {"error": f"Invalid category: {category}"}

    engine = create_engine(DATABASE_URL)
    from sqlmodel import Session

    with Session(engine) as session:
        service = CompetitorPricingService(session)
        result = service.get_price_suggestion(cat_enum, tier, country, region)

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
