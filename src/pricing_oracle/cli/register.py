"""Registration CLI for pricing oracle agent."""

from __future__ import annotations

import os
import sys

from rich.console import Console
from rich.table import Table

from pricing_oracle.uagent.agent import (
    AGENT_NAME,
    AGENT_SEED,
    _AGENT_DOMAIN,
    _AGENT_NETWORK,
)
from pricing_oracle.uagent.registration import (
    AGENT_DESCRIPTION,
    AGENT_METADATA,
    AGENT_README,
)

console = Console()


def main() -> None:
    """Register the pricing oracle agent on AgentVerse."""
    console.print("[bold cyan]Pricing Oracle Agent Registration[/bold cyan]\n")

    # Get configuration
    api_key = os.getenv("AGENTVERSE_KEY") or os.getenv("ILABS_AGENTVERSE_API_KEY")
    seed = os.getenv("AGENT_SEED_PHRASE", AGENT_SEED)
    domain = os.getenv("PRICING_AGENT_DOMAIN", _AGENT_DOMAIN)
    endpoint = f"{domain}/submit"

    # Display configuration
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Agent Name", AGENT_NAME)
    table.add_row("Endpoint", endpoint)
    table.add_row("Network", _AGENT_NETWORK)
    table.add_row("API Key", f"{api_key[:10]}..." if api_key else "[red]NOT SET[/red]")
    table.add_row("Seed", f"{seed[:10]}..." if seed else "[red]NOT SET[/red]")

    console.print(table)
    console.print()

    # Validate
    if not api_key:
        console.print("[bold red]Error:[/bold red] AGENTVERSE_KEY not set")
        console.print(
            "  Set AGENTVERSE_KEY or ILABS_AGENTVERSE_API_KEY environment variable"
        )
        sys.exit(1)

    if not seed:
        console.print("[bold red]Error:[/bold red] Seed not set")
        console.print("  Set AGENT_SEED_PHRASE environment variable or use default")
        sys.exit(1)

    # Perform registration
    try:
        from uagents_core.utils.registration import (
            RegistrationRequestCredentials,
            register_chat_agent,
        )

        console.print("[bold]Registering agent...[/bold]")

        register_chat_agent(
            name=AGENT_NAME,
            endpoint=endpoint,
            active=True,
            credentials=RegistrationRequestCredentials(
                agentverse_api_key=api_key,
                agent_seed_phrase=seed,
            ),
            readme=AGENT_README,
            description=AGENT_DESCRIPTION,
            metadata=AGENT_METADATA,
        )

        console.print("[bold green]Registration successful![/bold green]")
        console.print(f"  Agent: {AGENT_NAME}")
        console.print(f"  Endpoint: {endpoint}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
