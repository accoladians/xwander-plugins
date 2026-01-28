---
name: airtable-ops
description: Activate when user needs Airtable operations - record management, batch operations, formula building, or schema inspection. Provides AI-optimized Airtable workflows.
version: 1.0.0
---

# Airtable Operations Skill

## Purpose

Guide Claude through efficient Airtable operations using the xwander-airtable toolkit. Complements the Airtable MCP with batch operations, formula building, and optimized workflows.

## When to Use

Activate this skill when user:
- Needs to create, update, or delete multiple records
- Asks about filterByFormula syntax
- Wants batch operations with progress
- Needs schema inspection or caching
- Asks to "sync", "export", or "import" Airtable data
- References calendars, schedules, or CRM data in Airtable

## Key Advantages Over Raw MCP

| Operation | MCP | This Plugin |
|-----------|-----|-------------|
| Create 100 records | 100 API calls | 10 batched calls |
| Filter formula | Manual string building | Type-safe builder |
| Schema lookup | Fetched every call | Cached (5 min TTL) |
| Rate limiting | Not handled | Automatic (5 req/sec) |
| Progress feedback | None | Built-in callbacks |

## Formula Builder

The formula builder prevents syntax errors and handles escaping:

### Basic Comparisons

```python
from xwander_airtable.formula import Formula, F

# Equality
F.equals("Status", "Active")
# Output: {Status} = "Active"

# Not equals
F.not_equals("Type", "Private")
# Output: {Type} != "Private"

# Numeric comparisons
F.greater_than("Price", 100)
F.less_or_equal("Count", 50)
```

### Text Functions

```python
# Contains (FIND)
F.contains("Notes", "urgent")
# Output: FIND("urgent", {Notes}) > 0

# Starts with
F.starts_with("Name", "Summer")
# Output: FIND("Summer", {Name}) = 1

# Regex match
F.regex_match("Email", ".*@xwander.com")
```

### Date Functions

```python
# After specific date
F.is_after("Start Date", "2026-06-01")
# Output: IS_AFTER({Start Date}, "2026-06-01")

# After today (dynamic)
F.is_after_today("End Date")
# Output: IS_AFTER({End Date}, TODAY())

# Same day
F.is_same("Created", "2026-01-28", "day")
```

### Combining Conditions

```python
# AND
F.equals("Track", "Day Tours").and_(F.not_empty("Start Date"))
# Output: AND({Track} = "Day Tours", {Start Date} != "")

# OR
F.equals("Status", "Active").or_(F.equals("Status", "Pending"))

# Multiple values (IN list)
F.in_list("Track", ["Day Tours", "Academy", "Erasmus+"])
# Output: OR({Track} = "Day Tours", {Track} = "Academy", {Track} = "Erasmus+")

# Complex: All of multiple conditions
F.all_of(
    F.equals("Track", "Day Tours"),
    F.is_after("Start Date", "2026-06-01"),
    F.contains("Notes", "morning")
)
```

### Fluent Builder

```python
from xwander_airtable.formula import FormulaBuilder

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

### Batch Create

```python
from xwander_airtable import AirtableClient

client = AirtableClient()

# Create with progress
records = [{"Name": f"Event {i}"} for i in range(100)]
result = client.batch_create(
    "app5ctfBdvOxmTpOM",
    "Events",
    records,
    progress=True,  # Shows: Progress: 50/100 (50%)
)

print(f"Created: {result.successful}, Failed: {result.failed}")
```

### Batch Update

```python
updates = [
    {"id": "rec123", "fields": {"Status": "Active"}},
    {"id": "rec456", "fields": {"Status": "Active"}},
]
result = client.batch_update("app123", "Events", updates)
```

### Batch Delete

```python
record_ids = ["rec123", "rec456", "rec789"]
result = client.batch_delete("app123", "Events", record_ids)
```

### Batch Upsert

```python
# Update or insert based on matching fields
records = [
    {"Name": "Summer Tour", "Date": "2026-06-15", "Status": "Active"},
    {"Name": "Winter Tour", "Date": "2026-12-15", "Status": "Draft"},
]
result = client.batch_upsert(
    "app123",
    "Events",
    records,
    merge_on=["Name", "Date"],  # Unique key fields
)
```

## CLI Commands

```bash
# List bases
xw airtable list-bases

# Get schema (cached)
xw airtable schema --base app5ctfBdvOxmTpOM --fields

# List records with formula
xw airtable list-records \
  --base app5ctfBdvOxmTpOM \
  --table Events \
  --formula '{Track} = "Day Tours"' \
  --limit 50

