# Domain Docs

How engineering agents should consume this repository's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repository root.
- **`docs/adr/`** for decisions that touch the area being changed.

If one of these sources does not exist, proceed silently. Do not suggest creating documentation before the relevant language or decision has been resolved.

## File structure

This is a single-context repository:

```text
/
|-- CONTEXT.md
|-- docs/
|   |-- architecture.md
|   |-- contributing.md
|   |-- getting-started.md
|   |-- operations.md
|   |-- tool-reference.md
|   `-- adr/
|       |-- README.md
|       `-- 0001-typed-search-filters.md
`-- src/
```

`CONTEXT.md` owns domain vocabulary. The task-oriented guides under `docs/` describe current behavior. ADRs explain why durable constraints exist. Prefer links between those layers over repeating the same facts.

## Use the glossary's vocabulary

When output names a domain concept in an issue title, refactor proposal, hypothesis, or test name, use the term defined in `CONTEXT.md`. Do not drift to a synonym the glossary explicitly avoids.

If a needed concept is missing, reconsider whether the term belongs to this domain. If it represents a real gap, note it for the domain-documentation workflow.

## Flag ADR conflicts

If proposed work contradicts an accepted ADR, surface the conflict instead of silently overriding it. For example:

> _Contradicts ADR 0003 (Azure hybrid search), but worth reopening because the replacement provider has no vector capability._
