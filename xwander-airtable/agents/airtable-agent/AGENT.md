# Airtable Agent

Specialized agent for Airtable operations with the xwander-airtable toolkit.

## Capabilities

- Formula building with type-safe syntax
- Batch operations with progress tracking
- Schema inspection and caching
- Calendar/event management for Xwander Nordic

## Tools Available

- `xw airtable list-bases` - List accessible Airtable bases
- `xw airtable schema --base BASE_ID` - Get base schema
- `xw airtable list-records --base BASE_ID --table TABLE` - List records
- `xw airtable batch-create --base BASE_ID --table TABLE --file FILE` - Batch create
- `xw airtable formula --equals "Field=Value"` - Build and test formulas

## Python API

```python
from xwander_airtable import AirtableClient
from xwander_airtable.formula import F

client = AirtableClient()

# Query with formula
records = client.list_records(
    "app5ctfBdvOxmTpOM", "Events",
    formula=F.equals("Track", "Day Tours").and_(F.is_after_today("Start Date"))
)

# Batch create
result = client.batch_create("app5ctfBdvOxmTpOM", "Events", records, progress=True)
```

## When to Use

Use this agent when:
- Creating/updating multiple Airtable records
- Building complex filterByFormula queries
- Syncing data with Airtable
- Managing calendar events in Airtable

## Context: Xwander Nordic Calendar

- **Base ID:** app5ctfBdvOxmTpOM
- **Events Table:** tbl6W7GHp31cVnZ3u
- **Tracks:** Erasmus+, Academy, Day Tours, Week Packages, Cap of the North
