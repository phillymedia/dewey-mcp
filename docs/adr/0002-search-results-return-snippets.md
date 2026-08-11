# ADR 0002: Return Article Chunks as Search Results

**Status:** Accepted

## Context

Search callers need enough text and metadata to judge relevance without receiving complete News Articles in every response. Returning full articles would make search responses unnecessarily large, while grouping by article could hide which excerpt matched.

## Decision

Each News Archive Search Result represents one matching Article Chunk. It contains `source_id`, `text`, `title`, `published_date`, `author`, and `url`.

The request limit defaults to 10 and has a hard maximum of 20. Full-article retrieval is not part of the search tool and may be introduced later as a separate capability.

## Consequences

- Results stay small enough for an agent to scan and rank.
- One News Article can produce more than one result when several chunks match.
- Callers cannot use the search tool to retrieve a complete article body.
- Result-field and limit changes are public contract changes.

## Related documentation

- [News Archive tool reference](../tool-reference.md#search_archive)
- [Domain language](../../CONTEXT.md)
