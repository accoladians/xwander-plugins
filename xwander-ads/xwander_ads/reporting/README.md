# Reporting Module

GAQL query builder and reporting functionality for Google Ads.

## Overview

The reporting module provides:
- **GAQL Builder**: Fluent API for building Google Ads Query Language queries
- **Query Templates**: Pre-built queries for common reports
- **Query Execution**: Execute queries and process results
- **Export**: Export to CSV, JSON, Markdown, BigQuery

## Quick Start

### Using Pre-built Templates

```python
from xwander_ads.reporting import templates, execute_query
from xwander_ads.auth import get_client

client = get_client()
customer_id = "2425288235"

# Campaign performance report (last 7 days)
query = templates.campaign_performance(days=7, limit=50)
results = execute_query(client, customer_id, query)

# Conversion performance
query = templates.conversion_performance(days=30)
results = execute_query(client, customer_id, query)

# Search terms report
query = templates.search_terms(days=14, campaign_id="123456")
results = execute_query(client, customer_id, query)
```

### Building Custom Queries

```python
from xwander_ads.reporting import GAQLBuilder

query = (
    GAQLBuilder()
    .select('campaign.name', 'metrics.clicks', 'metrics.cost_micros')
    .from_resource('campaign')
    .where('campaign.status = ENABLED')
    .during('LAST_30_DAYS')
    .order_by('metrics.cost_micros', desc=True)
    .limit(50)
    .build()
)

results = execute_query(client, customer_id, query)
```

### Exporting Results

```python
from xwander_ads.reporting import export_results

# Export to CSV
export_results(results, '/tmp/report.csv', format='csv')

# Export to JSON
export_results(results, '/tmp/report.json', format='json')

# Export to Markdown
export_results(results, '/tmp/report.md', format='markdown')

# Export to string
from xwander_ads.reporting import export_to_string
csv_string = export_to_string(results, format='csv')
print(csv_string)
```

## CLI Commands

### Generate Reports

```bash
# Campaign performance (last 7 days)
xw ads report performance --customer-id 2425288235

# Last 30 days, export to CSV
xw ads report performance --customer-id 2425288235 --days 30 --output report.csv --format csv

# Conversion performance
xw ads report conversions --customer-id 2425288235 --days 30

# Search terms report
xw ads report search-terms --customer-id 2425288235 --days 14

# Asset group performance (Performance Max)
xw ads report asset-groups --customer-id 2425288235 --campaign-id 123456

# Show the GAQL query
xw ads report performance --customer-id 2425288235 --show-query
```

### Execute Custom Queries

```bash
# Execute GAQL query
xw ads query --customer-id 2425288235 "SELECT campaign.name FROM campaign LIMIT 10"

# Read query from file
xw ads query --customer-id 2425288235 --file query.gaql

# Export results to CSV
xw ads query --customer-id 2425288235 --file query.gaql --output results.csv --format csv

# Show formatted query
xw ads query --customer-id 2425288235 --file query.gaql --show-query
```

## GAQL Builder API

### Basic Structure

```python
from xwander_ads.reporting import GAQLBuilder

query = (
    GAQLBuilder()
    .select(...)          # Required: fields to retrieve
    .from_resource(...)   # Required: resource type
    .where(...)           # Optional: filter conditions
    .during(...)          # Optional: date range shortcut
    .order_by(...)        # Optional: sort order
    .limit(...)           # Optional: max rows
    .build()              # Returns GAQL string
)
```

### Methods

#### `select(*fields)` - Add fields to SELECT

```python
builder.select('campaign.id', 'campaign.name', 'metrics.clicks')
```

#### `from_resource(resource)` - Set FROM resource

```python
builder.from_resource('campaign')  # campaign, ad_group, keyword_view, etc.
```

#### `where(condition)` - Add WHERE condition

```python
builder.where('campaign.status = ENABLED')
builder.where('campaign.id = 123456')
```

#### `during(date_range)` - Add date range (shortcut)

```python
builder.during('LAST_7_DAYS')   # Last 7 days
builder.during('LAST_30_DAYS')  # Last 30 days
builder.during('THIS_MONTH')    # Current month
```

#### `date_between(start, end)` - Date range between dates

```python
builder.date_between('2025-01-01', '2025-01-31')
```

#### `order_by(field, desc=False)` - Sort results

```python
builder.order_by('metrics.clicks', desc=True)
builder.order_by('campaign.name')  # Ascending (default)
```

#### `limit(count)` - Limit rows returned

```python
builder.limit(50)
```

## Query Templates

Pre-built templates for common reports:

### Campaign Performance

```python
templates.campaign_performance(
    days=7,              # Number of days (default: 7)
    enabled_only=True,   # Only enabled campaigns (default: True)
    limit=50             # Max rows (default: 50)
)
```

Returns: Campaign ID, name, status, impressions, clicks, CTR, cost, conversions, etc.

### Conversion Actions

```python
templates.conversion_actions(customer_id="123")
```

Returns: All conversion actions with status, type, category.

### Conversion Performance

```python
templates.conversion_performance(
    days=30,    # Number of days (default: 30)
    limit=50    # Max rows (default: 50)
)
```

Returns: Conversion action performance metrics.

### Search Terms

```python
templates.search_terms(
    days=14,            # Number of days (default: 14)
    campaign_id=None,   # Filter by campaign (optional)
    limit=100           # Max rows (default: 100)
)
```

Returns: Search terms with clicks, cost, conversions.

