---
description: Generate Google Ads performance reports
argument-hint: <report-type> [--days N] [--customer-id ID]
allowed-tools: [Bash, Read, Write]
---

# Generate Google Ads Reports

Generate performance reports for Xwander Nordic campaigns using predefined templates or custom GAQL queries.

## Usage

```
/ads-report performance --days 30
/ads-report conversions --days 7
/ads-report search-terms --days 14
/ads-report custom --query "SELECT ..." --output /tmp/report.csv
```

## Report Types

### performance
Campaign performance overview with key metrics.

**Metrics:** Impressions, clicks, CTR, cost, conversions, CPA, ROAS

### conversions
Conversion tracking analysis by action.

**Metrics:** Conversions by action, conversion rate, value, cost per conversion

### search-terms
Search terms performance (queries triggering ads).

**Metrics:** Search term, impressions, clicks, CTR, conversions

### custom
Execute custom GAQL query for advanced reporting.

**Parameters:**
- `--query TEXT` - GAQL query string
- `--output PATH` - Optional output file path

## Implementation

```bash
export PYTHONPATH="/srv/plugins/xwander-ads:$PYTHONPATH"
cd /srv/plugins/xwander-ads
python3 -m xwander_ads.cli report {type} --customer-id 2425288235 --days {days} [--output {path}]
```

## Common Parameters

- `--customer-id ID` - Customer ID (default: 2425288235)
- `--days N` - Date range in days (default: 30)
- `--output PATH` - Save to file (CSV or JSON)
- `--format {table|csv|json}` - Output format (default: table)

## Example Output

```
=== Campaign Performance (Last 30 Days) ===

Campaign: Coolcation PMax
  Impressions: 45,678
  Clicks: 1,234 (2.70% CTR)
  Cost: EUR 2,345.67
  Conversions: 45 (3.65% rate)
  CPA: EUR 52.13
  ROAS: 4.2x
```

## GAQL Reference

See `docs/QUICK_REFERENCE.json` for:
- Common queries
- Available fields
- Metric definitions
- Segmentation options

## Best Practices

- **Date range:** Last 30-90 days for meaningful trends
- **Limit results:** Use LIMIT clause for large datasets
- **Export data:** Use --output for analysis in spreadsheets
- **Custom queries:** Test with small date ranges first

## Related Commands

- `/ads-pmax-list` - Quick campaign overview
- `/ads-conversion-sync` - Sync offline conversions
