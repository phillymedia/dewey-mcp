# Dewey MCP

Dewey MCP is a read-only gateway for agents that need to search a long-running archive of news articles. This context defines the language used when discussing the archive and its search surface.

## Language

**News Archive**:
The collection of historical and current news articles that agents may search. It includes articles from 1978 to the present.
_Avoid_: corpus, dataset, index

**Image Archive**:
The collection of image-backed archive materials that agents may search.
_Avoid_: corpus, dataset, index

**News Article**:
A single published story in the **News Archive**. A **News Archive** contains many **News Articles**.
_Avoid_: document, record, item

**Image**:
A single image-backed archive asset in the **Image Archive**.
_Avoid_: document, record, item

**Article Identifier**:
A stable identifier for one **News Article**.
_Avoid_: article key, document ID

**Article Chunk**:
A searchable excerpt from a **News Article**. A **News Article** may have many **Article Chunks**.
_Avoid_: snippet, passage, segment

**Chunk Identifier**:
A stable identifier for one **Article Chunk**.
_Avoid_: chunk key, row ID

**Image Identifier**:
A stable identifier for one **Image**.
_Avoid_: image key, row ID

**Published Date**:
The date and time when a **News Article** was published.
_Avoid_: timestamp, publication datetime

**Capture Date**:
The date and time when an **Image** was captured.
_Avoid_: timestamp, capture datetime

**Article Link**:
The URL where a **News Article** can be accessed.
_Avoid_: URL, href

**Image Link**:
The URL where an **Image** can be accessed.
_Avoid_: URL, href

**Caption**:
The short display text or editorial caption associated with an **Image**.
_Avoid_: title, label

**Description**:
The searchable text that describes an **Image**.
_Avoid_: body, text blob

**Author**:
The credited writer, contributor, or creator for a **News Article** or **Image**.
_Avoid_: byline, creator

**Read-only Gateway**:
The boundary that lets agents query the **News Archive** and **Image Archive** without changing them. It does not ingest, update, delete, enrich, reindex, or administer **News Articles** or **Images**.
_Avoid_: archive manager, ingestion service, admin service

**Search Request**:
A request from an agent to find archive material in the **News Archive** or **Image Archive**. It includes **Search Text** and zero or more **Search Filters**.
_Avoid_: query payload, search query

**Search Text**:
The words or phrase an agent wants to search for across the **News Archive**.
_Avoid_: query, keyword string, prompt

**Search Everything**:
The explicit `*` **Search Text** value, used when an agent wants matching **Article Chunks** constrained only by **Search Filters**.
_Avoid_: blank search, empty query

**Search Filter**:
A constraint that narrows which **Article Chunks** may be returned for a **Search Request**.
_Avoid_: facet, clause, predicate

**Search Result**:
Archive material returned for a **Search Request**, together with the information needed for an agent to judge relevance.
_Avoid_: hit, match, row, article result

## Example Dialogue

Developer: "Should Dewey MCP let an agent correct article metadata?"

Domain expert: "No. Dewey MCP is a Read-only Gateway. It can return Search Results from the News Archive, but it cannot change News Articles."

Developer: "So a Search Request uses Search Text and optional Search Filters to find matching Article Chunks, and each returned chunk is a Search Result?"

Domain expert: "Yes. Keep that language consistent."
