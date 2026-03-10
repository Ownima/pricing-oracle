"""Adapter registry for competitor price sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.pricing_oracle.adapters.base import PriceAdapter

logger = logging.getLogger(__name__)


@dataclass
class AdapterConfig:
    """Configuration for a price adapter."""

    adapter_type: str
    name: str
    config: dict[str, Any]
    enabled: bool = True
    schedule: str | None = None


class AdapterRegistry:
    """Registry for price source adapters."""

    _adapters: dict[str, type[PriceAdapter]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register an adapter class."""

        def decorator(adapter_cls: type[PriceAdapter]) -> type[PriceAdapter]:
            if not issubclass(adapter_cls, PriceAdapter):
                msg = f"{adapter_cls.__name__} must implement PriceAdapter protocol"
                raise TypeError(msg)
            cls._adapters[name] = adapter_cls
            logger.debug("Registered adapter: %s -> %s", name, adapter_cls.__name__)
            return adapter_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> type[PriceAdapter]:
        """Get an adapter class by name."""
        if name not in cls._adapters:
            available = ", ".join(cls._adapters.keys())
            msg = f"Unknown adapter: {name}. Available: {available}"
            raise ValueError(msg)
        return cls._adapters[name]

    @classmethod
    def create(cls, config: AdapterConfig) -> PriceAdapter:
        """Create an adapter instance from config."""
        adapter_cls = cls.get(config.adapter_type)
        try:
            return adapter_cls(config)
        except TypeError:
            return adapter_cls()

    @classmethod
    def list_adapters(cls) -> list[str]:
        """List all registered adapter names."""
        return list(cls._adapters.keys())

    @classmethod
    def create_all(cls, configs: list[AdapterConfig]) -> list[PriceAdapter]:
        """Create multiple adapter instances from configs."""
        adapters: list[PriceAdapter] = []
        for config in configs:
            if not config.enabled:
                logger.debug("Skipping disabled adapter: %s", config.name)
                continue
            try:
                adapter = cls.create(config)
                adapters.append(adapter)
            except Exception:
                logger.exception("Failed to create adapter: %s", config.name)
        return adapters
