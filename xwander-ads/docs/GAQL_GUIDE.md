# GAQL Guide - xwander-ads Plugin

## Overview

GAQL (Google Ads Query Language) is used throughout the xwander-ads plugin for querying Google Ads data. This guide documents key patterns and best practices.

## Key Concepts

### 1. GAQL Does NOT Support Subqueries

Unlike SQL, GAQL does not support nested SELECT statements. Use implicit joins instead.

**WRONG** (will fail):
```sql
SELECT asset_group.id
FROM asset_group
WHERE asset_group.campaign IN (
    SELECT campaign.resource_name
    FROM campaign
    WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
)
```

**CORRECT** (implicit join):
```sql
SELECT asset_group.id, campaign.id, campaign.name
FROM asset_group
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
```

### 2. Implicit Joins

When querying from a resource, related resources are automatically accessible:

| FROM Resource | Joined Resources |
|---------------|------------------|
| `asset_group` | `campaign` (via `asset_group.campaign`) |
| `ad_group` | `campaign` |
| `keyword_view` | `campaign`, `ad_group`, `ad_group_criterion` |
| `search_term_view` | `campaign`, `ad_group` |
| `geographic_view` | `campaign` |

### 3. WHERE Clause Patterns

```sql
-- Filter by campaign type
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'

-- Filter by campaign ID (numeric, no quotes)
WHERE campaign.id = 12345678

-- Filter by status
WHERE campaign.status = 'ENABLED'
AND asset_group.status != 'REMOVED'

-- Filter by resource name (requires quotes)
WHERE asset_group.campaign = 'customers/123/campaigns/456'
```

### 4. Date Filtering

```sql
-- Using DURING clause
WHERE segments.date DURING LAST_7_DAYS

-- Using date range
WHERE segments.date BETWEEN '2026-01-01' AND '2026-01-10'
```

### 5. Required LIMIT

Always include a LIMIT clause (max 10,000):

```sql
SELECT campaign.id, campaign.name
FROM campaign
LIMIT 100
```

## Common Queries

### List PMax Campaigns

```sql
SELECT
    campaign.id,
    campaign.name,
    campaign.status,
    campaign_budget.amount_micros,
    metrics.cost_micros,
    metrics.impressions,
    metrics.clicks,
    metrics.conversions
FROM campaign
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
ORDER BY campaign.name
LIMIT 50
```

### List Asset Groups for PMax

```sql
SELECT
    asset_group.id,
    asset_group.name,
    asset_group.status,
    campaign.id,
    campaign.name
FROM asset_group
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
ORDER BY asset_group.name
LIMIT 100
```

### Asset Group Performance

```sql
SELECT
    campaign.id,
    campaign.name,
    asset_group.id,
    asset_group.name,
    asset_group.status,
    metrics.impressions,
    metrics.clicks,
    metrics.cost_micros,
    metrics.conversions
FROM asset_group
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
AND segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 50
```

### Search Term Report

```sql
SELECT
    campaign.name,
    ad_group.name,
    search_term_view.search_term,
    segments.search_term_match_type,
    metrics.impressions,
    metrics.clicks,
    metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_14_DAYS
ORDER BY metrics.clicks DESC
LIMIT 100
```

## Input Validation

Always validate user input before interpolating into GAQL:

```python
def validate_campaign_id(campaign_id: str) -> str:
    """Validate and normalize campaign ID."""
    campaign_id = str(campaign_id).replace('-', '')
    if not campaign_id.isdigit():
        raise ValueError(f"Invalid campaign_id: must be numeric")
    return campaign_id
```

## Error Handling

Common GAQL errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid value campaign.resource_name` | Subquery attempted | Use implicit join |
| `LIMIT is required` | Missing LIMIT | Add LIMIT clause |
| `invalid value` in WHERE | Wrong data type | Check field type (string vs int) |
| `field not available` | Wrong resource | Check API schema for field availability |

## References

- [GAQL Grammar](https://developers.google.com/google-ads/api/docs/query/grammar)
- [GAQL Overview](https://developers.google.com/google-ads/api/docs/query/overview)
- [API Schema](https://developers.google.com/google-ads/api/docs/query/schema)

---
*Updated: 2026-01-12*
