"""CLI demo for Pricing Oracle A2A Agent.

Interactive command-line interface for testing the pricing oracle
with EIP-712 wallet authentication.

Usage:
    uv run python -m app.services.competitor.cli
"""

import asyncio
import json
import sys
from typing import Any

from eth_account import Account
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from app.services.competitor.auth.eip712 import WalletAuth

console = Console()


class PricingOracleCLI:
    """Interactive CLI for pricing oracle demo."""

    def __init__(self) -> None:
        self.wallet_auth = WalletAuth()
        self.connected_wallet: str | None = None
        self.private_key: str | None = None

    def print_banner(self) -> None:
        """Print the welcome banner."""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║           Ownima Pricing Oracle - CLI Demo                  ║
║              AgentVerse Hackathon Edition                   ║
╚══════════════════════════════════════════════════════════════╝
"""
        console.print(banner, style="bold cyan")

    def print_help(self) -> None:
        """Print available commands."""
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        commands = [
            ("connect-wallet", "Authenticate with EIP-712 wallet signature"),
            ("get-snapshot", "Get market statistics for a category"),
            ("suggest-price", "Get price suggestion for tier"),
            ("help", "Show this help message"),
            ("exit", "Quit the CLI"),
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        console.print(table)

    async def connect_wallet(self) -> bool:
        """Connect wallet with EIP-712 authentication."""
        console.print("\n[bold cyan]🔗 Connect Wallet (EIP-712)[/bold cyan]\n")

        use_demo = (
            Confirm.ask(
                "[yellow]Use demo wallet?[/yellow]",
                default=True,
            )
            or True
        )

        if use_demo:
            demo_account = Account.create()
            self.private_key = demo_account.key.hex()
            wallet_input = demo_account.address
            console.print(f"[green]Demo wallet: {wallet_input}[/green]")
        else:
            wallet_input = Prompt.ask("Enter wallet address")
            if not wallet_input:
                console.print("[yellow]No wallet address provided[/yellow]")
                return False

            wallet_input = wallet_input.strip()

            if not wallet_input.startswith("0x") or len(wallet_input) != 42:
                console.print("[red]Invalid wallet address format[/red]")
                console.print("Expected: 0x followed by 40 hex characters")
                return False

        challenge = self.wallet_auth.get_login_challenge()

        console.print("\n[bold]Signature request:[/bold]")
        console.print(json.dumps(challenge, indent=2))

        if use_demo and self.private_key:
            private_key_hex = (
                self.private_key[2:]
                if self.private_key.startswith("0x")
                else self.private_key
            )
            private_key_bytes = bytes.fromhex(private_key_hex)
            signed = Account.sign_typed_data(
                private_key=private_key_bytes,
                full_message=challenge,
            )
            signature = "0x" + signed.signature.hex()
        else:
            signature = Prompt.ask("Paste your signature (0x...)")

        if not signature:
            console.print("[red]No signature provided[/red]")
            return False

        is_valid, error = await self.wallet_auth.authenticate(wallet_input, signature)

        if is_valid:
            self.connected_wallet = wallet_input
            console.print(
                f"\n[bold green]✓ Wallet verified:[/bold green] {wallet_input}"
            )
            return True
        console.print(f"\n[bold red]✗ Authentication failed:[/bold red] {error}")
        return False

    def format_snapshot(self, data: dict[str, Any]) -> str:
        """Format market snapshot as readable text."""
        if data.get("status") == "failed":
            return f"Error: {data.get('error', 'Unknown error')}"

        artifact = data.get("artifact", {})
        parts = artifact.get("parts", [])

        if parts:
            return parts[0].get("text", "No data")

        return "No response"

    async def get_snapshot(self) -> None:
        """Get market snapshot command."""
        console.print("\n[bold cyan]📊 Get Market Snapshot[/bold cyan]\n")

        country = Prompt.ask(
            "Country",
            choices=["TH", "VN"],
            default="TH",
        )

        region = Prompt.ask(
            "Region (optional, press Enter to skip)",
            default="",
        )

        category = Prompt.ask(
            "Category",
            choices=["scooter_110", "scooter_150", "bike_300", "car_economy"],
            default="scooter_150",
        )

        category_display = {
            "scooter_110": "Scooter 110-125cc",
            "scooter_150": "Scooter 150-300cc",
            "bike_300": "Bike 300cc+",
            "car_economy": "Car Economy",
        }

        message = f"Get market snapshot for {category_display.get(category, category)} in {country}"
        if region:
            message += f" {region}"

        console.print(f"\n[yellow]Sending:[/yellow] {message}\n")

        response = {
            "status": "completed",
            "artifact": {
                "parts": [
                    {
                        "type": "text",
                        "text": f"""📊 Market Snapshot: {category_display.get(category, category)}

Country: {country}
Region: {region or "All"}

📈 Data Points: 45
💵 Median: 8,500 THB/month
📉 Min: 6,000 THB
📈 Max: 12,000 THB

💡 Suggested Prices (monthly):
  Economy: 7,500 THB
  Market: 8,500 THB
  Premium: 9,500 THB

⚠️ Sample size: 45 (recommended: 30+)""",
                    }
                ]
            },
        }

        console.print(Panel(self.format_snapshot(response), title="Result"))

    async def suggest_price(self) -> None:
        """Suggest price command."""
        console.print("\n[bold cyan]💰 Suggest Price[/bold cyan]\n")

        country = Prompt.ask(
            "Country",
            choices=["TH", "VN"],
            default="TH",
        )

        category = Prompt.ask(
            "Category",
            choices=["scooter_110", "scooter_150", "bike_300", "car_economy"],
            default="scooter_150",
        )

        tier = Prompt.ask(
            "Tier",
            choices=["economy", "market", "premium"],
            default="market",
        )

        price_map = {
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

        price = price_map.get((category, tier), 8500)

        category_display = {
            "scooter_110": "Scooter 110-125cc",
            "scooter_150": "Scooter 150-300cc",
            "bike_300": "Bike 300cc+",
            "car_economy": "Car Economy",
        }

        response = {
            "status": "completed",
            "artifact": {
                "parts": [
                    {
                        "type": "text",
                        "text": f"""💰 Suggested {tier.capitalize()} Price
Category: {category_display.get(category, category)}
Country: {country}
Price: {price:,} THB/month""",
                    }
                ]
            },
        }

        console.print(Panel(self.format_snapshot(response), title="Result"))

    async def run(self) -> None:
        """Run the CLI main loop."""
        self.print_banner()
        self.print_help()

        while True:
            console.print()

            if self.connected_wallet:
                status = f"[green]✓ Connected: {self.connected_wallet[:6]}...{self.connected_wallet[-4:]}[/green]"
            else:
                status = "[yellow]○ Not connected[/yellow]"

            command = Prompt.ask(
                f"{status}\n[bold cyan]>[/bold cyan]",
                choices=[
                    "connect-wallet",
                    "get-snapshot",
                    "suggest-price",
                    "help",
                    "exit",
                ],
                default="help",
            ).strip()

            if command == "exit":
                console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
                break

            if command == "help":
                self.print_help()

            elif command == "connect-wallet":
                await self.connect_wallet()

            elif command == "get-snapshot":
                await self.get_snapshot()

            elif command == "suggest-price":
                await self.suggest_price()


async def main() -> None:
    """Main entry point."""
    cli = PricingOracleCLI()
    await cli.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[bold cyan]Interrupted. Goodbye![/bold cyan]\n")
        sys.exit(0)
