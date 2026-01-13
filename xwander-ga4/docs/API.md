# Xwander GA4 Plugin - API Documentation

Version: 1.1.0 | Updated: 2026-01-13

## Overview

The Xwander GA4 plugin provides a Python wrapper and CLI for Google Analytics 4 Data and Admin APIs. It simplifies running reports, managing custom dimensions, and working with audiences.

**Key Features:**
- Easy report building with predefined templates
- Custom dimension and audience management
- CLI for quick operations
- Format reports as tables, JSON, or summaries
- Built-in Xwander configuration

---

## Installation

```bash
pip install -e /srv/plugins/xwander-ga4
```

**Dependencies:**
- google-analytics-data
- google-analytics-admin
- click

---

## Authentication

### Setup

1. Create a Google Cloud service account with Analytics Admin access
2. Download JSON key file
3. Set environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Verify

```bash
python -c "from xwander_ga4 import GA4DataClient; GA4DataClient('358203796')"
```

---

## CLI Reference

### Core Commands

#### `xwander-ga4 report` - Run a Report

Run a custom GA4 report.

```bash
xwander-ga4 report \
  --dimensions date source \
  --metrics sessions users \
  --days 7 \
  --format table
```

**Options:**
- `--property-id`: GA4 property ID (default: 358203796)
- `--dimensions`: Dimension names (required, multiple)
- `--metrics`: Metric names (required, multiple)
- `--start-date`: Start date YYYY-MM-DD (optional)
- `--end-date`: End date YYYY-MM-DD (optional)
- `--days`: Days back if no date range (default: 7)
- `--limit`: Max rows to return (default: 100)
- `--format`: Output format - table, json, summary (default: table)

**Examples:**

```bash
# Last 7 days by date and source
xwander-ga4 report --dimensions date source --metrics sessions users

# Last 30 days by page path
xwander-ga4 report --dimensions pagePath --metrics sessions --days 30 --limit 50

# Specific date range
xwander-ga4 report \
  --start-date 2026-01-01 \
  --end-date 2026-01-07 \
  --dimensions eventName \
  --metrics eventCount eventValue \
  --format json

# Top 10 countries by users
xwander-ga4 report \
  --dimensions country \
  --metrics users sessions \
  --limit 10
```

---

#### `xwander-ga4 realtime` - Get Realtime Users

View active users in real-time.

```bash
xwander-ga4 realtime

# With dimensions
xwander-ga4 realtime --dimensions country city source
```

**Options:**
- `--property-id`: GA4 property ID (default: 358203796)
- `--dimensions`: Dimension names (optional)
- `--metrics`: Metric names (optional)

---

#### `xwander-ga4 traffic-sources` - Traffic by Source/Medium

Get traffic breakdown by source and medium.

```bash
xwander-ga4 traffic-sources --days 30 --limit 50
```

**Options:**
- `--property-id`: GA4 property ID (default: 358203796)
- `--days`: Number of days (default: 30)
- `--limit`: Max rows (default: 50)

---

#### `xwander-ga4 top-pages` - Top Pages

Get top pages by sessions.

```bash
xwander-ga4 top-pages --days 30
```

**Options:**
- `--property-id`: GA4 property ID
- `--days`: Number of days (default: 30)
- `--limit`: Max rows (default: 50)

---

#### `xwander-ga4 conversions` - Conversions by Event

Get conversions grouped by event.

```bash
xwander-ga4 conversions --days 30
```

**Options:**
- `--property-id`: GA4 property ID
- `--days`: Number of days (default: 30)
- `--limit`: Max rows (default: 100)

---

#### `xwander-ga4 daily-summary` - Daily Summary

Get daily metrics summary.

```bash
xwander-ga4 daily-summary --days 30
```

**Options:**
- `--property-id`: GA4 property ID
- `--days`: Number of days (default: 30)

---

### Dimension Commands

#### `xwander-ga4 dimension create` - Create Custom Dimension

Create a new custom dimension.

```bash
xwander-ga4 dimension create \
  --display-name "Product Type" \
  --parameter-name product_type \
  --scope EVENT \
  --description "Day tours vs multi-day packages"
```

