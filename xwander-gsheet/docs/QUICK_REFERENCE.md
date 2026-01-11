# gsheet.py v2.0 - Quick Reference

**AI agents**: Use this for rapid task completion. All examples copy-paste ready.

---

## Create New Sheet

```python
from gsheet import GSheet

sheet = GSheet.create_new("Order 2026-01-05")
```

---

## Build Complete Order

```python
# Title
sheet.set_title("SUPPLIER ORDER")

# Summary (6-8 rows typical)
sheet.add_summary_row("Total Investment", 1791.22, format='currency')
sheet.add_summary_row("Expected Revenue (12m)", 5169.25, format='currency')
sheet.add_summary_row("Margin %", 42.5, format='percentage')
sheet.add_summary_row("Total SKUs", 23)

# Header
sheet.set_header(['Priority', 'SKU', 'Product', 'Color', 'Qty', 'Cost', 'Price', 'Margin %'])

# Data (loop through products)
for product in products:
    sheet.add_data_row({
        'priority': product['priority'],
        'sku': product['sku'],
        'product': product['name'],
        'color': product['color'],
        'qty': product['qty'],
        'cost': product['cost'],
        'price': product['price'],
        'margin_pct': product['margin']
    })

# Footer
sheet.add_footer_line("")
sheet.add_footer_line("CRITICAL ACTIONS REQUIRED")
sheet.add_footer_line("1. Price corrections needed")

# Sync
stats = sheet.sync()
print(f"✅ {sheet.get_url()}")

# Save state
sheet.save('order_state.json')
```

---

## Update Rows

```python
# Update one product by SKU
sheet.update_data_row(
    match={'sku': '2105'},
    updates={'priority': 'P1', 'qty': 20}
)

# Update all P0 products
sheet.update_data_row(
    match={'priority': 'P0'},
    updates={'priority': 'P1'}
)

# Re-sync
sheet.sync()
```

---

## Find Rows

```python
# Find all P0 products
p0_products = sheet.find_data_rows({'priority': 'P0'})
for p in p0_products:
    print(f"{p['product']} - {p['qty']} units")

# Find specific product
results = sheet.find_data_rows({'sku': '2105', 'color': 'Kelo'})
```

---

## Load Existing State

```python
# Load from JSON
sheet = GSheet.load('order_state.json')

# Modify
sheet.add_data_row({'priority': 'P2', 'product': 'New Item', 'qty': 5})

# Sync changes
sheet.sync()
```

---

## Format Types

```python
# Currency (displays as €X,XXX.XX)
sheet.add_summary_row("Total", 1791.22, format='currency')

# Percentage (displays as XX.X%)
sheet.add_summary_row("Margin", 42.5, format='percentage')

# Number (displays as X,XXX.XX)
sheet.add_summary_row("Units", 200, format='number')

# No format (plain text)
sheet.add_summary_row("Supplier", "Nordic Trail")
```

---

## Get Information

```python
# URL
url = sheet.get_url()

# Statistics
stats = sheet.get_stats()
# {'sections': 4, 'total_rows': 25, 'data_rows': 20, ...}

# Find how many P0 products
p0_count = len(sheet.find_data_rows({'priority': 'P0'}))
```

---

## Common Patterns

### Pattern: Build from Enhanced JSON

```python
import json
from gsheet import GSheet

# Load enhanced JSON
with open('SUPPLIER_ENHANCED_FOR_GSHEET.json') as f:
    data = json.load(f)

# Create sheet
sheet = GSheet.create_new(f"{data['_meta']['supplier']} Order {data['_meta']['date']}")

# Title
sheet.set_title(f"{data['_meta']['supplier'].upper()} ORDER - {data['order_summary']['scenario']}")

# Summary
for key, value in data['order_summary'].items():
    if key == 'scenario':
        continue
    format_type = 'currency' if 'investment' in key or 'revenue' in key else None
    sheet.add_summary_row(key.replace('_', ' ').title(), value, format=format_type)

# Header (from first product keys)
if data['products']:
    columns = list(data['products'][0].keys())
    sheet.set_header(columns)

# Data
for product in data['products']:
    sheet.add_data_row(product)

# Footer
sheet.add_footer_line("")
sheet.add_footer_line("CRITICAL ACTIONS REQUIRED")
for action in data.get('critical_actions', []):
    sheet.add_footer_line(f"• {action}")

# Sync
sheet.sync()
sheet.save(f"order_state_{data['_meta']['date']}.json")
```

