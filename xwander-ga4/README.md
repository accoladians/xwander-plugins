# Xwander GA4 Plugin

Google Analytics 4 API wrapper and CLI for Xwander Nordic travel marketing.

## Features

- **Data API Operations**: Run reports with custom dimensions and metrics
- **Admin API Operations**: Create/manage custom dimensions and audiences
- **Pre-built Reports**: Traffic sources, top pages, conversions, daily summaries
- **Multiple Output Formats**: Tables, JSON, text summaries
- **CLI & Python API**: Use from command line or Python code
- **Xwander Defaults**: Pre-configured for Xwander Nordic (property 358203796)

## Quick Start

### Installation

```bash
pip install -e /srv/plugins/xwander-ga4
```

### Setup Credentials

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### CLI Example

```bash
# Get traffic sources for last 30 days
xwander-ga4 traffic-sources --days 30

# Get top pages
xwander-ga4 top-pages

# Get conversions
xwander-ga4 conversions

# Run custom report
xwander-ga4 report --dimensions date source --metrics sessions users --days 7

# Create custom dimension
xwander-ga4 dimension create \
  --display-name "Product Type" \
  --parameter-name product_type \
  --scope EVENT

# List audiences
xwander-ga4 audience list --sort-by-size
```

### Python Example

```python
from xwander_ga4 import GA4DataClient, ReportBuilder, ReportFormatter

# Get traffic data
client = GA4DataClient('358203796')
builder = ReportBuilder(client)
result = builder.traffic_sources(days=30)

# Display as table
formatter = ReportFormatter()
print(formatter.table(result))
```

## Commands

### Reporting
- `report` - Run custom report
- `realtime` - Get realtime active users
- `traffic-sources` - Traffic by source/medium
- `top-pages` - Top pages by sessions
- `conversions` - Conversions by event
- `daily-summary` - Daily metrics

### Dimensions
- `dimension create` - Create custom dimension
- `dimension list` - List custom dimensions

### Audiences
- `audience list` - List audiences
- `audience search` - Search by name

## Documentation

- **Quick Reference**: [docs/QUICK_REFERENCE.json](docs/QUICK_REFERENCE.json)
- **API Documentation**: [docs/API.md](docs/API.md)

## Architecture

```
xwander_ga4/
├── client.py       # GA4 Data/Admin API clients
├── reports.py      # Report builders and formatters
├── dimensions.py   # Custom dimension management
├── audiences.py    # Audience management
├── exceptions.py   # Custom exceptions
└── cli.py          # CLI entry point
```

## API Classes

### GA4DataClient
Low-level Data API wrapper
- `run_report()` - Run report with date ranges
- `run_realtime_report()` - Get realtime metrics

### GA4AdminClient
Low-level Admin API wrapper
- `create_custom_dimension()` - Create dimension
- `list_custom_dimensions()` - List dimensions
- `list_audiences()` - List audiences

### ReportBuilder
High-level report building helper
- `last_n_days()` - Report for N days
- `date_range()` - Report for date range
- `traffic_sources()` - Traffic report
- `top_pages()` - Top pages report
- `conversions()` - Conversions report

### ReportFormatter
Format reports for display
- `table()` - ASCII table
- `json()` - JSON format
- `summary()` - Text summary

### DimensionManager
High-level dimension management
- `create()` - Create dimension
- `list()` - List dimensions
- `by_scope()` - Filter by scope

### AudienceManager
High-level audience management
- `list()` - List audiences
- `filter_by_name()` - Search by name
- `sorted_by_size()` - Sort by member count

## Xwander Configuration

**Property ID**: 358203796 (Xwander Nordic)
**Account ID**: 89715181
**Timezone**: Europe/Helsinki
**Currency**: EUR
**Website**: xwander.com

## Error Handling

```python
from xwander_ga4 import GA4Error, GA4ValidationError

try:
    result = client.run_report(...)
except GA4ValidationError as e:
    print(f"Invalid params: {e}")
except GA4Error as e:
    print(f"Error: {e}")
```

## Requirements

- Python 3.8+
- google-analytics-data >= 0.18.0
- google-analytics-admin >= 0.20.0
- click >= 8.0.0

## Common Dimensions

date, month, year, dayOfWeek, source, medium, campaign, country, region, city, pagePath, pageTitle, eventName, deviceCategory, browser, operatingSystem

## Common Metrics

sessions, users, newUsers, bounceRate, sessionDuration, screenPageViews, eventCount, eventValue, conversions, conversionValue, activeUsers

## License

MIT

## Support

See [Xwander Growth Agent Documentation](https://github.com/accoladians/xwander.com/blob/dev/growth/CLAUDE.md)