**Options:**
- `--property-id`: GA4 property ID
- `--display-name`: User-friendly name (required)
- `--parameter-name`: Event parameter name (required)
- `--scope`: EVENT, USER, or ITEM (default: EVENT)
- `--description`: Optional description

**Parameter Name Rules:**
- 1-40 characters
- Alphanumeric and underscore only
- Cannot start with digit

---

#### `xwander-ga4 dimension list` - List Custom Dimensions

List all custom dimensions.

```bash
xwander-ga4 dimension list

# Filter by scope
xwander-ga4 dimension list --scope EVENT
xwander-ga4 dimension list --scope USER
```

**Options:**
- `--property-id`: GA4 property ID
- `--scope`: Filter by EVENT, USER, or ITEM

---

### Audience Commands

#### `xwander-ga4 audience list` - List Audiences

List all audiences.

```bash
xwander-ga4 audience list

# Sort by size (largest first)
xwander-ga4 audience list --sort-by-size
```

**Options:**
- `--property-id`: GA4 property ID
- `--sort-by-size`: Sort by member count

---

#### `xwander-ga4 audience search` - Search Audiences

Search audiences by name pattern.

```bash
xwander-ga4 audience search "Northern Lights"
xwander-ga4 audience search paid_search
```

---

## Python API Reference

### GA4DataClient

Low-level Data API client.

```python
from xwander_ga4 import GA4DataClient

client = GA4DataClient('358203796')
```

#### Methods

##### `run_report()`

Run a report.

```python
result = client.run_report(
    date_ranges=[
        {
            'start_date': '2026-01-01',
            'end_date': '2026-01-07'
        }
    ],
    dimensions=['date', 'source'],
    metrics=['sessions', 'users'],
    limit=100,
    offset=0
)

print(result['rows'])
print(result['row_count'])
print(result['property_quota'])
```

