# Xwander GA4 Plugin - AI Agent Guide

**Version:** 1.1.0 | **Updated:** 2026-01-13

AI agent guide for using the xwander-ga4 plugin effectively.

---

## Quick Commands Reference

```bash
# Property ID (default for all commands)
DEFAULT_PROPERTY_ID=358203796  # xwander.com

# Quick reports
xwander-ga4 traffic-sources --days 30
xwander-ga4 top-pages --days 30
xwander-ga4 conversions --days 30
xwander-ga4 daily-summary --days 30
xwander-ga4 realtime

# Custom reports
xwander-ga4 report \
  --dimensions date source \
  --metrics sessions users \
  --days 7 \
  --format table

# Dimension management
xwander-ga4 dimension list
xwander-ga4 dimension list --scope EVENT
xwander-ga4 dimension create \
  --display-name "Product Type" \
  --parameter-name product_type \
  --description "Tour type classification"

# Audience management
xwander-ga4 audience list
xwander-ga4 audience list --sort-by-size
xwander-ga4 audience search "Northern Lights"
```

---

## Decision Tree

### When to use which command?

#### Need traffic source breakdown?
```bash
xwander-ga4 traffic-sources --days 30
# Returns: source, medium, sessions, activeUsers, bounceRate
```

#### Need top pages?
```bash
xwander-ga4 top-pages --days 30
# Returns: pagePath, sessions, activeUsers, averageSessionDuration
```

#### Need conversion data?
```bash
xwander-ga4 conversions --days 30
# Returns: eventName, eventCount, eventValue
```

#### Need daily trend?
```bash
xwander-ga4 daily-summary --days 30
# Returns: date, sessions, activeUsers, eventCount
```

#### Need realtime data?
```bash
xwander-ga4 realtime
# Returns: country, activeUsers (live)
```

#### Need custom report?
```bash
xwander-ga4 report \
  --dimensions <dimension_names> \
  --metrics <metric_names> \
  --days <N> \
  --format table|json|summary
```

#### Need to create custom dimension?
```bash
# 1. Check if it already exists
xwander-ga4 dimension list

# 2. Create if needed
xwander-ga4 dimension create \
  --display-name "User Friendly Name" \
  --parameter-name snake_case_name \
  --scope EVENT|USER|ITEM \
  --description "What this tracks"
```

#### Need to find audiences?
```bash
# List all
xwander-ga4 audience list

# Find by size
xwander-ga4 audience list --sort-by-size

# Search by name
xwander-ga4 audience search "search_term"
```

---

## Common Workflows

### Workflow 1: Traffic Analysis

```bash
# 1. Get traffic sources for last 30 days
xwander-ga4 traffic-sources --days 30

# 2. Get top pages
xwander-ga4 top-pages --days 30

# 3. Get conversions
xwander-ga4 conversions --days 30

# 4. Analyze by date
xwander-ga4 report \
  --dimensions date source \
  --metrics sessions users \
  --days 30 \
  --format table
```

### Workflow 2: Custom Dimension Creation

```bash
# 1. Check existing dimensions
xwander-ga4 dimension list

# 2. Create new dimension
xwander-ga4 dimension create \
  --display-name "Product Category" \
  --parameter-name product_category \
  --scope EVENT \
  --description "Categorize tours by type"

# 3. Verify creation
xwander-ga4 dimension list --scope EVENT
```

### Workflow 3: Audience Research

```bash
# 1. List all audiences by size
xwander-ga4 audience list --sort-by-size

# 2. Search for specific audiences
xwander-ga4 audience search "Purchasers"

# 3. Search for campaign-related audiences
xwander-ga4 audience search "Northern Lights"
```

### Workflow 4: Daily Performance Report

```bash
# 1. Get daily summary
xwander-ga4 daily-summary --days 7

# 2. Get conversions
xwander-ga4 conversions --days 7

# 3. Get realtime snapshot
xwander-ga4 realtime

# 4. Export as JSON for processing
xwander-ga4 report \
  --dimensions date \
  --metrics sessions users conversions \
  --days 7 \
  --format json > /tmp/daily-report.json
```

---

## Property ID Default

All commands default to Xwander property:
```
DEFAULT_PROPERTY_ID=358203796
```

