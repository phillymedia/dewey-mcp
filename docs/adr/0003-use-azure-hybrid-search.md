# Use Azure Hybrid Search

For the News Archive, Dewey MCP uses Azure AI Search hybrid search, combining text search, vector search through configured vectorizer profiles, and semantic ranking through the article index semantic configuration. This favors relevance quality for agent search workflows over a simpler lexical-only implementation. Image Archive retrieval is recorded separately in ADR 0017 because that index has no semantic configuration.

Hybrid search is fixed internal behavior, not an agent-selectable option in the MCP contract. Agents provide Search Text, Search Filters, and an optional result limit; the gateway owns the Azure search strategy.

The initial Azure index uses `text_vector` as the vector field. The Azure adapter maps provider fields into the MCP result contract: `sourcepage` filename stem to `source_id` with a `doc_` prefix, `chunk` to `text`, `headline` to `title`, `publish_date` to `published_date`, `authors` to `author`, and `link` to `url`.
