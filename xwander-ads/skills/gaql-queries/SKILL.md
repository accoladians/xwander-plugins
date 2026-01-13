---
name: gaql-queries
description: Activate when user needs custom Google Ads data analysis, advanced reporting, or specific metric queries. Provides GAQL query building and execution guidance.
version: 1.0.1
---

# GAQL Queries Skill

## Purpose

Guide Claude through building and executing Google Ads Query Language (GAQL) queries for advanced data analysis and custom reporting.

## When to Use

Activate this skill when user:
- Requests specific data not available in standard reports
- Needs custom metrics or segmentation
- Wants to analyze historical trends
- Asks for "query", "GAQL", or "SQL-like" analysis
- Needs data export for external analysis

## GAQL Fundamentals

### Basic Syntax

```sql
SELECT
  resource.field,
  metrics.metric_name
FROM
  resource_name
WHERE
  condition
ORDER BY
  field DESC
LIMIT 50
```

### Key Concepts

- **Resources:** campaign, ad_group, keyword_view, asset_group, etc.
- **Metrics:** clicks, impressions, conversions, cost_micros, etc.
- **Segments:** date, day_of_week, device, etc.
- **Attributes:** name, status, id, etc.

## How to Use

### 1. Execute Custom Query

```
/ads-query "SELECT campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS LIMIT 20"
```

### 2. Generate Report from Query

```
/ads-query "{query}" --format csv --output /tmp/report.csv
```

### 3. Build Query Interactively

For complex queries, break down into steps:

1. **Identify resource:** What data source? (campaign, ad_group, etc.)
2. **Select fields:** What columns needed?
3. **Add filters:** Date range, status, etc.
4. **Add sorting:** ORDER BY most important metric
5. **Limit results:** LIMIT 50 max (internal tool, light use)

## Common Query Templates

### Campaign Performance

```sql
SELECT
  campaign.id,
  campaign.name,
  campaign.status,
  campaign.advertising_channel_type,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.conversions_value
FROM campaign
WHERE
  segments.date DURING LAST_30_DAYS
  AND campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
LIMIT 20
```

### Search Terms Analysis

```sql
SELECT
  campaign_search_term_view.search_term,
  campaign_search_term_view.status,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.conversions,
  metrics.cost_micros
FROM campaign_search_term_view
WHERE
  segments.date DURING LAST_14_DAYS
  AND metrics.impressions > 10
ORDER BY metrics.clicks DESC
LIMIT 50
```

### Conversion Action Performance

```sql
SELECT
  conversion_action.id,
  conversion_action.name,
  conversion_action.category,
  conversion_action.status,
  metrics.conversions,
  metrics.conversions_value,
  metrics.cost_per_conversion
FROM conversion_action
WHERE
  conversion_action.status = 'ENABLED'
ORDER BY metrics.conversions DESC
LIMIT 50
```

### Asset Group Signals

```sql
SELECT
  asset_group.id,
  asset_group.name,
  asset_group_signal.search_theme.search_theme
FROM asset_group_signal
WHERE
  asset_group.campaign = 'customers/2425288235/campaigns/23423204148'
```

### Device Performance

```sql
SELECT
  campaign.name,
  segments.device,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.conversions,
  metrics.cost_micros
FROM campaign
WHERE
  segments.date DURING LAST_30_DAYS
ORDER BY segments.device, metrics.cost_micros DESC
LIMIT 50
```

### Geographic Performance

```sql
SELECT
  geographic_view.country_criterion_id,
  metrics.impressions,
  metrics.clicks,
  metrics.conversions,
  metrics.cost_micros
FROM geographic_view
WHERE
  segments.date DURING LAST_30_DAYS
ORDER BY metrics.conversions DESC
LIMIT 50
```

## Date Range Options

```sql
-- Last N days
segments.date DURING LAST_7_DAYS
segments.date DURING LAST_30_DAYS
segments.date DURING LAST_90_DAYS

-- Specific date range
segments.date BETWEEN '2025-01-01' AND '2025-01-31'

-- This month
segments.date DURING THIS_MONTH

-- Last month
segments.date DURING LAST_MONTH
```

## Field Reference

### Common Metrics

| Metric | Description | Format |
|--------|-------------|--------|
| impressions | Ad impressions | Integer |
| clicks | Ad clicks | Integer |
| ctr | Click-through rate | Decimal (0.0523 = 5.23%) |
| cost_micros | Cost in micros | Integer (divide by 1M for EUR) |
| conversions | Total conversions | Decimal |
| conversions_value | Conversion value | Decimal |
| cost_per_conversion | CPA | Decimal |
| conversion_rate | Conv rate | Decimal (0.035 = 3.5%) |

