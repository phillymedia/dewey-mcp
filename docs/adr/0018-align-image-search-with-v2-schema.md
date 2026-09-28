# ADR 0018: Align Image Search with the v2 Schema

**Status:** Accepted

## Context

The `inq-betadam-images-v2` schema removes `thumbnail_url`, retains `screen_url` for previews, and adds title, filename, attribution, and source metadata. Selecting the removed field would fail Azure searches.

## Decision

Use `screen_url` as the single preview link and remove `thumbnail_url` from Image Search Results. Keep `image_url` for the original image. Return the new metadata as nullable fields.

Extend the keyword fields described in ADR 0017 to include `title`, `original_filename`, `credit`, and `byline`. Keep description-vector retrieval, Captured Date filters, and Author filters on `authors`.

## Consequences

- Clients that read `thumbnail_url` must switch to `screen_url`.
- Searches can match the added searchable metadata, which can change ranking.
- Source metadata is returned but is not used for keyword search because those fields are not searchable.
- Deployments must configure an image index with the v2 schema.

## Related documentation

- [Image tool reference](../tool-reference.md#search_image_archive)
- [Azure adapters](../architecture.md#azure-adapters)
- [ADR 0017](0017-image-hybrid-search-and-dual-readiness.md)
