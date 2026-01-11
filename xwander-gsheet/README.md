# xwander-gsheet

AI-first Google Sheets management with section-based abstraction.

## Features

- **Section-based API** - No cell coordinates, just logical sections
- **Local-first** - JSON state with sync to Google Sheets
- **AI-friendly** - Query and update by criteria, not cell ranges
- **Automatic formatting** - Currency, percentage, frozen headers

## Installation

```bash
# Development mode (editable)
cd /srv/plugins/xwander-gsheet
pip install -e .

# Or from source
pip install .
```

## Quick Start

```python
from xwander_gsheet import GSheet

# Create new spreadsheet
sheet = GSheet.create_new("My Order")
sheet.set_title("PURCHASE ORDER")
sheet.add_summary_row("Total Investment", 1791.22, format='currency')
sheet.set_header(['Priority', 'Product', 'Qty', 'Price'])
sheet.add_data_row({'priority': 'P0', 'product': 'Widget', 'qty': 10, 'price': 15.50})
sheet.sync()

print(f"Created: {sheet.get_url()}")
```

## Documentation

- **Quick Reference**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)
- **API Reference**: [docs/API.md](docs/API.md)
- **Examples**: [examples/](examples/)
- **Skills**: [skills/gsheet-ops.md](skills/gsheet-ops.md)

## Testing

```bash
pytest tests/ -v
```

## Claude Code Plugin

This is a native Claude Code plugin providing:
- **Skill**: `gsheet-ops` for Google Sheets operations
- **Agent**: `gsheet-agent` (Sonnet specialist)
- **Tools**: Bash, Read, Write, Edit

## License

MIT
