# xwander-airtable

AI-first Airtable toolkit for Claude Code that complements the Airtable MCP server.

## Why This Plugin?

The Airtable MCP server is functional but has gaps that cause token waste and suboptimal workflows:

| Gap | MCP Behavior | This Plugin |
|-----|-------------|-------------|
| **Rate Limiting** | None (429 errors) | Token bucket (5 req/sec) |
| **Batch Operations** | 1 record at a time | Auto-chunked (10/batch) |
| **Formula Building** | Manual string concat | Type-safe builder |
| **Schema Caching** | Fetched every call | 5-min TTL cache |
| **Progress Feedback** | None | Built-in callbacks |

## Installation

```bash
cd /srv/plugins/xwander-airtable
pip install -e .
```

## Quick Start

### Python API

```python
from xwander_airtable import AirtableClient
from xwander_airtable.formula import F

# Initialize client (uses AIRTABLE_TOKEN env var)
client = AirtableClient()

# List records with type-safe formula
records = client.list_records(
    base_id="app5ctfBdvOxmTpOM",
    table="Events",
    formula=F.equals("Track", "Day Tours").and_(F.is_after_today("Start Date")),
    max_records=50,
)

# Batch create with progress
result = client.batch_create(
    "app5ctfBdvOxmTpOM",
    "Events",
    [{"Name": f"Event {i}", "Track": "Day Tours"} for i in range(100)],
    progress=True,  # Shows: Progress: 50/100 (50%)
)
print(f"Created: {result.successful}, Failed: {result.failed}")
```

### CLI

```bash
# List bases
xw airtable list-bases

# Get schema (cached)
xw airtable schema --base app5ctfBdvOxmTpOM --fields

# List records with formula filter
xw airtable list-records \
  --base app5ctfBdvOxmTpOM \
  --table Events \
  --formula '{Track} = "Day Tours"' \
  --limit 50

# Batch create from JSON file
xw airtable batch-create \
  --base app5ctfBdvOxmTpOM \
  --table Events \
  --file records.json

# Test formula building
xw airtable formula --equals "Status=Active" --after "Start Date:2026-06-01"
```

## Formula Builder

Prevent syntax errors with the type-safe formula builder:

```python
from xwander_airtable.formula import Formula, F, FormulaBuilder

# Simple equality
F.equals("Status", "Active")
# Output: {Status} = "Active"

# Contains (FIND)
F.contains("Notes", "urgent")
# Output: FIND("urgent", {Notes}) > 0

# Date comparisons
F.is_after("Start Date", "2026-06-01")
F.is_after_today("End Date")

# Combining conditions
F.equals("Track", "Day Tours").and_(F.not_empty("Start Date"))
# Output: AND({Track} = "Day Tours", {Start Date} != "")

# Multiple values (IN list)
F.in_list("Track", ["Day Tours", "Academy", "Erasmus+"])
# Output: OR({Track} = "Day Tours", {Track} = "Academy", {Track} = "Erasmus+")

# Fluent builder
formula = (
    FormulaBuilder()
    .where("Status", "Active")
    .and_where("Track", "Day Tours")
    .after("Start Date", "2026-06-01")
    .not_empty("Location")
    .build()
)
```

## Batch Operations

All batch operations auto-chunk to 10 records (Airtable's limit):

```python
# Batch create
result = client.batch_create("app123", "Events", records, progress=True)

# Batch update
updates = [{"id": "rec123", "fields": {"Status": "Active"}}]
result = client.batch_update("app123", "Events", updates)

# Batch delete
result = client.batch_delete("app123", "Events", ["rec123", "rec456"])

# Batch upsert (update or insert)
result = client.batch_upsert(
    "app123", "Events", records,
    merge_on=["Name", "Date"],  # Unique key fields
)
```

## Error Handling

Typed exceptions for specific error conditions:

```python
from xwander_airtable.exceptions import (
    AirtableError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
)

try:
    record = client.get_record(BASE, "Events", "recINVALID")
except NotFoundError as e:
    print(f"Record not found: {e.resource_id}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ValidationError as e:
    print(f"Validation error on field: {e.field}")
```

## Xwander Nordic Calendar Context

- **Base ID:** `app5ctfBdvOxmTpOM`
- **Events Table:** `tbl6W7GHp31cVnZ3u`
- **Packages Table:** `tbl2NtM9i85lcqeqE`
- **Tracks:** Erasmus+, Academy, Day Tours, Week Packages, Cap of the North

## Architecture

```
xwander-airtable/
├── .claude-plugin/
│   └── plugin.json       # Claude Code plugin manifest
├── xwander_airtable/
│   ├── __init__.py       # Package exports
│   ├── client.py         # Main AirtableClient
│   ├── formula.py        # Type-safe formula builder
│   ├── batch.py          # Batch operations
│   ├── rate_limiter.py   # Token bucket rate limiter
│   ├── exceptions.py     # Typed exceptions
│   └── cli.py            # CLI commands
├── skills/
│   └── airtable-ops/
│       └── SKILL.md      # Claude Code skill definition
├── tests/
│   └── test_formula.py   # Unit tests
├── setup.py              # Package installation
└── README.md             # This file
```

## Environment Variables

- `AIRTABLE_TOKEN` - Personal Access Token (required)

## Related

- **Airtable MCP:** Standard MCP for basic operations
- **SKILL.md:** `/srv/plugins/xwander-airtable/skills/airtable-ops/SKILL.md`
- **API Docs:** https://airtable.com/developers/web/api/introduction

## License

Proprietary - Xwander Productions
