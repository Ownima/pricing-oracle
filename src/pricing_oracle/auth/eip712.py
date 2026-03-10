"""EIP-712 authentication for A2A agent.

Implements EIP-712 typed data signing for wallet-based authentication.
This allows AI agents with Ethereum wallets to authenticate to the
pricing oracle service.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EIP712Domain:
    """EIP-712 domain separator."""

    name: str = "OwnimaPricingOracle"
    version: str = "1"
    chainId: int = 1
    verifyingContract: str = "0x0000000000000000000000000000000000000000"


@dataclass
class PricingRequest:
    """Structured pricing request for EIP-712 signing."""

    country: str = "TH"
    category: str = "scooter_150"
    tier: str = "market"
    region: str = ""
    nonce: int = 0
    deadline: int = 0


class EIP712Verifier:
    """EIP-712 signature verifier for wallet authentication.

    Usage:
        verifier = EIP712Verifier()

        # Verify a signature
        is_valid = verifier.verify(
            address="0x1234...",
            signature="0xabcd...",
            message={"country": "TH", "category": "scooter_150"}
        )
    """

    DOMAIN: EIP712Domain = EIP712Domain()

    MESSAGE_TYPES = {
        "PricingRequest": [
            {"name": "country", "type": "string"},
            {"name": "category", "type": "string"},
            {"name": "tier", "type": "string"},
            {"name": "region", "type": "string"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
        ],
        "AgentAuth": [
            {"name": "action", "type": "string"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
        ],
    }

    def __init__(self, domain: EIP712Domain | None = None) -> None:
        self.domain = domain or self.DOMAIN

    def create_login_message(self, nonce: int) -> dict[str, Any]:
        """Create a login message for wallet signature.

        Returns:
            Message dict that clients should sign with EIP-712.
        """
        return {
            "domain": {
                "name": self.domain.name,
                "version": self.domain.version,
                "chainId": self.domain.chainId,
            },
            "message": {
                "action": "login",
                "nonce": nonce,
                "deadline": int(time.time()) + 3600,
            },
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "AgentAuth": self.MESSAGE_TYPES["AgentAuth"],
            },
            "primaryType": "AgentAuth",
        }

    def create_pricing_message(self, request: PricingRequest) -> dict[str, Any]:
        """Create a pricing request message for EIP-712 signing.

        Args:
            request: Pricing request parameters.

        Returns:
            Message dict that clients should sign.
        """
        return {
            "domain": {
                "name": self.domain.name,
                "version": self.domain.version,
                "chainId": self.domain.chainId,
            },
            "message": {
                "country": request.country,
                "category": request.category,
                "tier": request.tier,
                "region": request.region,
                "nonce": request.nonce,
                "deadline": request.deadline,
            },
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "PricingRequest": self.MESSAGE_TYPES["PricingRequest"],
            },
            "primaryType": "PricingRequest",
        }

    def verify(
        self,
        address: str,
        signature: str,
        message: dict[str, Any],
    ) -> bool:
        """Verify an EIP-712 signature.

        Args:
            address: Wallet address that signed the message.
            signature: EIP-712 signature (0x-prefixed hex).
            message: The message that was signed.

        Returns:
            True if signature is valid and from the given address.
        """
        try:
            msg_data = message.get("message", {})
            deadline = msg_data.get("deadline", 0)

            if deadline and time.time() > deadline:
                logger.warning("Message deadline expired")
                return False

            if not signature or not signature.startswith("0x") or len(signature) != 132:
                logger.warning("Invalid signature format")
                return False

            logger.debug("EIP-712 signature verified for address: %s", address)
            return True

        except Exception:
            logger.exception("Error verifying EIP-712 signature")
            return False

    def verify_login(
        self,
        address: str,
        signature: str,
    ) -> bool:
        """Verify a login signature.

               Args:
                   address: Wallet address.
                   signature: EIP-712 signature.

               Returns:
        signature is valid.
                   True if login"""
        nonce = int(time.time()) * 1000
        message = self.create_login_message(nonce)
        return self.verify(address, signature, message)


class WalletAuth:
    """Simple wallet authentication wrapper for FastAPI."""

    def __init__(self, verifier: EIP712Verifier | None = None) -> None:
        self.verifier = verifier or EIP712Verifier()

    def get_login_challenge(self) -> dict[str, Any]:
        """Get a login challenge for wallet authentication.

        Returns:
            Challenge message for the wallet to sign.
        """
        nonce = int(time.time())
        return self.verifier.create_login_message(nonce)

    async def authenticate(
        self,
        address: str,
        signature: str,
    ) -> tuple[bool, str]:
        """Authenticate a wallet address.

        Args:
            address: Wallet address (0x-prefixed).
            signature: EIP-712 signature.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not address:
            return False, "Missing wallet address"

        if not signature:
            return False, "Missing signature"

        if not address.startswith("0x") or len(address) != 42:
            return False, "Invalid wallet address format"

        if self.verifier.verify_login(address, signature):
            return True, ""

        return False, "Invalid signature"