# Batch create from file
xw airtable batch-create \
  --base app5ctfBdvOxmTpOM \
  --table Events \
  --file records.json

# Test formula syntax
xw airtable formula --equals "Status=Active" --after "Start Date:2026-06-01"
```

## Common Workflows

### 1. Populate Calendar with Events

```python
from xwander_airtable import AirtableClient
from xwander_airtable.formula import F
from datetime import date, timedelta

client = AirtableClient()
BASE = "app5ctfBdvOxmTpOM"

# Generate weekly events for summer
events = []
current = date(2026, 6, 1)
end = date(2026, 8, 31)

while current <= end:
    if current.weekday() == 5:  # Saturday
        events.append({
            "Name": "Day Tour",
            "Track": "Day Tours",
            "Start Date": current.isoformat(),
            "End Date": current.isoformat(),
        })
    current += timedelta(days=1)

result = client.batch_create(BASE, "Events", events, progress=True)
print(f"Created {result.successful} events")
```

### 2. Filter and Update Records

```python
# Find all pending events after today
formula = F.equals("Status", "Pending").and_(F.is_after_today("Start Date"))

records = client.list_records(
    BASE, "Events",
    formula=formula,
    max_records=100,
)

# Update to Active
updates = [
    {"id": r["id"], "fields": {"Status": "Active"}}
    for r in records
]
result = client.batch_update(BASE, "Events", updates, progress=True)
```

### 3. Sync External Data

```python
# Upsert pattern - update existing or create new
external_data = [
    {"External ID": "ext-001", "Name": "Item 1", "Value": 100},
    {"External ID": "ext-002", "Name": "Item 2", "Value": 200},
]

result = client.batch_upsert(
    BASE, "Sync Table",
    external_data,
    merge_on=["External ID"],
    typecast=True,  # Auto-convert field types
)
```

## Rate Limiting

The plugin automatically handles Airtable's 5 requests/second/base limit:

```python
# Rate limiting is automatic - no extra code needed
for i in range(100):
    client.create_record(BASE, "Events", {"Name": f"Event {i}"})
    # Automatically throttled to 5 req/sec
```

## Schema Caching

Schemas are cached for 5 minutes by default:

```python
# First call - fetches from API
schema = client.get_schema(BASE)

# Subsequent calls - uses cache
schema = client.get_schema(BASE)

# Force refresh
schema = client.get_schema(BASE, use_cache=False)

# Invalidate cache
client.invalidate_cache(BASE)
```

## Error Handling

```python
from xwander_airtable import AirtableClient
from xwander_airtable.exceptions import (
    AirtableError,
    RateLimitError,
    NotFoundError,
    ValidationError,
)

try:
    record = client.get_record(BASE, "Events", "recINVALID")
except NotFoundError as e:
    print(f"Record not found: {e.resource_id}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ValidationError as e:
    print(f"Validation error on field: {e.field}")
except AirtableError as e:
    print(f"Airtable error [{e.status_code}]: {e.message}")
```

## Context: Xwander Nordic Calendar

- **Base ID:** app5ctfBdvOxmTpOM
- **Events Table:** tbl6W7GHp31cVnZ3u
- **Packages Table:** tbl2NtM9i85lcqeqE
- **Flights Table:** tblUqHsaqBTnxPsgo

### Tracks (Swimlanes)
- Erasmus+
- Academy
- Day Tours
- Week Packages
- Cap of the North

## Related Skills

- **gaql-queries** - For Google Ads data analysis
- **gsheet-ops** - For Google Sheets operations

## Resources

- **Plugin Code:** /srv/plugins/xwander-airtable/
- **Airtable MCP:** airtable-mcp-server (complements this plugin)
- **API Docs:** https://airtable.com/developers/web/api/introduction
- **Formula Reference:** https://support.airtable.com/docs/formula-field-reference

## Troubleshooting

### "Rate limit exceeded"
The plugin auto-throttles, but if you see this:
- Check if multiple processes are hitting the same base
- Add `time.sleep(0.2)` between operations

### "Invalid formula"
Use the formula builder to avoid syntax errors:
```bash
xw airtable formula --equals "Status=Active" --contains "Notes:urgent"
```

### "Field not found"
- Check schema: `xw airtable schema --base BASE_ID --fields`
- Field names are case-sensitive
- Use field names, not IDs in formulas

### Authentication error
- Ensure AIRTABLE_TOKEN is set
- Token must have correct base permissions
- Check token hasn't expired
