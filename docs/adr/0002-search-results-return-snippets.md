# Search Results Return Snippets

The search tool returns Search Results as individual matching Article Chunks suitable for judging relevance, not full News Article text and not grouped article-level results. Full article retrieval is a separate capability that may be added as a future MCP tool, keeping search responses focused and preventing large article bodies from becoming part of the initial search contract.

Each Search Result returns these fields: `source_id`, `text`, `title`, `published_date`, `author`, and `url`. `source_id` identifies the source document for the returned Article Chunk.

The search tool allows agents to request a result limit, defaults to `10`, and enforces a hard maximum of `20`.
