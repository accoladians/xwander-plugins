---
name: conversion-tracking
description: Activate when user asks about conversion tracking, HubSpot sync, offline conversions, or attribution. Provides guidance on conversion setup and troubleshooting.
version: 1.0.1
---

# Conversion Tracking Skill

## Purpose

Guide Claude through conversion tracking setup, monitoring, and troubleshooting for Xwander Nordic Google Ads account.

## When to Use

Activate this skill when user mentions:
- "conversions", "conversion tracking", or "conversion actions"
- "HubSpot sync", "offline conversions", "deal won"
- "GCLID", "click ID", or "attribution"
- "enhanced conversions" or "ECL"
- Conversion rate optimization or tracking issues

## Conversion Types (Xwander Nordic)

### Active Working (3)

1. **GA4 travel_package_submit** (7397259491)
   - Type: GA4 custom event
   - Category: SUBMIT_LEAD_FORM
   - Status: Working (43 conversions/30d)
   - Bidding: YES

2. **GA4 plan_your_holiday_submit** (7397155834)
   - Type: GA4 custom event
   - Category: SUBMIT_LEAD_FORM
   - Status: Working (8 conversions/30d)
   - Bidding: YES

3. **GA4 checkout_click** (7397156296)
   - Type: GA4 custom event
   - Category: DEFAULT
   - Status: Working (1 conversion/30d)
   - Bidding: NO

### Active Broken (9)

**Critical:**
- **HubSpot Deal Won** (7409115542) - Offline sync not running (EUR 83K missing)
- **Purchase - Bokun Day Tour** (7196325246) - GTM tag not firing

See `/srv/xwander-platform/xwander.com/growth/knowledge/conversions.json` for complete list.

## How to Use

### 1. Audit Conversion Tracking

Generate conversion performance report:

```
/ads-report conversions --days 30
```

**Check for:**
- Zero-conversion actions (broken tracking)
- Duplicate conversions (GTM + GA4 double-counting)
- Missing attribution (no GCLID)
- Value discrepancies

### 2. Sync HubSpot Conversions

Upload offline conversions (Deal Won events):

```
/ads-conversion-sync
/ads-conversion-sync --dry-run
/ads-conversion-sync --source booking --days 90
```

**Expected flow:**
1. HubSpot deals closed with "Won" status
2. Script extracts GCLID from contact (hs_google_click_id)
3. Uploads to Google Ads conversion action 7409115542
4. Attributes revenue to original ad click

### 3. Troubleshoot GCLID Capture

**Current Issue (as of 2026-01-03):**
- GCLID capture: 0% (zero contacts with GCLID)
- GTM tag 66 deployed but not working
- EUR 83,188 revenue unattributed (21 deals in 90 days)

**Debug steps:**
1. Check GTM tag 66 firing status (GTM Preview mode)
2. Verify GCLID in localStorage (browser console)
3. Test form submission on xwander.com
4. Confirm HubSpot field mapping (hs_google_click_id)

**Resources:**
- GTM config: `/srv/xwander-platform/xwander.com/growth/knowledge/gtm.json`
- HubSpot config: `/srv/xwander-platform/xwander.com/growth/knowledge/hubspot.json`

### 4. Query Conversion Data

Custom GAQL queries for conversion analysis:

```sql
SELECT
  conversion_action.name,
  conversion_action.id,
  conversion_action.status,
  metrics.conversions,
  metrics.conversions_value,
  metrics.cost_per_conversion
FROM conversion_action
WHERE conversion_action.status = 'ENABLED'
ORDER BY metrics.conversions DESC
```

## Common Workflows

### Weekly Conversion Sync

```
1. /ads-conversion-sync --dry-run
2. Review deals found and GCLID capture rate
3. If > 0 deals with GCLID: /ads-conversion-sync --upload
4. Verify conversions appear in Google Ads (3h delay)
5. Check attribution in Google Ads > Conversions
```

### Fix Broken Conversion Action

```
1. /ads-report conversions --days 30
2. Identify action with 0 conversions
3. Check source (GTM tag ID or GA4 event)
4. If GTM: Review tag firing in GTM Preview
5. If GA4: Check event in GA4 DebugView
6. Fix implementation issue
7. Monitor for 48h to confirm fix
```

### Enhanced Conversions Setup

**Web (GTM):**
- Status: CONFIGURED_NOT_FIRING
- Tags with EC enabled: 9, 11, 20, 21, 28, 7
- Issue: Tags not firing (fix tag issues first)

**Leads (HubSpot):**
- Status: CONFIGURED_NOT_IMPORTING
- Method: HubSpot native ECL
- Issue: Sync script not scheduled
- Fix: Enable `/ads-conversion-sync` as cron job

## Best Practices

### Conversion Value Setup

- **Purchases:** Use transaction value (dynamic)
- **Leads:** Assign fixed value based on historical close rate
  - Tour inquiry: EUR 100 (average)
  - Plan Your Holiday: EUR 150 (high intent)
  - Contact form: EUR 50 (low intent)

### Attribution Settings

- **Model:** Data-driven (currently enabled)
- **Click window:** 90 days for purchases, 90 days for forms
- **View window:** 1 day (standard)

### Duplication Prevention

**GTM vs GA4:**
- Set GA4 conversions to SECONDARY if GTM version exists
- After fixing GTM tags, will double-count without adjustment
- Priority: GTM conversions (more reliable, richer data)

## Troubleshooting

### Zero conversions but traffic exists

**Check:**
1. Conversion tag firing (GTM Preview or GA4 DebugView)
2. Tag configuration (correct account ID: 2425288235)
3. Conversion action status (ENABLED in Google Ads)
4. Attribution window (recent conversions within window)

### GCLID capture issues

**Symptoms:**
- Offline conversions not attributing
- Zero deals with hs_google_click_id field populated
- Conversion showing but no click attribution

**Fix:**
1. Verify Conversion Linker tag fires on all pages
2. Check localStorage gclid value (browser console: `localStorage.getItem('gclid')`)
3. Confirm GTM tag 66 injects hidden field on forms
4. Test HubSpot Forms API field mapping

### HubSpot sync failing

**Check:**
1. HUBSPOT_ACCESS_TOKEN in environment
2. Google Ads API credentials valid
3. Conversion action 7409115542 exists and enabled
4. Deals have closedate within attribution window (90 days)

## Key Metrics

### Health Score (Current: 62/100)

- **Working conversions:** 3/12 (25%)
- **GTM tags firing:** 0/6 (0%)
- **GCLID capture rate:** 0% (target: 60-80%)
- **Offline sync:** Not running (EUR 83K missing)

**Priority fixes:**
1. P0: Debug GTM tags not firing
2. P0: Enable HubSpot offline sync
3. P1: Improve GCLID capture rate
4. P1: Set GA4 conversions to SECONDARY after GTM fix

## Context: Xwander Nordic

- **Customer ID:** 2425288235
- **Primary conversion:** Deal Won (purchase)
- **Lead forms:** Plan Your Holiday, Tour Inquiry, Contact
- **Transaction source:** Bokun booking widget
- **CRM:** HubSpot portal 8208470

## Related Skills

- **pmax-optimization** - Optimize campaigns based on conversion data
- **gaql-queries** - Advanced conversion analysis

## Resources

- **Conversions Reference:** /srv/xwander-platform/xwander.com/growth/knowledge/conversions.json
- **Audit Report:** /srv/xwander-platform/xwander.com/growth/audits/google-ads-conversion-audit-deep-2026-01-03.md
- **HubSpot Guide:** /srv/xwander-platform/xwander.com/growth/docs/hubspot-api-gclid-2025.md
