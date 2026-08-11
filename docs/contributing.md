# Contributing

This guide explains the repository workflow and where common changes belong. Complete [Getting Started](getting-started.md) first.

## Before changing code

1. Read the canonical [domain language](../CONTEXT.md).
2. Read the [architecture guide](architecture.md) for the boundary you will change.
3. Check the [ADR index](adr/README.md) for decisions that constrain the change.
4. Inspect nearby tests before editing the implementation.

Use the defined domain terms in code, tests, issues, and documentation. If a proposed change conflicts with an accepted ADR, call out the conflict and decide whether the ADR should be superseded instead of silently contradicting it.

## Development setup

Install the locked development environment:

```bash
uv sync --dev
uv run pre-commit install
```

The application supports Python 3.11 and newer. Dependency declarations belong in `pyproject.toml`; `uv.lock` records the resolved environment. Keep runtime packages in `project.dependencies` and maintenance tools in the `dev` dependency group.

## Required checks

Run these before opening or merging a change:

```bash
uv lock --check
uv run pytest
uv run ruff check src tests main.py
uv run black --check src tests main.py
```

These checks cover the maintained application and test code. The optional experimental notebooks are not part of the application lint and format gate.

For deployment-related changes, also complete the [Docker preflight](operations.md#docker-preflight). A merge to `main` deploys automatically.

## Test strategy

The test strategy has three layers:

1. Unit tests cover request validation, filter translation, result mapping, settings, limits, retry classification, and other isolated behavior.
2. MCP tool tests assemble the server with fake providers and verify discovery, routing, structured responses, errors, readiness, and cleanup.
3. Live Azure integration tests are opt-in and validate assumptions against real indexes when needed.

The repository currently contains the unit and MCP/fake-provider layers. Live Azure verification is performed only when a change requires it; live tests added in the future must remain opt-in. The default `uv run pytest` command must stay deterministic, credential-free, and network-free. Prefer a fake provider when testing MCP behavior and a fake Azure client when testing adapter behavior.

## Where changes belong

| Change | Primary location | Also update |
| --- | --- | --- |
| Tool parameter or result field | `server.py`, `models.py` | Tool tests, [tool reference](tool-reference.md), and an ADR when the contract decision changes. |
| Validation or filter semantics | `models.py`, `filters.py` | Unit tests, tool reference, and relevant ADR. |
| Azure query or field mapping | Provider adapter | Adapter tests and [architecture](architecture.md). |
| Provider selection or construction | `settings.py`, `providers/factory.py` | Settings tests, operations, and architecture. |
| Error contract | `errors.py`, `server.py` | Tool tests, tool reference, and ADR 0008. |
| Health or lifecycle behavior | `server.py`, provider protocols | Server tests, operations, architecture, and ADR 0010. |
| Runtime setting | `settings.py`, `.env.template` | Settings tests and operations. |
| Deployment behavior | `Dockerfile` or `.github/workflows/` | Docker verification and operations. |

Keep MCP code dependent on Dewey-owned models and protocols. Azure SDK types, query construction, response shapes, and field mappings remain inside provider-facing modules.

## Adding a search provider

Azure is currently the only provider. To add another backend:

1. Implement `ArchiveSearchProvider` and/or `ImageSearchProvider` from `ports.py`, including asynchronous `search`, `probe`, and `close` methods.
2. Keep backend query construction, credentials, SDK objects, retries, and response mapping inside adapter modules under `providers/`.
3. Return Dewey request and response models across the protocol boundary.
4. Map expected backend failures to `SearchProviderError` or `SearchProviderTimeoutError` so the public contract stays stable.
5. Register construction in `providers/factory.py` and extend the validated `SEARCH_PROVIDER` values in `settings.py`.
6. Add adapter tests with fake clients and MCP tests if tool-level behavior changes.
7. Update architecture, operations, and any affected decisions.

Do not build a dynamic plugin system as part of the first additional adapter unless a separate decision explicitly establishes that requirement.

## Documentation rules

Each fact has one canonical home:

- `README.md` introduces and routes readers; it does not duplicate reference material.
- `CONTEXT.md` defines domain language.
- `docs/tool-reference.md` describes the public MCP contract.
- `docs/architecture.md` explains code boundaries and current internal behavior.
- `docs/operations.md` owns runtime and deployment procedures.
- `docs/adr/` records why durable decisions were made.
- `docs/agents/` configures automation and is not contributor onboarding.

Use relative links. Commands should be runnable from the repository root unless the text says otherwise. When behavior changes, update its canonical guide in the same pull request.

## Issue workflow

Issues and PRDs are tracked in GitHub Issues for `KevoHoff/dewey-mcp`. Agent-specific commands and triage mappings live in `docs/agents/`; human contributors can use the same labels through the GitHub interface or `gh` CLI.