### Common Resources

- **campaign** - Campaign-level metrics
- **ad_group** - Ad group metrics
- **keyword_view** - Keyword performance
- **campaign_search_term_view** - Search queries
- **asset_group** - PMax asset groups
- **asset_group_signal** - PMax signals
- **conversion_action** - Conversion tracking
- **geographic_view** - Geographic performance

## Best Practices

### Query Optimization

- **Always use LIMIT** - Prevent large result sets (max 50 for internal use)
- **Date filters required** - Narrow with WHERE clauses
- **Specific fields only** - Don't SELECT * (not supported)
- **Test incrementally** - Start with small date ranges

### Data Formatting

- **Cost conversion:** `cost_micros / 1,000,000 = EUR`
- **Rate fields:** Multiply by 100 for percentage (0.0523 → 5.23%)
- **IDs:** Always use normalized format (remove hyphens)

### Error Prevention

- **Check field compatibility** - Not all fields work together
- **Validate resource names** - Use exact API names
- **Mind quota limits** - Space out large queries
- **Use metrics namespace** - `metrics.clicks` not just `clicks`

## Common Workflows

### Analyze Top Performing Campaigns

```
1. /ads-query "SELECT campaign.name, metrics.conversions, metrics.cost_micros FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.conversions DESC LIMIT 10"
2. Identify top 3 campaigns
3. Deep dive with search terms query for each
4. Extract successful patterns
5. Recommend budget reallocation
```

### Search Term Mining

```
1. /ads-query "SELECT campaign_search_term_view.search_term, metrics.conversions FROM campaign_search_term_view WHERE segments.date DURING LAST_30_DAYS AND metrics.conversions > 0 ORDER BY metrics.conversions DESC LIMIT 50" --format csv
2. Export to /tmp/search-terms.csv
3. Analyze patterns in converting search terms
4. Generate list of new PMax search themes
5. Add themes via /ads-pmax-signals bulk
```

### Conversion Attribution Analysis

```
1. /ads-query "SELECT conversion_action.name, campaign.name, metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS AND metrics.conversions > 0 LIMIT 50"
2. Group conversions by action type
3. Calculate conversion mix (form leads vs purchases)
4. Identify campaigns driving highest-value conversions
5. Recommend optimization priorities
```

## Troubleshooting

### Query fails with "Invalid field"

**Check:**
- Field exists in resource (see GAQL reference)
- Correct namespace (metrics.clicks not just clicks)
- Field compatibility (some fields can't be selected together)

### "Quota exceeded" error

**Fix:**
- Reduce date range
- Lower LIMIT value
- Space out queries (wait 1 minute between large queries)

### Empty result set

**Check:**
- Date range has data (campaign may not have run)
- Filters too restrictive (remove WHERE clauses incrementally)
- Resource exists (verify campaign ID, etc.)

### Authentication error

**Fix:**
- Verify google-ads.yaml credentials
- Check customer ID (2425288235)
- Test auth: `cd /srv/plugins/xwander-ads && python3 -m xwander_ads.cli auth test`

## Context: Xwander Nordic

- **Customer ID:** 2425288235
- **Currency:** EUR (cost_micros / 1,000,000)
- **Timezone:** Europe/Helsinki
- **Primary campaign ID:** 23423204148 (Xwander PMax Nordic)
- **Asset groups:** 6655152002 (EN), 6655251007 (DE), 6655151999 (FR), 6655250848 (ES)

## Related Skills

- **pmax-optimization** - Use query insights for campaign optimization
- **conversion-tracking** - Analyze conversion performance with queries

## Resources

- **GAQL Reference:** /srv/plugins/xwander-ads/docs/QUICK_REFERENCE.json
- **Field Catalog:** https://developers.google.com/google-ads/api/fields
- **Query Validator:** https://developers.google.com/google-ads/api/fields/v20/query_validator
- **Official Docs:** https://developers.google.com/google-ads/api/docs/query/overview

## Advanced Techniques

### Subqueries (via multiple queries)

GAQL doesn't support nested queries, but you can chain:

```
1. Get campaign IDs: /ads-query "SELECT campaign.id FROM campaign WHERE ..."
2. Extract IDs from result
3. Query each campaign: /ads-query "SELECT ... WHERE campaign.id = {id}"
```

### Custom Metrics

Calculate custom metrics from raw data:

```
ROAS = conversions_value / (cost_micros / 1,000,000)
CPA = (cost_micros / 1,000,000) / conversions
Conv Rate = (conversions / clicks) * 100
```

### Aggregation

Use segments for grouping:

```sql
-- By date
segments.date

-- By device
segments.device

-- By day of week
segments.day_of_week
```
