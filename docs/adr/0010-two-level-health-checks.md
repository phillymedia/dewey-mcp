# ADR 0010: Use Two-Level Health Checks

**Status:** Accepted

## Context

Container infrastructure needs to distinguish a running web process from an instance that cannot serve the complete public search surface. Treating provider failure as a process crash would blur recovery and routing decisions.

## Decision

Dewey exposes liveness and readiness separately. Liveness confirms that the server process responds. Readiness probes both the News Archive and Image Archive providers with lightweight document-count requests.

If either provider is unavailable or times out, readiness returns HTTP 503 while liveness remains successful.

## Consequences

- Platforms can restart dead processes without restarting every instance affected by an external outage.
- Traffic can be removed from an instance that cannot reach either required index.
- The service is intentionally not partially ready when only one archive works.
- Health route changes must be coordinated with deployment probes.

## Related documentation

- [Health checks](../operations.md#health-checks)
- [Process lifecycle](../architecture.md#process-lifecycle)
- [ADR 0017](0017-image-hybrid-search-and-dual-readiness.md)