### Asset Group Performance

```python
templates.asset_group_performance(
    campaign_id=None,   # Filter by campaign (optional)
    days=30,            # Number of days (default: 30)
    limit=50            # Max rows (default: 50)
)
```

Returns: Performance Max asset group metrics.

### Ad Group Performance

```python
templates.ad_group_performance(
    campaign_id=None,   # Filter by campaign (optional)
    days=30,            # Number of days (default: 30)
    limit=50            # Max rows (default: 50)
)
```

### Keyword Performance

```python
templates.keyword_performance(
    campaign_id=None,   # Filter by campaign (optional)
    ad_group_id=None,   # Filter by ad group (optional)
    days=30,            # Number of days (default: 30)
    limit=100           # Max rows (default: 100)
)
```

### Geographic Performance

```python
templates.geographic_performance(
    days=30,    # Number of days (default: 30)
    limit=50    # Max rows (default: 50)
)
```

### Audience Performance

```python
templates.audience_performance(
    days=30,    # Number of days (default: 30)
    limit=50    # Max rows (default: 50)
)
```

## Export Formats

### CSV

```python
from xwander_ads.reporting import CSVExporter

# To file
CSVExporter.export(results, 'output.csv')

# With specific columns
CSVExporter.export(results, 'output.csv', columns=['campaign.name', 'metrics.clicks'])

# To string
csv_string = CSVExporter.to_string(results)
```

### JSON

```python
from xwander_ads.reporting import JSONExporter

# To file
JSONExporter.export(results, 'output.json', indent=2)

# To string
json_string = JSONExporter.to_string(results)
```

### Markdown

```python
from xwander_ads.reporting import MarkdownExporter

# To file with title
MarkdownExporter.export(results, 'output.md', title="Campaign Performance")

# To string
md_string = MarkdownExporter.to_string(results)
```

### BigQuery (Planned)

```python
from xwander_ads.reporting import BigQueryExporter

# Coming soon
BigQueryExporter.export(
    results,
    project_id='my-project',
    dataset_id='google_ads',
    table_id='campaign_performance'
)
```

## Formatting Helpers

### Format Micros as Currency

```python
from xwander_ads.reporting import format_micros

cost_micros = 1500000  # 1.5 EUR in micros
formatted = format_micros(cost_micros, currency="EUR")
# Result: "EUR 1.50"
```

### Format Decimal as Percentage

```python
from xwander_ads.reporting import format_percentage

ctr = 0.0523  # 5.23%
formatted = format_percentage(ctr)
# Result: "5.23%"
```

### Table Formatter

```python
from xwander_ads.reporting import TableFormatter

# Generic table
table = TableFormatter.format(results)
print(table)

# Performance table (formatted for campaign performance)
table = TableFormatter.format_performance(results, currency="EUR")
print(table)
```

## Examples

### Example 1: Weekly Performance Report

```python
from xwander_ads.reporting import templates, execute_query, export_results
from xwander_ads.auth import get_client

client = get_client()
customer_id = "2425288235"

# Generate report
query = templates.campaign_performance(days=7, enabled_only=True, limit=100)
results = execute_query(client, customer_id, query)

# Export to CSV
export_results(results, '/tmp/weekly-performance.csv', format='csv')

print(f"Exported {len(results)} campaigns")
```

### Example 2: Search Term Analysis

```python
query = templates.search_terms(days=30, limit=200)
results = execute_query(client, customer_id, query)

# Find high-cost, low-conversion terms
wasteful_terms = [
    r for r in results
    if r.get('metrics.cost_micros', 0) > 10_000_000  # > EUR 10
    and r.get('metrics.conversions', 0) == 0
]

print(f"Found {len(wasteful_terms)} wasteful search terms")
for term in wasteful_terms:
    print(f"  {term['search_term_view.search_term']}: {format_micros(term['metrics.cost_micros'])}")
```

### Example 3: Custom Query with Builder

```python
from xwander_ads.reporting import GAQLBuilder

# Build custom query
query = (
    GAQLBuilder()
    .select(
        'campaign.id',
        'campaign.name',
        'ad_group.id',
        'ad_group.name',
        'metrics.impressions',
        'metrics.clicks',
        'metrics.conversions'
    )
    .from_resource('ad_group')
    .where('campaign.id = 123456')
    .where('ad_group.status = ENABLED')
    .during('LAST_7_DAYS')
    .order_by('metrics.conversions', desc=True)
    .limit(50)
    .build()
)

results = execute_query(client, customer_id, query)

# Format and print
from xwander_ads.reporting import TableFormatter
print(TableFormatter.format(results))
```

## Error Handling

```python
from xwander_ads.exceptions import AdsError

try:
    results = execute_query(client, customer_id, query)
except AdsError as e:
    print(f"Query failed: {e}")
    print(f"Exit code: {e.exit_code}")
```

## Best Practices

1. **Always use LIMIT**: Prevent accidentally pulling massive datasets
2. **Validate queries**: Use `validate_query()` before execution
3. **Use templates**: Start with templates and modify as needed
4. **Filter by date**: Always include date range for performance queries
5. **Stream large results**: Use `execute_query_stream()` for very large datasets

## Resources

- [GAQL Reference](../../../xwander.com/growth/docs/gaql-reference.md)
- [Google Ads Query Language Guide](https://developers.google.com/google-ads/api/docs/query/overview)
- [Field Selector Reference](https://developers.google.com/google-ads/api/fields/v20)
