# AGENTS.md — pricing-oracle

The guide for every AI agent in this repository. `CLAUDE.md` holds only `@AGENTS.md`,
so Claude Code and every other agent read the same text.

**This repository is public.** Nothing private from the Ownima organisation goes here:
no hostnames, keys, internal URLs or customer data.

## State: a dormant prototype

All of the history is 2026-03-09 to 2026-03-11, with nothing since. The code runs in
parts, and the README promises more than the code has. Trust the code over the README.
This is what was true on 2026-10-17:

- **No tests, no CI.** `pyproject.toml` sets `testpaths = ["tests"]`, but `tests/` does not
  exist, and there is no `.github/`. Write the first test before you change behaviour.
- **The Dockerfile does not build.** It copies `pricing_oracle/`, but the package lives in
  `src/pricing_oracle/`. `docker-compose.yml` starts the uAgent with
  `python -m pricing_oracle.uagent`, but `uagent/` has no `__main__.py`.
- **The A2A agent is not wired up.** `a2a/agent.py` is never imported, and its card URL is
  hardcoded to `http://localhost:8000/a2a`.
- **README vs code.** `POST /price` and the `"success"` health response belong to the
  uAgent, not to the FastAPI app. FastAPI serves `GET /health`, `GET /v1/market/snapshot`
  and `GET /v1/pricing/suggest`. The README's tests, `mypy pricing_oracle` and LICENSE link
  point at things that don't exist.
- `NEXT_SESSION.md` is a handoff note from March, not current state.

## Layout

All code is in `src/pricing_oracle/` (setuptools, `where = ["src"]`):

| Path | What |
|---|---|
| `api/main.py` | FastAPI app. Creates its schema at startup with `SQLModel.metadata.create_all` |
| `service.py` | Market data: owner-api first, then the local DB (last 30 days), then `MOCK_MARKET_DATA` |
| `models.py` | SQLModel tables `countries`, `regions`, `competitor_listings`; `CategoryEnum` |
| `uagent/` | Fetch.ai uAgent (`agent.py`) and Agentverse registration |
| `a2a/` | Google A2A agent card and handler (not served) |
| `adapters/` | `Adapter` protocol and an empty `AdapterRegistry`: no scraper exists yet |
| `cli/` | `pricing-oracle` (wallet demo) and `pricing-oracle-register` |

Run things through the `pyproject.toml` entry points: `uv run pricing-oracle-api`
(port 8000), `uv run pricing-oracle-uagent`, `uv run pricing-oracle-register`. Database:
Postgres via `DATABASE_URL`. There are no migrations, even though `alembic` is a dependency.

## Traps

- **Two category spellings.** `CategoryEnum` values are uppercase (`SCOOTER_110_125CC`),
  and FastAPI expects those. The uAgent and the README use lowercase (`scooter_150`).
  In `service.py` the `category_map` is keyed by lowercase, but it is looked up with the
  uppercase enum value, so the map never matches.
- **The uAgent ignores `service.py` and the DB.** It answers from the hardcoded
  `PRICE_MAP` in `uagent/agent.py`, with a fallback of 8500. A pricing fix in `service.py`
  does not reach uAgent users.
- **Both servers default to port 8000** (`api/main.py`, `PRICING_AGENT_PORT`). Running both
  needs one of them moved.
- **Seeds are identities.** The uAgent's address comes from its seed, read from
  `PRICING_AGENT_SEED` and `AGENT_SEED_PHRASE`. Both fall back to a default that is
  written in this public repo, so any deployment that leaves them unset has an identity
  anyone can reproduce. Always set them. Never print a seed, not even a prefix.
- **Agentverse:** registration goes to `/submit`, not `/webhook`. The chat protocol is
  `Protocol(spec=chat_protocol_spec)` through `QuotaProtocol`, and the chat models are
  immutable. The uAgent registers itself at startup when a key is set, so a second
  `pricing-oracle-register` is usually redundant. `av-mcp_mdc.mdc` is the uAgents v0.22.9
  reference these rules come from.

## Checks

```bash
uv run --extra dev ruff check . && uv run --extra dev ruff format --check .
uv run --extra dev mypy src
```

**Neither is green yet.** On 2026-10-17 `ruff check` reported 21 errors and `mypy src`
46 errors in 8 files; `ruff format --check` was clean. Don't add to either count, and
compare against these numbers rather than expecting zero.

There is nothing to run for tests yet (see above). Commit messages: Conventional Commits
(`feat:`, `fix:`, `chore:`). The early history mixes styles; don't copy that.
