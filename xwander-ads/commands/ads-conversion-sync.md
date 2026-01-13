---
description: Sync HubSpot conversions to Google Ads
argument-hint: [--source {booking|all}] [--days N] [--dry-run]
allowed-tools: [Bash, Read]
---

# Sync HubSpot Conversions to Google Ads

Upload offline conversions from HubSpot (Deal Won events) to Google Ads for attribution tracking.

## Usage

```
/ads-conversion-sync
/ads-conversion-sync --source booking --days 90
/ads-conversion-sync --dry-run
```

## How It Works

1. **Query HubSpot** for closed-won deals in date range
2. **Extract GCLID** from contact properties (hs_google_click_id)
3. **Upload to Google Ads** via offline conversion import API
4. **Attribute revenue** back to original ad clicks

## Parameters

- `--source {booking|all}` - Pipeline filter (default: booking)
- `--days N` - Lookback period (default: 90)
- `--dry-run` - Preview without uploading
- `--customer-id ID` - Customer ID (default: 2425288235)

## Implementation

```bash
cd /srv/xwander-platform/xwander.com/growth
source venv/bin/activate
python3 toolkit/hubspot_sync.py --source booking --upload [--dry-run]
```

## Conversion Action

**ID:** 7409115542
**Name:** HubSpot Deal Won
**Type:** UPLOAD_CLICKS
**Category:** PURCHASE

## Requirements

- **GCLID capture:** GTM tag 66 must be working (currently 0% capture rate)
- **HubSpot access:** HUBSPOT_ACCESS_TOKEN in environment
- **Google Ads API:** Valid credentials in google-ads.yaml
- **Attribution window:** 90 days (click to conversion)

## Expected Output

```
=== HubSpot Offline Conversion Sync ===

Querying HubSpot for closed deals (last 90 days)...
Found 21 deals worth EUR 83,188

Deals with GCLID: 0 (0.0%)
Deals without GCLID: 21 (100.0%)

⚠️ WARNING: 0% GCLID capture rate
Action required: Debug GTM tag 66

[DRY RUN] Would upload 0 conversions to Google Ads
```

## Troubleshooting

### Zero conversions uploaded

**Check:**
1. GTM tag 66 firing status
2. HubSpot hs_google_click_id field populated
3. Deals have original_source_type = PAID_SEARCH
4. Attribution window (90 days from click)

### GCLID capture issues

**Fix:**
1. Verify GTM Conversion Linker tag
2. Check GCLID localStorage persistence
3. Test form submission in GTM Preview mode
4. Confirm HubSpot Forms API field mapping

## Related Commands

- `/ads-report conversions` - Verify conversion tracking
- `/ads-pmax-list` - Check campaign performance impact

## Context

This sync enables Google Ads to attribute EUR 83K+ in revenue (21 deals in last 90 days) back to original campaigns. Critical for ROAS optimization and budget allocation.

**Status:** Script exists but GCLID capture broken (0% rate as of 2026-01-03)
