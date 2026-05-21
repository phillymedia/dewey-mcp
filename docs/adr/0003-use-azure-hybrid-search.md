# Use Azure Hybrid Search

Dewey MCP uses Azure AI Search hybrid search for its initial retrieval strategy, combining text search, vector search through configured vectorizer profiles, and semantic ranking through the index semantic configuration. This favors relevance quality for agent search workflows over a simpler lexical-only implementation.

Hybrid search is fixed internal behavior, not an agent-selectable option in the MCP contract. Agents provide Search Text, Search Filters, and an optional result limit; the gateway owns the Azure search strategy.

The initial Azure index uses `text_vector` as the vector field. The Azure adapter maps provider fields into the MCP result contract: `parent_id` to `article_id`, `headline` to `title`, `publish_date` to `published_date`, `authors` to `author`, and `chunk` to `chunk_text`.
