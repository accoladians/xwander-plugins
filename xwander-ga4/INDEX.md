# Xwander GA4 Plugin - Complete Index

**Version**: 1.0.0 | **Built**: 2026-01-10 | **Status**: Production Ready

## Table of Contents

1. [Core Files](#core-files)
2. [API Reference](#api-reference)
3. [CLI Commands](#cli-commands)
4. [Quick Examples](#quick-examples)
5. [Installation](#installation)
6. [File Manifest](#file-manifest)

---

## Core Files

### Python Modules

- **`xwander_ga4/__init__.py`** - Package initialization and exports
  - Exports all public classes and exceptions
  - Version: 1.0.0

- **`xwander_ga4/client.py`** (385 lines)
  - `GA4DataClient` - Low-level Data API wrapper
    - `run_report()` - Execute GA4 reports
    - `run_realtime_report()` - Get realtime metrics
  - `GA4AdminClient` - Low-level Admin API wrapper
    - `get_property()` - Retrieve property details
    - `create_custom_dimension()` - Create dimensions
    - `list_custom_dimensions()` - List all dimensions
    - `list_audiences()` - List all audiences

- **`xwander_ga4/reports.py`** (240 lines)
  - `ReportBuilder` - High-level report template builder
    - `last_n_days()` - Report for N days
    - `date_range()` - Report for specific date range
    - `traffic_sources()` - Traffic by source/medium
    - `top_pages()` - Top pages by sessions
    - `conversions()` - Conversions by event
    - `daily_summary()` - Daily metrics summary
    - `realtime_summary()` - Realtime active users
  - `ReportFormatter` - Format reports for display
    - `table()` - ASCII table format
    - `json()` - JSON format
    - `summary()` - Text summary format

- **`xwander_ga4/dimensions.py`** (65 lines)
  - `DimensionManager` - Custom dimension operations
    - `create()` - Create dimension
    - `list()` - List all dimensions
    - `by_scope()` - Filter by scope (EVENT/USER/ITEM)
    - `get_by_name()` - Lookup by parameter name
    - Validation methods for parameter and display names

- **`xwander_ga4/audiences.py`** (40 lines)
  - `AudienceManager` - Audience operations
    - `list()` - List all audiences
    - `filter_by_name()` - Search by name pattern
    - `get_by_name()` - Lookup by exact name
    - `sorted_by_size()` - Sort by member count

- **`xwander_ga4/exceptions.py`** (25 lines)
  - Exception hierarchy:
    - `GA4Error` - Base exception
    - `GA4ConfigError` - Configuration issues
    - `GA4APIError` - API errors
    - `GA4ValidationError` - Invalid parameters
    - `GA4AuthError` - Authentication issues

- **`xwander_ga4/cli.py`** (450 lines)
  - Click-based CLI interface
  - Command groups: `report`, `realtime`, `traffic-sources`, `top-pages`, `conversions`, `daily-summary`, `dimension`, `audience`
  - All Xwander defaults pre-configured (property 358203796)

---

## API Reference

### Quick Links

- **Full API Documentation**: [`docs/API.md`](docs/API.md)
- **Quick Reference Guide**: [`docs/QUICK_REFERENCE.json`](docs/QUICK_REFERENCE.json)
- **Agent Skills**: [`skills/ga4-ops.md`](skills/ga4-ops.md)

### Core Classes

```python
from xwander_ga4 import (
    GA4DataClient,           # Low-level Data API
    GA4AdminClient,          # Low-level Admin API
    ReportBuilder,           # High-level reports
    ReportFormatter,         # Format output
    DimensionManager,        # Manage dimensions
    AudienceManager,         # Manage audiences
    GA4Error,                # Error types
)
```

### Usage Pattern

```python
# 1. Create client
client = GA4DataClient('358203796')

# 2. Use builder for convenience
builder = ReportBuilder(client)
result = builder.traffic_sources(days=30)

# 3. Format output
formatter = ReportFormatter()
print(formatter.table(result))
```

---

## CLI Commands

### Reporting Commands

**`xwander-ga4 report`** - Run custom report
```bash
xwander-ga4 report \
  --dimensions date source \
  --metrics sessions users \
  --days 30 \
  --format table
```

**`xwander-ga4 realtime`** - Realtime report
```bash
xwander-ga4 realtime --dimensions country city
```

**`xwander-ga4 traffic-sources`** - Traffic by source
```bash
xwander-ga4 traffic-sources --days 30 --limit 50
```

**`xwander-ga4 top-pages`** - Top pages
```bash
xwander-ga4 top-pages --days 30
```

**`xwander-ga4 conversions`** - Conversions
```bash
xwander-ga4 conversions --days 30
```

**`xwander-ga4 daily-summary`** - Daily summary
```bash
xwander-ga4 daily-summary --days 30
```

### Dimension Commands

**`xwander-ga4 dimension create`** - Create dimension
```bash
xwander-ga4 dimension create \
  --display-name "Product Type" \
  --parameter-name product_type \
  --scope EVENT
```

**`xwander-ga4 dimension list`** - List dimensions
```bash
xwander-ga4 dimension list [--scope EVENT|USER|ITEM]
```

### Audience Commands

**`xwander-ga4 audience list`** - List audiences
```bash
xwander-ga4 audience list [--sort-by-size]
```

**`xwander-ga4 audience search`** - Search audiences
```bash
xwander-ga4 audience search "Northern Lights"
```

---

## Quick Examples

### Get Traffic Report

```python
from xwander_ga4 import GA4DataClient, ReportBuilder, ReportFormatter

client = GA4DataClient('358203796')
builder = ReportBuilder(client)
result = builder.traffic_sources(days=30)

formatter = ReportFormatter()
print(formatter.table(result))
```

### Create Custom Dimension

```python
from xwander_ga4 import GA4AdminClient, DimensionManager

admin = GA4AdminClient('358203796')
manager = DimensionManager(admin)

result = manager.create(
    display_name='Product Type',
    parameter_name='product_type',
    scope='EVENT'
)
print(f"Created: {result['api_name']}")
```

### Run Custom Report

```python
client = GA4DataClient('358203796')
result = client.run_report(
    date_ranges=[{
        'start_date': '2026-01-01',
        'end_date': '2026-01-07'
    }],
    dimensions=['date', 'source'],
    metrics=['sessions', 'users'],
    limit=100
)

for row in result['rows']:
    print(row)
```

### List Audiences by Size

```python
from xwander_ga4 import GA4AdminClient, AudienceManager

admin = GA4AdminClient('358203796')
manager = AudienceManager(admin)

audiences = manager.sorted_by_size()
for aud in audiences[:10]:
    print(f"{aud['name']}: {aud['member_count']:,} members")
```

---

## Installation

### Requirements

- Python 3.8+
- google-analytics-data >= 0.18.0
- google-analytics-admin >= 0.20.0
- click >= 8.0.0

### Steps

```bash
# 1. Install
pip install -e /srv/plugins/xwander-ga4

# 2. Setup credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# 3. Test
xwander-ga4 realtime

# 4. Use
xwander-ga4 traffic-sources --days 30
```

---

## File Manifest

### Plugin Structure

```
/srv/plugins/xwander-ga4/
│
├── xwander_ga4/                    # Main package
│   ├── __init__.py                 # Exports
│   ├── client.py                   # API clients (385 lines)
│   ├── reports.py                  # Report builders (240 lines)
│   ├── dimensions.py               # Dimension manager (65 lines)
│   ├── audiences.py                # Audience manager (40 lines)
│   ├── exceptions.py               # Custom exceptions (25 lines)
│   └── cli.py                      # CLI interface (450 lines)
│
├── docs/                           # Documentation
│   ├── API.md                      # Full API documentation (900+ lines)
│   └── QUICK_REFERENCE.json        # Quick reference guide
│
├── tests/                          # Test suite
│   └── test_ga4.py                 # Unit tests (230+ lines)
│
├── skills/                         # Agent skills
│   └── ga4-ops.md                  # Quick operations guide
│
├── .claude-plugin/                 # Plugin metadata
│   └── plugin.json                 # Configuration
│
├── README.md                       # Project overview
├── setup.py                        # Installation config
├── INDEX.md                        # This file
└── BUILD_SUMMARY.md                # Build details

Total: 15 files | 3,000+ lines
```

### Key Documentation Files

- **`docs/API.md`** - Complete API reference with 15+ examples
- **`docs/QUICK_REFERENCE.json`** - CLI commands, Python API, constants
- **`skills/ga4-ops.md`** - Quick templates for common operations
- **`README.md`** - Feature overview and quick start
- **`BUILD_SUMMARY.md`** - Build details and architecture decisions
- **`INDEX.md`** (this file) - Complete index and navigation

---

## Features at a Glance

### Data Operations
- Run reports with custom dimensions/metrics
- Realtime active users
- Automatic response formatting
- Quota tracking

### Admin Operations
- Create custom dimensions
- List custom dimensions
- List audiences
- Property management

### Output Formats
- ASCII table
- JSON
- Text summary

### Pre-built Reports
- Traffic by source/medium
- Top pages
- Conversions by event
- Daily metrics
- Realtime active users

### Command-line
- 13 CLI commands
- Sensible defaults (Xwander property)
- Multiple output formats
- Full help text

---

## Xwander Configuration

**Default Settings:**
- Property ID: 358203796 (Xwander Nordic)
- Account ID: 89715181
- Timezone: Europe/Helsinki
- Currency: EUR
- Website: xwander.com

All CLI commands use these defaults automatically.

---

## Getting Help

### Quick Start
- See `README.md`

### API Reference
- See `docs/API.md`

### Quick Examples
- See `docs/QUICK_REFERENCE.json`

### Agent Skills
- See `skills/ga4-ops.md`

### CLI Help
```bash
xwander-ga4 --help
xwander-ga4 report --help
xwander-ga4 dimension --help
xwander-ga4 audience --help
```

---

## Support Resources

- **GA4 Data API Docs**: https://developers.google.com/analytics/devguides/reporting/data/v1
- **GA4 Admin API Docs**: https://developers.google.com/analytics/devguides/config/admin/v1
- **Xwander GA4 Config**: `/srv/xwander-platform/xwander.com/growth/knowledge/ga4.json`

---

**Last Updated**: 2026-01-10 | **Version**: 1.0.0 | **Status**: Production Ready
