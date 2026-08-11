# Dewey MCP Domain Language

Dewey MCP is a read-only gateway for agents that need to search long-running archives of news articles and images. This context defines the language used when discussing the archives and their search surfaces.

## Language

**News Archive**:
The collection of historical and current news articles that agents may search. It includes articles from 1978 to the present.
_Avoid_: corpus, dataset, index

**News Article**:
A single published story in the **News Archive**. A **News Archive** contains many **News Articles**.
_Avoid_: document, record, item

**Article Identifier**:
A stable identifier for one **News Article**.
_Avoid_: article key, document ID

**Article Chunk**:
A searchable excerpt from a **News Article**. A **News Article** may have many **Article Chunks**.
_Avoid_: snippet, passage, segment

**Image Archive**:
The collection of historical and current image metadata that agents may search. Image files remain at their referenced locations; Dewey MCP does not download, validate, proxy, or embed them.
_Avoid_: image corpus, image dataset, image index

**Archived Image**:
A single image described by metadata in the **Image Archive**.
_Avoid_: image document, image record, image item

**Image Identifier**:
A stable identifier for one **Archived Image**.
_Avoid_: image key, document ID

**Chunk Identifier**:
A stable identifier for one **Article Chunk**.
_Avoid_: chunk key, row ID

**Published Date**:
The date and time when a **News Article** was published.
_Avoid_: timestamp, publication datetime

**Captured Date**:
The date and time associated with capturing an **Archived Image**. Image Search Filters use this date.
_Avoid_: image publish date, timestamp

**Created Date**:
The date and time when an **Archived Image** or its metadata was created, as supplied by the **Image Archive**.
_Avoid_: creation timestamp

**Article Link**:
The URL where a **News Article** can be accessed.
_Avoid_: URL, href

**Author**:
The credited writer or contributor for a **News Article**.
_Avoid_: byline, creator

**Read-only Gateway**:
The boundary that lets agents query the **News Archive** and **Image Archive** without changing them. It does not ingest, update, delete, enrich, reindex, or administer **News Articles** or **Archived Images**.
_Avoid_: archive manager, ingestion service, admin service

**Search Request**:
A request from an agent to find **Article Chunks** in the **News Archive**. It includes **Search Text** and zero or more **Search Filters**.
_Avoid_: query payload, search query

**Image Search Request**:
A request from an agent to find **Archived Images** in the **Image Archive**. It includes **Search Text** and zero or more **Search Filters**.
_Avoid_: image query payload, image search query

**Search Text**:
The words or phrase an agent wants to search for across the selected archive.
_Avoid_: query, keyword string, prompt

**Search Everything**:
The explicit `*` **Search Text** value, used when an agent wants results constrained only by **Search Filters**.
_Avoid_: blank search, empty query

**Search Filter**:
A constraint that narrows which results may be returned for a **Search Request** or **Image Search Request**.
_Avoid_: facet, clause, predicate

**Search Result**:
An **Article Chunk** returned for a **Search Request**, together with the article information needed for an agent to judge relevance.
_Avoid_: hit, match, row, article result

**Image Search Result**:
An **Archived Image** returned for an **Image Search Request**, together with the metadata and image links needed for an agent to judge relevance.
_Avoid_: image hit, image match, image row

## Example Dialogue

Developer: "Should Dewey MCP let an agent correct article metadata?"

Domain expert: "No. Dewey MCP is a Read-only Gateway. It can return Search Results from the News Archive, but it cannot change News Articles."

Developer: "So a Search Request uses Search Text and optional Search Filters to find matching Article Chunks, and each returned chunk is a Search Result?"

Domain expert: "Yes. Keep that language consistent."

Developer: "Does an Image Search Result contain the image bytes?"

Domain expert: "No. It contains metadata and links for an Archived Image. The Read-only Gateway does not download, proxy, or embed image files."