**Parameters:**
- `date_ranges`: List of {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"} (required)
- `dimensions`: List of dimension names (required)
- `metrics`: List of metric names (required)
- `limit`: Max rows (default: 10)
- `offset`: Row offset (default: 0)
- `order_bys`: Optional sort order

**Returns:**
```python
{
    'rows': [
        {'date': '2026-01-01', 'source': 'google', 'sessions': '1234'},
        ...
    ],
    'row_count': 1234,
    'property_quota': {
        'tokens_per_day': 1000000,
        'tokens_used': 50000,
        'tokens_remaining': 950000,
        ...
    }
}
```

---

##### `run_realtime_report()`

Run a realtime report.

```python
result = client.run_realtime_report(
    dimensions=['country', 'city'],
    metrics=['activeUsers'],
    limit=20
)

print(result['rows'])
print(result['total_users'])
```

**Parameters:**
- `dimensions`: List of dimension names (required)
- `metrics`: List of metric names (required)
- `limit`: Max rows (default: 10)

**Returns:**
```python
{
    'rows': [
        {'country': 'Finland', 'city': 'Helsinki', 'activeUsers': '42'},
        ...
    ],
    'total_users': 150
}
```

---

### ReportBuilder

High-level report building helper.

```python
from xwander_ga4 import GA4DataClient, ReportBuilder

client = GA4DataClient('358203796')
builder = ReportBuilder(client)
```

#### Methods

##### `last_n_days()`

Get report for last N days.

```python
result = builder.last_n_days(
    days=30,
    dimensions=['date'],
    metrics=['sessions', 'users'],
    limit=100
)
```

**Parameters:**
- `days`: Number of days (1-730) (required)
- `dimensions`: Dimension names (required)
- `metrics`: Metric names (required)
- `limit`: Max rows (default: 100)
- `order_bys`: Optional sort order

---

##### `date_range()`

Get report for specific date range.

```python
result = builder.date_range(
    start_date='2026-01-01',
    end_date='2026-01-07',
    dimensions=['date'],
    metrics=['sessions'],
    limit=100
)
```

---

##### `traffic_sources()`

Get traffic by source/medium.

```python
result = builder.traffic_sources(days=30, limit=50)
# Returns dimensions: source, medium
# Returns metrics: sessions, users, bounceRate
```

---

##### `top_pages()`

Get top pages by sessions.

```python
result = builder.top_pages(days=30, limit=50)
# Returns dimension: pagePath
# Returns metrics: sessions, users, avgSessionDuration
```

---

##### `conversions()`

Get conversions by event.

```python
result = builder.conversions(days=30, limit=100)
# Returns dimension: eventName
# Returns metrics: eventCount, eventValue
```

---

##### `daily_summary()`

Get daily summary.

```python
result = builder.daily_summary(days=30)
# Returns dimension: date
# Returns metrics: sessions, users, eventCount
```

---

##### `realtime_summary()`

Get realtime active users.

```python
result = builder.realtime_summary()
# Returns dimension: country
# Returns metric: activeUsers
```

---

### ReportFormatter

Format reports for display.

```python
from xwander_ga4 import ReportFormatter

formatter = ReportFormatter()
```

#### Methods

##### `table()`

Format as ASCII table.

```python
output = formatter.table(result)
# Optional: filter columns
output = formatter.table(result, columns=['date', 'sessions'])
print(output)
```

---

##### `json()`

Format as JSON.

```python
output = formatter.json(result)
print(output)
```

---

##### `summary()`

Format as text summary.

```python
output = formatter.summary(result)
print(output)
```

---

### GA4AdminClient

Admin API client for property settings.

```python
from xwander_ga4 import GA4AdminClient

admin = GA4AdminClient('358203796')
```

#### Methods

##### `get_property()`

Get property details.

```python
info = admin.get_property()
print(info['timezone'])
print(info['currency_code'])
```

---

##### `create_custom_dimension()`

Create custom dimension.

```python
result = admin.create_custom_dimension(
    display_name='Product Type',
    parameter_name='product_type',
    scope='EVENT',
    description='Day tours vs multi-day packages'
)
print(result['api_name'])
```

---

##### `list_custom_dimensions()`

List custom dimensions.

```python
dimensions = admin.list_custom_dimensions()
for dim in dimensions:
    print(f"{dim['display_name']} ({dim['api_name']})")
```

---

##### `list_audiences()`

List audiences.

```python
audiences = admin.list_audiences()
for aud in audiences:
    print(f"{aud['name']}: {aud['member_count']:,} members")
```

---

### DimensionManager

High-level dimension management.

```python
from xwander_ga4 import GA4AdminClient, DimensionManager

admin = GA4AdminClient('358203796')
manager = DimensionManager(admin)
```

#### Methods

##### `create()`

Create custom dimension.

```python
result = manager.create(
    display_name='Product Type',
    parameter_name='product_type',
    scope='EVENT'
)
```

---

##### `list()`

List all dimensions.

```python
dimensions = manager.list()
```

---

##### `by_scope()`

Get dimensions by scope.

```python
event_dims = manager.by_scope('EVENT')
user_dims = manager.by_scope('USER')
```

---

##### `get_by_name()`

Get dimension by parameter name.

```python
dim = manager.get_by_name('product_type')
```

---

### AudienceManager

High-level audience management.

```python
from xwander_ga4 import GA4AdminClient, AudienceManager

admin = GA4AdminClient('358203796')
manager = AudienceManager(admin)
```

#### Methods

##### `list()`

List all audiences.

```python
audiences = manager.list()
```

---

##### `filter_by_name()`

Search audiences by name pattern.

```python
results = manager.filter_by_name('Northern Lights')
```

---

##### `get_by_name()`

Get audience by exact name.

```python
audience = manager.get_by_name('Paid Search Visitors')
```

---

##### `sorted_by_size()`

List audiences sorted by member count.

```python
audiences = manager.sorted_by_size()  # Largest first
```

---

## Common Dimensions

| Dimension | Type | Example |
|-----------|------|---------|
| date | Time | 2026-01-10 |
| month | Time | 202601 |
| year | Time | 2026 |
| dayOfWeek | Time | Monday |
| source | Traffic | google, facebook |
| medium | Traffic | organic, paid |
| campaign | Traffic | winter_campaign |
| country | Geography | Finland |
| region | Geography | Uusimaa |
| city | Geography | Helsinki |
| pagePath | Page | /plan-your-holiday/ |
| pageTitle | Page | Plan Your Holiday |
| eventName | Event | purchase, lead_form |
| deviceCategory | Device | mobile, desktop |
| browser | Device | Chrome, Firefox |
| operatingSystem | Device | Windows, macOS |

---

## Common Metrics

| Metric | Type | Description |
|--------|------|-------------|
| sessions | Engagement | Number of sessions |
| users | Engagement | Number of users |
| newUsers | Engagement | New users |
| bounceRate | Engagement | % of bounces (0-100) |
| sessionDuration | Engagement | Avg session duration (seconds) |
| screenPageViews | Engagement | Total page views |
| eventCount | Event | Total events |
| eventValue | Event | Total event value |
| conversions | Conversion | Total conversions |
| conversionValue | Conversion | Total conversion value |
| activeUsers | Realtime | Currently active users |

---

## Error Handling

```python
from xwander_ga4 import GA4DataClient, GA4Error, GA4ValidationError

try:
    client = GA4DataClient('358203796')
    result = client.run_report(...)
except GA4ValidationError as e:
    print(f"Invalid parameters: {e}")
except GA4Error as e:
    print(f"GA4 error: {e}")
```

### Exception Types

- **GA4Error**: Base exception
- **GA4ConfigError**: Missing credentials or invalid configuration
- **GA4APIError**: GA4 API returned an error
- **GA4ValidationError**: Invalid request parameters
- **GA4AuthError**: Authentication/authorization failed

---

## Examples

### Example 1: Traffic Report

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

### Example 2: Create Dimension and Use It

```python
from xwander_ga4 import GA4AdminClient, GA4DataClient, DimensionManager, ReportBuilder

# Create custom dimension
admin = GA4AdminClient('358203796')
manager = DimensionManager(admin)
manager.create(
    display_name='Product Type',
    parameter_name='product_type',
    scope='EVENT'
)

# Use it in a report (after events are being tracked with the dimension)
data_client = GA4DataClient('358203796')
builder = ReportBuilder(data_client)
result = builder.last_n_days(
    days=30,
    dimensions=['date', 'customEvent:product_type'],  # Use api_name format
    metrics=['eventCount']
)
```

### Example 3: Audience Analysis

```python
from xwander_ga4 import GA4AdminClient, AudienceManager

admin = GA4AdminClient('358203796')
manager = AudienceManager(admin)

# Find largest audiences
audiences = manager.sorted_by_size()
for aud in audiences[:10]:
    print(f"{aud['name']}: {aud['member_count']:,}")

# Search for specific audiences
paid_search = manager.filter_by_name('paid search')
print(f"Found {len(paid_search)} paid search audiences")
```

---

## Troubleshooting

### "Failed to initialize GA4 Data API"

**Cause:** Missing or invalid credentials

**Solution:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
python -c "from xwander_ga4 import GA4DataClient; print('OK')"
```

### "Property not found"

**Cause:** Invalid property ID or no access

**Solution:**
- Verify property ID: Check GA4 property settings
- Check access: Service account must be added as Admin to the property

### "Custom dimension failed"

**Cause:** Dimension already exists or invalid parameters

**Solution:**
- Check parameter_name is alphanumeric + underscore
- Use `xwander-ga4 dimension list` to see existing dimensions

---

## API Quotas

GA4 has rate limits:
- **Tokens per day**: 1,000,000
- **Tokens per hour**: 100,000
- **Concurrent requests**: 10

Monitor quota usage in report results:
```python
result = client.run_report(...)
quota = result['property_quota']
print(f"Used: {quota['tokens_used']} / Remaining: {quota['tokens_remaining']}")
```

---

## References

- [GA4 Data API Docs](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [GA4 Admin API Docs](https://developers.google.com/analytics/devguides/config/admin/v1)
- [Xwander GA4 Config](/srv/xwander-platform/xwander.com/growth/knowledge/ga4.json)

