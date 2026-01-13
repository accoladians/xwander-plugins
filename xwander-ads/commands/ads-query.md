---
description: Execute custom GAQL queries
argument-hint: <query> [--customer-id ID] [--format {table|csv|json}]
allowed-tools: [Bash, Read, Write]
---

# Execute Custom GAQL Queries

Run custom Google Ads Query Language (GAQL) queries for advanced data retrieval and analysis.

## Usage

```
/ads-query "SELECT campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS"
/ads-query "SELECT ad_group.name, metrics.conversions FROM ad_group LIMIT 20" --format csv
```

## Implementation

```bash
export PYTHONPATH="/srv/plugins/xwander-ads:$PYTHONPATH"
cd /srv/plugins/xwander-ads
python3 -m xwander_ads.cli query --customer-id 2425288235 --query "{query}" [--format {format}]
```

## Parameters

- `query` (required) - GAQL query string
- `--customer-id ID` - Customer ID (default: 2425288235)
- `--format {table|csv|json}` - Output format (default: table)
- `--output PATH` - Save results to file
- `--limit N` - Row limit (recommended: 50 max)

## GAQL Syntax

### Basic Structure

```sql
SELECT
  resource.field,
  metrics.metric_name
FROM
  resource_name
WHERE
  segments.date DURING LAST_30_DAYS
ORDER BY
  metrics.metric_name DESC
LIMIT 50
```

### Common Resources

- `campaign` - Campaign-level data
- `ad_group` - Ad group data
- `ad_group_ad` - Ad-level data
- `keyword_view` - Keyword performance
- `campaign_search_term_view` - Search terms
- `asset_group` - Performance Max asset groups
- `asset_group_signal` - PMax signals

### Date Filters

```sql
segments.date DURING LAST_7_DAYS
segments.date DURING LAST_30_DAYS
segments.date DURING LAST_90_DAYS
segments.date BETWEEN '2025-01-01' AND '2025-01-31'
```

## Example Queries

### Campaign Performance

```sql
SELECT
  campaign.name,
  campaign.status,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 20
```

### Search Terms

```sql
SELECT
  campaign_search_term_view.search_term,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions
FROM campaign_search_term_view
WHERE segments.date DURING LAST_14_DAYS
ORDER BY metrics.clicks DESC
LIMIT 50
```

### Asset Group Signals

```sql
SELECT
  asset_group_signal.asset_group,
  asset_group_signal.audience.audience,
  asset_group_signal.search_theme.search_theme
FROM asset_group_signal
WHERE asset_group.id = 6655152002
```

## Best Practices

- **Always use LIMIT** - Prevent large result sets (max 50 recommended)
- **Date filters** - Narrow down with WHERE clauses
- **Micros conversion** - cost_micros / 1,000,000 = EUR
- **Test queries** - Start with small date ranges
- **Reference docs** - See `docs/QUICK_REFERENCE.json` for field names

## Output Formats

### table (default)
Human-readable table format for terminal display.

### csv
Comma-separated values for spreadsheet import.

### json
Structured JSON for programmatic processing.

## Error Handling

Common errors:
- **Invalid field name** - Check GAQL reference
- **Quota exceeded** - Reduce date range or LIMIT
- **Authentication failed** - Verify google-ads.yaml credentials

## Related Commands

- `/ads-report` - Predefined report templates
- `/ads-pmax-list` - Quick campaign overview

## Resources

- **GAQL Reference:** docs/QUICK_REFERENCE.json
- **Google Docs:** https://developers.google.com/google-ads/api/docs/query/overview
- **Field Catalog:** https://developers.google.com/google-ads/api/fields
