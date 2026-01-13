---
description: List Performance Max campaigns with metrics
argument-hint: [--customer-id ID] [--enabled-only]
allowed-tools: [Bash, Read]
---

# List Performance Max Campaigns

List all Performance Max campaigns for Xwander Nordic with performance metrics.

## Usage

```
/ads-pmax-list
/ads-pmax-list --customer-id 2425288235
/ads-pmax-list --enabled-only
```

## Implementation

1. Set customer ID (default: 2425288235 from knowledge/accounts.json)
2. Set Python path and execute via CLI:
   ```bash
   export PYTHONPATH="/srv/plugins/xwander-ads:$PYTHONPATH"
   cd /srv/plugins/xwander-ads
   python3 -m xwander_ads.cli pmax list --customer-id {customer_id} --campaigns
   ```
3. Parse output and format for user
4. If error, suggest checking credentials or reviewing docs/QUICK_REFERENCE.json

## Example Output

```
=== Performance Max Campaigns (2) ===

23423204148: Coolcation PMax
  Status: ENABLED | Budget: EUR 100.00 | Spent: EUR 45.67
  Impressions: 12,345 | Clicks: 456 | Conversions: 23.0

21956481773: Winter Tours
  Status: PAUSED | Budget: EUR 50.00 | Spent: EUR 0.00
```

## Related Commands

- `/ads-pmax-signals` - Manage search themes
- `/ads-report` - Generate performance reports

## Context

Uses Google Ads API v20 (stable) by default. Customer ID 2425288235 is Xwander Nordic account.
