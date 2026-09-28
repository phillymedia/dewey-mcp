# Tool Reference

Dewey exposes two MCP tools over streamable HTTP. Both are read-only and use the same request shape, response wrapper, validation rules, and provider-error contract.

## Shared request fields

| Field | Type | Required | Behavior |
| --- | --- | --- | --- |
| `query` | string | Yes | Natural-language Search Text. Whitespace-only values are rejected. Use `*` for Search Everything. |
| `start_date` | `YYYY-MM-DD` | No | Inclusive lower date bound. It applies to Published Date for articles and Captured Date for images. |
| `end_date` | `YYYY-MM-DD` | No | Inclusive upper date bound. It cannot be earlier than `start_date`. |
| `authors` | array of strings | No | Matches any requested Author. Blank entries are removed and duplicates are removed case-insensitively. |
| `limit` | integer | No | Defaults to 10; minimum 1 and maximum 20. |

Date and Author filters combine with `AND`. Multiple Author values combine with `OR`. Author filtering is text matching, not exact identity matching. End dates include the entire requested day.

The explicit `*` query runs a filters-only search. A blank query never means Search Everything.

## `search_archive`

Searches the News Archive and returns matching Article Chunks.

Example request:

```json
{
  "query": "Iran hostage crisis",
  "start_date": "1979-11-01",
  "end_date": "1979-12-01",
  "authors": ["George Will"],
  "limit": 10
}
```

Successful responses contain `results` and `count`. Every result represents one Article Chunk:

```json
{
  "results": [
    {
      "source_id": "doc_article-123",
      "text": "Matching article excerpt...",
      "title": "Example headline",
      "published_date": "1979-11-15T00:00:00Z",
      "author": "George Will",
      "url": "https://example.test/article-123"
    }
  ],
  "count": 1
}
```

| Result field | Type | Notes |
| --- | --- | --- |
| `source_id` | string | Required source identifier derived from the Azure `sourcepage` field. |
| `text` | string | Required Article Chunk text. |
| `title` | string or null | News Article headline. |
| `published_date` | datetime or null | Published Date supplied by the archive. |
| `author` | string or null | Author text supplied by the archive. |
| `url` | string or null | Article Link supplied by the archive. |

Ordinary requests use Azure keyword, vector, and semantic search. Search Everything omits vector and semantic search and applies only filters and the limit. Search strategy is internal behavior; callers cannot select it.

## `search_image_archive`

Searches the Image Archive and returns Archived Image metadata and links. Dewey does not fetch or validate the linked image bytes.

Example request:

```json
{
  "query": "city hall press conference",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "authors": ["Jane Photographer"],
  "limit": 10
}
```

Example response:

```json
{
  "results": [
    {
      "id": "image-1",
      "image_url": "https://example.test/image.jpg",
      "screen_url": "https://example.test/screen.jpg",
      "title": "City hall press conference",
      "original_filename": "city-hall.jpg",
      "authors": "Jane Photographer",
      "credit": "Example News",
      "byline": "Jane Photographer / Example News",
      "ingest_source": "DAM",
      "source": "Staff",
      "caption": "City hall press conference",
      "description": "Officials speak at a lectern.",
      "created_date": "2024-01-02T10:00:00Z",
      "captured_date": "2024-01-01T14:30:00Z"
    }
  ],
  "count": 1
}
```

| Result field | Type | Notes |
| --- | --- | --- |
| `id` | string | Required Image Identifier. |
| `image_url` | string or null | Link to the original image. |
| `screen_url` | string or null | Link to the screen-sized rendition; use this for image previews. |
| `title` | string or null | Archived Image title. |
| `original_filename` | string or null | Original image filename. |
| `authors` | string or null | Author or photographer metadata. |
| `credit` | string or null | Image credit supplied by the archive. |
| `byline` | string or null | Image byline supplied by the archive. |
| `ingest_source` | string or null | Ingest source supplied by the archive. |
| `source` | string or null | Image source supplied by the archive. |
| `caption` | string or null | Image caption. |
| `description` | string or null | Searchable image description. |
| `created_date` | datetime or null | Created Date supplied by the archive. |
| `captured_date` | datetime or null | Captured Date used by date filters. |

The v2 schema consolidates preview links into `screen_url`; `thumbnail_url` is no longer returned. Metadata and links may be null when absent from the archive.

Ordinary requests combine keyword search over `title`, `original_filename`, `authors`, `credit`, `byline`, `caption`, and `description` with vector retrieval over `description_vector`. The image index has no semantic ranking configuration. Search Everything applies only filters and the limit. Author filters continue to match `authors`.

## Empty results and errors

A successful search with no matches is:

```json
{
  "results": [],
  "count": 0
}
```

Invalid input is rejected at the MCP boundary. Provider failures return a tool result with `isError: true` and one of these stable payloads:

```json
{
  "error": "search_provider_unavailable",
  "message": "The archive search provider did not respond successfully."
}
```

```json
{
  "error": "search_provider_timeout",
  "message": "The archive search provider timed out."
}
```

Provider details, credentials, raw queries, and returned content are not included in public error messages.

## Contract ownership

The implementation source of truth is `src/dewey_mcp/server.py` for exposed tool parameters and `src/dewey_mcp/models.py` for validation and result models. Public field names use snake_case. Update this reference whenever either contract changes.
