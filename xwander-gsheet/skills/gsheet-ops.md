---
name: gsheet-ops
description: AI-first Google Sheets management with section-based abstraction. Eliminates hardcoded cell ranges.
allowed-tools: Bash, Read, Write, Edit
triggers:
  - "google sheet"
  - "spreadsheet"
  - "purchase order sheet"
  - "create sheet"
  - "update sheet"
  - "sync to gsheet"
---

# GSheet Operations Skill

## Overview

Use gsheet.py v2.0 for all Google Sheets operations. This library provides:
- **Section-based abstraction** (title, summary, header, data, footer)
- **Local-first JSON state** with sync to Google Sheets
- **AI-friendly operations** (find/update by criteria, no cell coordinates)
- **Automatic formatting** (currency, percentage, frozen headers)

## Library Location

```python
# Import from erasoppi purchasing lib
import sys
sys.path.insert(0, '/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/lib')
from gsheet import GSheet, GSheetAuth
```

## Core API

### Create New Spreadsheet

```python
from gsheet import GSheet

# Creates in AI Automation shared drive
sheet = GSheet.create_new("Kupilka Order 2026-01-05")
sheet.set_title("KUPILKA PURCHASE ORDER")
sheet.add_summary_row("Total Investment", 1791.22, format='currency')
sheet.add_summary_row("Expected Revenue", 5169.25, format='currency')
sheet.add_summary_row("Margin %", 42.5, format='percentage')
sheet.set_header(['Priority', 'SKU', 'Product', 'Qty', 'Cost', 'Total'])
sheet.add_data_row({'priority': 'P0', 'sku': 'KP21', 'product': 'Kupilka 21', 'qty': 15, 'cost': 8.30, 'total': 124.50})
sheet.sync()
print(f"Sheet URL: {sheet.get_url()}")
```

### Load and Update Existing Sheet

```python
# Load from JSON state
sheet = GSheet.load('order_state.json')

# Update specific row by criteria (no cell coordinates!)
sheet.update_data_row(
    match={'product': 'Kupilka 21'},
    updates={'priority': 'P1', 'qty': 20}
)

# Sync changes to Google Sheets
sheet.sync()
sheet.save('order_state.json')
```

### Query Data

```python
# Find all P0 products
p0_products = sheet.find_data_rows({'priority': 'P0'})
print(f"Found {len(p0_products)} P0 products")

# Get stats
stats = sheet.get_stats()
print(f"Total rows: {stats['total_rows']}, Data rows: {stats['data_rows']}")
```

## Section Types

| Section | Purpose | Methods |
|---------|---------|---------|
| title | Sheet title (merged, centered) | `set_title(text)` |
| summary | Key-value pairs | `add_summary_row(key, value, format)` |
| header | Column headers (frozen) | `set_header(columns, freeze=True)` |
| data | Main data table | `add_data_row(dict)`, `update_data_row()`, `find_data_rows()` |
| footer | Notes, actions | `add_footer_line(text)` |

## Format Types

- `currency` - €#,##0.00
- `percentage` - 0.0%
- `number` - Standard number

## Best Practices

1. **Always use sections** - Never hardcode cell ranges
2. **Save JSON state** - Enables resumable operations
3. **Update by criteria** - `match={'sku': 'X'}` not `A15`
4. **Sync once** - Build complete sheet, then single sync()
5. **Use shared drive** - Default: AI Automation (0AOx6w8RvMATMUk9PVA)

## When to Use

- Creating purchase order spreadsheets
- Building analysis reports in Google Sheets
- Updating existing sheets by product/SKU/priority
- Any task requiring Google Sheets with structured data

## When NOT to Use

- Simple one-time cell updates (use gspread directly)
- Reading existing sheets without modification
- Non-tabular data

## Error Handling

```python
try:
    sheet.sync()
except Exception as e:
    print(f"Sync failed: {e}")
    # State is still valid in JSON, can retry
    sheet.save('backup_state.json')
```

## Reference

- **Library**: `/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/lib/gsheet.py`
- **Spec**: `/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/specs/GSHEET_V2_RELEASE_PLAN.md`
- **Examples**: `/srv/plugins/xwander-gsheet/examples/`
