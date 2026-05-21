# Use Typed Search Filters

Dewey MCP exposes a single structured search tool whose Search Request contains Search Text and zero or more typed Search Filters. Agents do not send raw Azure AI Search filter expressions; the gateway validates an allowlisted filter model and owns translation into Azure AI Search syntax, which keeps the MCP contract stable, safer, and independent from Azure-specific query mechanics.

## Consequences

The server needs explicit validation for supported filter fields and operators. Pydantic is the preferred mechanism for modeling and validating the Search Request at the MCP boundary.

The initial supported Search Filters are Published Date and Author. Published Date maps to the Azure AI Search `publish_date` field, which is a `DateTimeOffset`; Published Date filtering is range-only and uses half-open ranges where `start` is inclusive and `end` is exclusive. Author maps to the Azure AI Search `authors` field using `@search.ismatch` because the field is searchable rather than filterable. Author filtering means author text matches the requested phrase; it does not mean exact author identity equality.

`search_text` is required and must not be blank. The explicit `*` value is allowed as Search Everything behavior when the agent wants results constrained only by Search Filters.

Multiple Search Filters in one Search Request are combined with `AND` semantics.