### Pattern: Update Priorities

```python
# Change all P0 gloves to P1
sheet.update_data_row(
    match={'priority': 'P0', 'category': 'gloves'},
    updates={'priority': 'P1'}
)

# Find and update specific product
sheet.update_data_row(
    match={'product': 'Guide Gloves', 'color': 'Black'},
    updates={'qty': 20, 'note': 'Increased order'}
)
```

### Pattern: Calculate Totals

```python
# Get all data rows
all_products = sheet.find_data_rows({})

# Calculate totals
total_investment = sum(p.get('total_cost', 0) for p in all_products)
total_units = sum(p.get('qty', 0) for p in all_products)

# Update summary
# (Note: In v1.0, recreate summary section or use load/modify/save pattern)
```

---

## Error Handling

```python
try:
    sheet = GSheet.create_new("My Order")
    sheet.set_title("ORDER")
    sheet.sync()
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Authentication

**Default service account** (automatic):
```python
from gsheet import GSheetAuth

client = GSheetAuth.get_default_client()
# Uses: /srv/xwander-platform/projects/alone/service_account.json
```

**Custom service account**:
```python
client = GSheetAuth.from_service_account('/path/to/service_account.json')
```

---

## Section Order

Sections auto-order as:
1. **title** - Merged cell header
2. **summary** - Key-value pairs
3. **header** - Column names (frozen)
4. **data** - Product rows
5. **footer** - Notes and actions

You can add sections in any order - they'll be sorted automatically.

---

## Tips for AI Agents

1. **Always save state**: `sheet.save('state.json')` enables resume/modify later
2. **Match criteria is powerful**: Update multiple rows with one call
3. **Use format types**: 'currency', 'percentage', 'number' for auto-formatting
4. **Header freezes by default**: Users can scroll data while seeing headers
5. **Find returns actual row data**: Not indices, so you can read values directly

---

## File Locations

**Implementation**: `/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/lib/gsheet.py`

**Tests**: `/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/tests/test_gsheet.py`

**Example**: `/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/examples/gsheet_example.py`

**Service Account**: `/srv/xwander-platform/projects/alone/service_account.json`

**Shared Drive ID**: `0AOx6w8RvMATMUk9PVA` (AI Automation)

---

## Full Example (Copy-Paste Ready)

```python
#!/usr/bin/env python3
from gsheet import GSheet

# Create
sheet = GSheet.create_new("Kupilka Order 2026-01-05")

# Build
sheet.set_title("KUPILKA ORDER - Scenario B")
sheet.add_summary_row("Total Investment", 1791.22, format='currency')
sheet.add_summary_row("Margin %", 42.5, format='percentage')
sheet.set_header(['Priority', 'Product', 'Qty', 'Cost', 'Price'])
sheet.add_data_row({'priority': 'P0', 'product': 'Kupilka 21', 'qty': 15, 'cost': 8.30, 'price': 17.50})
sheet.add_data_row({'priority': 'P1', 'product': 'SUOVA 20', 'qty': 3, 'cost': 9.03, 'price': 15.90})
sheet.add_footer_line("CRITICAL ACTIONS REQUIRED")
sheet.add_footer_line("1. Price optimization needed")

# Sync
stats = sheet.sync()
print(f"✅ Success! {sheet.get_url()}")
print(f"   Synced {stats['rows_updated']} rows")

# Save
sheet.save('kupilka_order_state.json')
```

**Runtime**: ~5 seconds for small orders

---

**Version**: 2.0.0 (Week 1 - Core)
**Updated**: 2026-01-05
