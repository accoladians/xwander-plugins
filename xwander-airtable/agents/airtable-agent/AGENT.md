# Airtable Agent

Specialized sub-agent for bulk Airtable operations. Saves orchestrator tokens
by handling batch operations, field management, and transforms internally.

## When to Delegate Here

| Task | Token Savings |
|------|---------------|
| Batch create/update/delete (>10 records) | 80-90% |
| Rename field values across table | 90%+ |
| Bulk transforms (set values where, copy field) | 85% |
| Schema inspection + multi-step operations | 70% |
| Field option management | 60% |

## Invocation

```python
Task(subagent_type="backend-agent", prompt="""
You are the Airtable Agent. Use the xwander-airtable Python library.

TASK: Rename Track "Week Packages" to "Holiday Packages" in Events table.

CONTEXT:
- Base: app5ctfBdvOxmTpOM
- Table: Events (tbl6W7GHp31cVnZ3u)
- Library: /srv/plugins/xwander-airtable/

APPROACH:
1. Import: from xwander_airtable import AirtableClient
2. Use client.transforms.rename_values() for smart rename
3. Report result

TOKEN: Set AIRTABLE_TOKEN from ~/.claude.json mcpServers.airtable.env.AIRTABLE_API_KEY
""", description="Airtable bulk rename")
```

## Python API

```python
import json
from pathlib import Path
from xwander_airtable import AirtableClient
from xwander_airtable.formula import F

# Token from MCP config
config = json.loads(Path.home().joinpath(".claude.json").read_text())
token = config["mcpServers"]["airtable"]["env"]["AIRTABLE_API_KEY"]
client = AirtableClient(token=token)

# === Field Option Management ===
# Rename select option (1 API call, affects ALL records)
client.fields.rename_option("app123", "Events", "Track",
    "Week Packages", "Holiday Packages")

# Add new option
client.fields.add_option("app123", "Events", "Track",
    "New Track", color="cyanLight2")

# Delete option
client.fields.delete_option("app123", "Events", "Track", "Old Track")

# === Smart Transforms ===
# Auto-detects: select field → rename option, text field → batch update
result = client.transforms.rename_values("app123", "Events", "Track",
    "Week Packages", "Holiday Packages")

# Set value on all records matching formula
result = client.transforms.set_values_where("app123", "Events",
    field="Status", value="Done",
    formula=F.equals("Track", "Academy"))

# Copy field values
result = client.transforms.copy_field("app123", "Events",
    from_field="Name", to_field="Display Name")

# Clear field values by formula
result = client.transforms.clear_field_where("app123", "Events",
    field="Notes", formula=F.is_before("End Date", "2026-01-01"))

# === Batch Operations ===
# Create (auto-chunks to 10/request)
result = client.batch_create("app123", "Events", records, progress=True)

# Update
updates = [{"id": "recXXX", "fields": {"Status": "Done"}}]
result = client.batch_update("app123", "Events", updates, progress=True)

# Delete
result = client.batch_delete("app123", "Events", ["rec1", "rec2"], progress=True)

# Upsert (update or create by key)
result = client.batch_upsert("app123", "Events", records,
    merge_on=["Name"], progress=True)
```

## Xwander Nordic Calendar

| Key | Value |
|-----|-------|
| Base ID | app5ctfBdvOxmTpOM |
| Events Table | tbl6W7GHp31cVnZ3u |
| Packages Table | tbl2NtM9i85lcqeqE |
| Tracks | Erasmus+, Academy, Day Tours, Holiday Packages, Cap of the North |

## Error Handling

| Error | Exit Code | Action |
|-------|-----------|--------|
| Rate limit (429) | 2 | Auto-retry via rate limiter |
| Auth failed (401) | 3 | Check token |
| Not found (404) | 4 | Verify IDs |
| Validation (422) | 5 | Check types, use typecast=True |
| Batch partial fail | 6 | Report successes + errors |
