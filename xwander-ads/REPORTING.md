# xwander-ads Reporting Module

Built on 2026-01-10. Complete GAQL query builder and reporting functionality for Google Ads.

## What Was Built

### 1. GAQL Query Builder (`xwander_ads/reporting/gaql.py`)
Fluent API for building Google Ads Query Language queries:

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
```

**Features:**
- Fluent/chainable API
- Query validation
- Query formatting for readability
- Date range helpers (`during()`, `date_between()`)

### 2. Query Templates (`xwander_ads/reporting/templates.py`)
Pre-built queries for common reports:

- `campaign_performance()` - Campaign metrics
- `conversion_actions()` - List conversion actions
- `conversion_performance()` - Conversion metrics
- `search_terms()` - Search term report
- `asset_group_performance()` - Performance Max asset groups
- `ad_group_performance()` - Ad group metrics
- `keyword_performance()` - Keyword metrics
- `geographic_performance()` - Geographic data
- `audience_performance()` - Audience metrics

### 3. Query Execution (`xwander_ads/reporting/reports.py`)
Execute queries and format results:

```python
from xwander_ads.reporting import execute_query, TableFormatter

results = execute_query(client, customer_id, query)
print(TableFormatter.format_performance(results))
```

**Features:**
- `execute_query()` - Execute and return all results
- `execute_query_stream()` - Stream large result sets
- `TableFormatter` - Format as ASCII tables
- Helper functions for formatting micros, percentages

### 4. Export Functionality (`xwander_ads/reporting/export.py`)
Export results to multiple formats:

```python
from xwander_ads.reporting import export_results

# Export to CSV
export_results(results, '/tmp/report.csv', format='csv')

# Export to JSON
export_results(results, '/tmp/report.json', format='json')

# Export to Markdown
export_results(results, '/tmp/report.md', format='markdown')
```

**Formats supported:**
- CSV
- JSON
- Markdown
- BigQuery (placeholder for future)

### 5. CLI Commands

#### Report Command
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

#### Query Command
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

## Files Created

```
/srv/plugins/xwander-ads/
├── xwander_ads/reporting/
│   ├── __init__.py          # Module exports
│   ├── gaql.py              # GAQL query builder
│   ├── reports.py           # Query execution & formatting
│   ├── templates.py         # Pre-built query templates
│   ├── export.py            # Export to CSV/JSON/Markdown
│   └── README.md            # Comprehensive documentation
├── tests/
│   └── test_reporting.py    # 22 tests (all passing)
└── examples/
    └── reporting_example.py # Usage examples
```

## Test Results

```
22 tests PASSED in 0.33s
```

Tests cover:
- GAQL query building (9 tests)
- Query validation (3 tests)
- Query formatting (2 tests)
- Query templates (4 tests)
- Export functionality (4 tests)

## Migration from Existing Code

Migrated functionality from:
- `/srv/xwander-platform/xwander.com/growth/toolkit/reports.py`

**Improvements over original:**
1. Fluent query builder API (easier to build complex queries)
2. Pre-built templates for common reports
3. Multiple export formats (CSV, JSON, Markdown)
4. Comprehensive test coverage
5. Better error handling with AdsError
6. Query validation and formatting
7. CLI integration with argparse
8. Streaming support for large datasets

## Usage Examples

### Example 1: Campaign Performance Report

```python
from xwander_ads.reporting import templates, execute_query
from xwander_ads.auth import get_client

client = get_client()
query = templates.campaign_performance(days=7, limit=50)
results = execute_query(client, '2425288235', query)

print(f"Found {len(results)} campaigns")
```

### Example 2: Search Term Analysis

```python
from xwander_ads.reporting import GAQLBuilder, execute_query

query = (
    GAQLBuilder()
    .select('search_term_view.search_term', 'metrics.clicks', 'metrics.cost_micros')
    .from_resource('search_term_view')
    .during('LAST_14_DAYS')
    .order_by('metrics.cost_micros', desc=True)
    .limit(100)
    .build()
)

results = execute_query(client, '2425288235', query)
```

### Example 3: Export to CSV

```python
from xwander_ads.reporting import export_results

export_results(results, '/tmp/report.csv', format='csv')
print("Exported to /tmp/report.csv")
```

## Reference Documentation

### Knowledge Base Files Used
- `/srv/xwander-platform/xwander.com/growth/knowledge/accounts.json` - Account IDs
- `/srv/xwander-platform/xwander.com/growth/docs/gaql-reference.md` - GAQL syntax

### API Documentation
- GAQL Builder: `xwander_ads/reporting/README.md`
- Query Templates: See docstrings in `templates.py`
- Export Formats: See docstrings in `export.py`

## Next Steps

1. **Test with real API credentials**
   ```bash
   xw ads report performance --customer-id 2425288235 --days 7
   ```

2. **Create custom query files**
   ```sql
   # query.gaql
   SELECT
     campaign.name,
     metrics.clicks,
     metrics.cost_micros
   FROM campaign
   WHERE segments.date DURING LAST_30_DAYS
   LIMIT 50
   ```

   ```bash
   xw ads query --customer-id 2425288235 --file query.gaql
   ```

3. **Schedule automated reports** (future enhancement)
   - Weekly performance reports
   - Daily search term analysis
   - Monthly conversion summaries

4. **BigQuery integration** (future enhancement)
   - Export directly to BigQuery
   - Enable data warehouse analytics
   - Join with other data sources

## Integration with Existing Toolkit

The reporting module is now available via:

1. **CLI**: `xw ads report` and `xw ads query`
2. **Python API**: `from xwander_ads.reporting import ...`
3. **Legacy migration**: Original `toolkit/reports.py` can be replaced

## Token Efficiency

**IMPORTANT**: Direct GAQL queries via CLI/module are MUCH more efficient than MCP:
- MCP call: ~100K+ tokens (includes full API response)
- CLI/Python: ~1K tokens (just the query + minimal output)

**Best practice**: Always use CLI or Python API, not MCP directly.

---

Built with Claude Sonnet 4.5 on 2026-01-10