To use a different property, add `--property-id <ID>` to any command.

---

## Error Handling Reference

### Common Errors

#### "Failed to initialize GA4 Data API"
**Cause:** Missing or invalid Google credentials
**Solution:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### "Property not found"
**Cause:** Invalid property ID or no access
**Solution:** Verify property ID and service account permissions

#### "Custom dimension failed"
**Cause:** Dimension already exists or invalid parameter name
**Solution:**
- Check existing dimensions: `xwander-ga4 dimension list`
- Validate parameter name: alphanumeric + underscore only, cannot start with digit

#### "No data returned"
**Cause:** No data for requested dimensions/metrics
**Solution:** Check date range, verify dimensions/metrics exist

---

## Python API Usage

### Quick Start

```python
from xwander_ga4 import GA4DataClient, ReportBuilder, ReportFormatter

# Initialize
client = GA4DataClient('358203796')
builder = ReportBuilder(client)

# Run report
result = builder.traffic_sources(days=30)

# Format output
formatter = ReportFormatter()
print(formatter.table(result))
```

### Error Handling

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

---

## Common Dimensions & Metrics

### Dimensions
| Name | Type | Example |
|------|------|---------|
| date | Time | 2026-01-13 |
| source | Traffic | google, facebook |
| medium | Traffic | organic, cpc |
| pagePath | Content | /plan-your-holiday/ |
| country | Geo | Finland |
| deviceCategory | Tech | mobile, desktop |
| eventName | Event | purchase, lead_form |

### Metrics
| Name | Type | Description |
|------|------|-------------|
| sessions | Engagement | Total sessions |
| activeUsers | Engagement | Active users |
| bounceRate | Engagement | Bounce rate (0-100) |
| eventCount | Event | Total events |
| eventValue | Event | Event value |
| conversions | Conversion | Total conversions |

**Full list:** See `docs/API.md` for complete dimension and metric reference.

---

## Output Formats

### Table (default)
```bash
xwander-ga4 report --dimensions date --metrics sessions --format table
```
Best for: Terminal display, human reading

### JSON
```bash
xwander-ga4 report --dimensions date --metrics sessions --format json
```
Best for: Programmatic processing, saving to files

### Summary
```bash
xwander-ga4 report --dimensions date --metrics sessions --format summary
```
Best for: Quick overview, first 5 rows + quota info

---

## Tips for AI Agents

### DO
- Always use `xwander-ga4` command (not `xw ga4`)
- Check existing dimensions before creating new ones
- Use `--format json` for parsing results
- Use specific date ranges with `--start-date` and `--end-date` when precision matters
- Use predefined reports (traffic-sources, top-pages, etc.) when possible
- Include `--limit` to control result size

### DON'T
- Don't create dimensions without checking if they exist
- Don't use property ID other than 358203796 without explicit request
- Don't forget to validate parameter names (alphanumeric + underscore)
- Don't exceed quota (check quota in result output)

### Best Practices
1. Start with predefined reports (traffic-sources, top-pages, conversions)
2. Use custom reports only when predefined ones don't fit
3. Always specify reasonable `--limit` values
4. Check error messages carefully (they guide to solution)
5. Use `--format json` for automation, `table` for humans
6. Save large results to files instead of printing

---

## File Locations

```
/srv/plugins/xwander-ga4/
├── xwander_ga4/           # Python package
│   ├── __init__.py        # Version: 1.1.0
│   ├── cli.py             # CLI commands
│   ├── client.py          # API clients
│   ├── reports.py         # Report builders
│   ├── dimensions.py      # Dimension manager
│   └── audiences.py       # Audience manager
├── docs/
│   └── API.md             # Full API documentation
├── CLAUDE.md              # This file
└── README.md              # Installation guide
```

---

## Related Documentation

- Full API Docs: `/srv/plugins/xwander-ga4/docs/API.md`
- GA4 Config: `/srv/xwander-platform/xwander.com/growth/knowledge/ga4.json`
- GA4 Data API: https://developers.google.com/analytics/devguides/reporting/data/v1
- GA4 Admin API: https://developers.google.com/analytics/devguides/config/admin/v1

---

**Last Updated:** 2026-01-13
**Plugin Version:** 1.1.0
**Default Property:** 358203796 (xwander.com)
