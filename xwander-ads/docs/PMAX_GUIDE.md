# Performance Max Module Guide

**xwander-ads plugin v1.0.0**

Complete guide to managing Google Ads Performance Max campaigns via CLI.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Campaign Management](#campaign-management)
4. [Asset Groups](#asset-groups)
5. [Search Themes (Signals)](#search-themes-signals)
6. [API Versions](#api-versions)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## Quick Start

### Installation

```bash
cd /srv/plugins/xwander-ads
pip install -e .
```

### Test Authentication

```bash
xw ads auth test
```

### List Your Campaigns

```bash
xw ads pmax list --customer-id 2425288235 --campaigns
```

---

## Authentication

### Config File Location

The plugin searches for `google-ads.yaml` in these locations (in order):

1. `~/.google-ads.yaml` (standard)
2. `/srv/xwander-platform/.env/google-apis/google-ads.yaml`
3. `/srv/xwander-platform/tools/business-tools/google-ads.yaml`
4. `~/.google-ads/config.yaml`

### Config File Format

```yaml
developer_token: YOUR_DEVELOPER_TOKEN
client_id: YOUR_CLIENT_ID.apps.googleusercontent.com
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
login_customer_id: 2007072401  # Optional, for MCC accounts
use_proto_plus: True
```

### Test Your Auth

```bash
# Test with default config
xw ads auth test

# Test with specific config file
xw ads auth test --config /path/to/google-ads.yaml
```

**Expected Output:**
```
✓ Auth works! Found 4 accounts

Accessible accounts:
  - 2425288235
  - 5048098625
  - 5802421905
  - 9714445193
```

---

## Campaign Management

### List All Performance Max Campaigns

```bash
xw ads pmax list --customer-id 2425288235 --campaigns
```

**Output:**
```
=== Performance Max Campaigns (1) ===

  23423204148: Xwander PMax Nordic
    Status: ENABLED | Budget: EUR 150.00 | Spent: EUR 1,234.56
    Impressions: 45,678 | Clicks: 1,234 | Conversions: 56.0
```

### List Only Enabled Campaigns

```bash
xw ads pmax list --customer-id 2425288235 --campaigns --enabled-only
```

### Get Campaign Details

```bash
xw ads pmax get --customer-id 2425288235 --campaign-id 23423204148
```

**Output:**
```
=== Campaign 23423204148: Xwander PMax Nordic ===

  Status: ENABLED
  Budget: EUR 150.00
  Spent: EUR 1,234.56
  Impressions: 45,678
  Clicks: 1,234
  Conversions: 56.0
  Conversion Value: EUR 28,000.00
  Target ROAS: 4.50
```

---

## Asset Groups

### List All Asset Groups

```bash
xw ads pmax list --customer-id 2425288235 --asset-groups
```

**Output:**
```
=== Asset Groups (4) ===

  6655152002: Xwander EN
    Campaign: 23423204148 | Status: ENABLED

  6655251007: Xwander DE
    Campaign: 23423204148 | Status: ENABLED

  6655151999: Xwander FR
    Campaign: 23423204148 | Status: ENABLED

  6655250848: Xwander ES
    Campaign: 23423204148 | Status: ENABLED
```

### List Asset Groups for Specific Campaign

```bash
xw ads pmax list --customer-id 2425288235 --asset-groups --campaign-id 23423204148
```

---

## Search Themes (Signals)

Search themes help Google understand which searches are relevant to your products.

### List Search Themes

```bash
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 list
```

**Output:**
```
=== Asset Group 6655152002 Search Themes (25) ===

  1. "lapland tours"
  2. "northern lights finland"
  3. "rovaniemi activities"
  ...
```

### Add Single Search Theme

```bash
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 add --theme "midnight sun tours"
```

**Output:**
```
✓ Added search theme: "midnight sun tours"
  Resource: customers/2425288235/assetGroupSignals/6655152002~123456789
```

### Bulk Add Search Themes

**Step 1: Create themes file**

Create `themes.txt` with one theme per line:

```
lapland summer tours
midnight sun experiences
northern lights photography
husky sledding adventures
reindeer farm visits
arctic nature walks
```

**Step 2: Upload themes**

```bash
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 bulk --file themes.txt
```

**Output:**
```
Adding 6 search themes to asset group 6655152002...

✓ Successfully added 6 themes
```

### Remove Search Theme

**Step 1: List themes to get resource name**

```bash
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 list
```

**Step 2: Remove by resource name**

```bash
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 remove \
  --resource-name 'customers/2425288235/assetGroupSignals/6655152002~123456789'
```

---

## API Versions

The plugin supports multiple Google Ads API versions.

### Default Version (v20)

```bash
xw ads pmax list --customer-id 2425288235 --campaigns
```

### Use Specific Version

```bash
xw ads pmax list --customer-id 2425288235 --campaigns --api-version v22
```

### Supported Versions

- `v20` (default, stable)
- `v21` (current)
- `v22` (latest)

**Recommendation:** Use v20 for production, v22 for testing new features.

---

## Error Handling

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | None |
| 1 | Generic error | Check error message |
| 2 | Quota exceeded | Wait and retry later |
| 3 | Authentication failed | Check credentials |
| 4 | Resource not found | Verify campaign/asset group ID |
| 5 | Duplicate signal | Theme already exists (skip) |
| 6 | Invalid resource | Check resource name format |
| 7 | Budget error | Check budget configuration |
| 8 | Validation error | Fix input data |

### Common Errors

**Error: Authentication failed**

```bash
✗ Error: Authentication failed - check your refresh token
```

**Solution:** Run `xw ads auth test` to diagnose.

---

**Error: Asset group not found**

```bash
✗ Error: Asset group 6655152002 not found for customer 2425288235
```

**Solution:** Verify asset group ID with `xw ads pmax list --asset-groups`.

---

**Error: Duplicate signal**

```bash
✗ Error: Search theme 'lapland tours' already exists
```

**Solution:** This theme is already added. Use `list` to see existing themes.

---

**Error: API quota exceeded**

```bash
✗ Error: API quota exceeded - try again later
```

**Solution:** Wait a few minutes and retry. Google Ads API has rate limits.

---

## Best Practices

### Search Themes

**Quantity:**
- Add 5-25 themes per asset group
- Start with 10-15 core themes
- Expand based on performance

**Quality:**
- 2-10 words per theme
- Match user search intent
- Reflect landing page content
- Mix broad and specific themes

**Examples:**

**Good Themes:**
```
lapland winter tours
northern lights guided experiences
rovaniemi husky sledding
midnight sun photography tours
```

**Poor Themes:**
```
tours (too broad)
visit lapland finland for amazing northern lights experiences (too long)
www.xwander.com (not a search term)
cheap tours (price-focused, low quality)
```

### Campaign Management

**Regular Checks:**

1. **Weekly:** Review campaign performance
   ```bash
   xw ads pmax get --customer-id 2425288235 --campaign-id 23423204148
   ```

2. **Monthly:** Audit asset groups and signals
   ```bash
   xw ads pmax list --asset-groups
   xw ads pmax signals --asset-group-id 6655152002 list
   ```

3. **Quarterly:** Refresh search themes based on search console data

### Bulk Operations

**Before bulk upload:**

1. Test with small file (5-10 themes)
2. Verify themes are unique
3. Check for typos and formatting
4. Review existing themes to avoid duplicates

**After bulk upload:**

1. List themes to verify count
2. Check for any errors in output
3. Monitor campaign performance for 48h

---

## Xwander Platform Context

### Account Details

- **Customer ID:** 2425288235
- **Account Name:** Xwander Nordic
- **Currency:** EUR
- **Timezone:** Europe/Helsinki

### Main Campaign

- **Campaign ID:** 23423204148
- **Campaign Name:** Xwander PMax Nordic

### Asset Groups

| Language | Asset Group ID | Name |
|----------|----------------|------|
| English | 6655152002 | Xwander EN |
| German | 6655251007 | Xwander DE |
| French | 6655151999 | Xwander FR |
| Spanish | 6655250848 | Xwander ES |

### Typical Workflow

**1. Check campaign health:**
```bash
xw ads pmax get --customer-id 2425288235 --campaign-id 23423204148
```

**2. Review search themes for EN asset group:**
```bash
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 list
```

**3. Add new seasonal themes:**
```bash
# Create themes-summer.txt with summer-specific themes
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 bulk --file themes-summer.txt
```

**4. Repeat for other languages:**
```bash
# DE
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655251007 bulk --file themes-summer-de.txt

# FR
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655151999 bulk --file themes-summer-fr.txt

# ES
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655250848 bulk --file themes-summer-es.txt
```

---

## Advanced Usage

### Scripting

**Example: Add themes to all asset groups**

```bash
#!/bin/bash
CUSTOMER_ID="2425288235"
ASSET_GROUPS=("6655152002" "6655251007" "6655151999" "6655250848")

for AG_ID in "${ASSET_GROUPS[@]}"; do
  echo "Processing asset group $AG_ID..."
  xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id $AG_ID bulk --file themes-${AG_ID}.txt
done
```

### Caching (Future Feature)

```bash
# Will cache campaign data locally for faster access
xw ads pmax list --customer-id 2425288235 --campaigns --cached
```

**Status:** Not yet implemented in v1.0.0

---

## Migration from toolkit/pmax_signals.py

### Old Script
```bash
cd /srv/xwander-platform/xwander.com/growth
python3 toolkit/pmax_signals.py list --customer-id 2425288235 --asset-group 6655152002
```

### New Plugin
```bash
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 list
```

### Key Changes

1. **Command structure:** `xw ads pmax` instead of `python3 toolkit/pmax_signals.py`
2. **Flag names:** `--asset-group-id` instead of `--asset-group` (more explicit)
3. **Error handling:** Specific exit codes for automation
4. **Modularity:** Part of larger plugin ecosystem

### Compatibility

All functionality from the original script is preserved:
- ✓ List signals
- ✓ Add single theme
- ✓ Bulk add themes
- ✓ Remove signal
- ✓ Batch processing (50 themes per API call)

---

## Support

**Documentation:**
- Quick Reference: `docs/QUICK_REFERENCE.json`
- This Guide: `docs/PMAX_GUIDE.md`
- Examples: `examples/`

**Contact:**
- Platform: Xwander Platform
- Issues: Report via platform issue tracker

---

**Last Updated:** 2026-01-10
**Plugin Version:** 1.0.0
**Author:** Xwander Platform
