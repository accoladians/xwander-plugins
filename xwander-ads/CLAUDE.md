# xwander-ads Plugin - AI Agent Guide

**Version:** 1.1.0
**Purpose:** Google Ads API operations for Performance Max campaigns
**Primary Customer:** Xwander Nordic (2425288235)
**Main Campaign:** Coolcation PMax EU (23423204148)

---

## Quick Reference

| Resource | Value |
|----------|-------|
| **Customer ID** | 2425288235 |
| **Campaign ID** | 23423204148 |
| **API Version** | v20 (default) |
| **Config** | /srv/xwander-platform/xwander.com/growth/config/google-ads.yaml |
| **Knowledge Base** | /srv/xwander-platform/xwander.com/growth/knowledge/ |

---

## Decision Tree for PMax Operations

### When to Use Each Command

```
Is this about campaigns?
├─ YES → Need to list all campaigns?
│        ├─ YES → xw ads pmax list --customer-id 2425288235 --campaigns
│        └─ NO → Need specific campaign details?
│                 └─ YES → xw ads pmax get --customer-id 2425288235 --campaign-id 23423204148
│
├─ NO → Is this about search themes/audience signals?
│       ├─ YES → What action?
│       │        ├─ List themes → xw ads pmax signals list --customer-id 2425288235 --asset-group-id ID
│       │        ├─ Add single → xw ads pmax signals add --customer-id 2425288235 --asset-group-id ID --theme "text"
│       │        ├─ Bulk add → xw ads pmax signals bulk --customer-id 2425288235 --asset-group-id ID --file themes.txt
│       │        └─ Remove → xw ads pmax signals remove --customer-id 2425288235 --resource-name "customers/..."
│       │
│       └─ NO → Need reports or analytics?
│                ├─ YES → What type?
│                │        ├─ Campaign performance → xw ads report performance --customer-id 2425288235
│                │        ├─ Conversion tracking → xw ads report conversions --customer-id 2425288235
│                │        ├─ Search terms → xw ads report search-terms --customer-id 2425288235 --campaign-id 23423204148
│                │        └─ Asset groups → xw ads report asset-groups --customer-id 2425288235 --campaign-id 23423204148
│                │
│                └─ NO → Custom GAQL query?
│                         └─ xw ads query --customer-id 2425288235 "SELECT ... LIMIT 50"
```

---

## Common Workflows

### 1. List All Campaigns

**Goal:** Get overview of all Performance Max campaigns

```bash
xw ads pmax list --customer-id 2425288235 --campaigns
```

**Output:** Campaign ID, name, status, budget, spend, impressions, clicks, conversions

**Use Case:** Daily monitoring, finding campaign IDs

---

### 2. Get Coolcation Campaign Details

**Goal:** Check specific campaign metrics

```bash
xw ads pmax get --customer-id 2425288235 --campaign-id 23423204148
```

**Output:** Full campaign details including budget, spend, target CPA/ROAS, performance metrics

**Use Case:** Performance reviews, budget checks, optimization decisions

---

### 3. List Asset Groups (Find Asset Group ID)

**Goal:** Get asset group IDs for signals/themes operations

```bash
# All asset groups
xw ads pmax list --customer-id 2425288235 --asset-groups

# For specific campaign
xw ads pmax list --customer-id 2425288235 --asset-groups --campaign-id 23423204148
```

**Output:** Asset group ID, name, campaign ID, status

**Use Case:** Before adding search themes, you need the asset group ID

---

### 4. Add Search Themes (Single)

**Goal:** Add one search theme to asset group

```bash
xw ads pmax signals add \
  --customer-id 2425288235 \
  --asset-group-id 12345678901 \
  --theme "northern lights tours"
```

**Output:** Success message with resource name

**Use Case:** Testing new theme, quick addition

---

### 5. Add Search Themes (Bulk)

**Goal:** Add multiple themes from file

**Step 1:** Create themes file (one per line)
```bash
cat > /tmp/themes.txt <<EOF
northern lights tours
arctic wilderness adventure
lapland winter holidays
aurora borealis experience
EOF
```

**Step 2:** Bulk add
```bash
xw ads pmax signals bulk \
  --customer-id 2425288235 \
  --asset-group-id 12345678901 \
  --file /tmp/themes.txt
```

**Output:** Success count and confirmation

**Use Case:** Large theme lists, seasonal updates

---

### 6. List Current Search Themes

**Goal:** See what themes are already active

```bash
xw ads pmax signals list \
  --customer-id 2425288235 \
  --asset-group-id 12345678901
```

**Output:** Numbered list of theme texts

**Use Case:** Audit before adding, avoid duplicates

---

### 7. Performance Report (Last 30 Days)

**Goal:** Campaign performance analysis

```bash
# Table format (human-readable)
xw ads report performance \
  --customer-id 2425288235 \
  --days 30

# CSV for spreadsheet
xw ads report performance \
  --customer-id 2425288235 \
  --days 30 \
  --format csv \
  --output /tmp/performance.csv
```

**Output:** Campaign name, impressions, clicks, CTR, cost, conversions, CPA

**Use Case:** Weekly/monthly reviews, stakeholder reports

---

### 8. Search Terms Report

**Goal:** See what queries triggered ads

```bash
xw ads report search-terms \
  --customer-id 2425288235 \
  --campaign-id 23423204148 \
  --days 7
```

**Output:** Search terms, impressions, clicks, conversions

**Use Case:** Theme optimization, negative keywords

---

### 9. Custom GAQL Query

**Goal:** Advanced queries not covered by reports

```bash
# From command line
xw ads query \
  --customer-id 2425288235 \
  "SELECT campaign.name, campaign.status FROM campaign WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX' LIMIT 10"

# From file
xw ads query \
  --customer-id 2425288235 \
  --file /tmp/my-query.gaql \
  --format json \
  --output /tmp/results.json
```

**IMPORTANT:** Always include `LIMIT` clause (max 10000)

**Use Case:** Complex analysis, custom reporting

---

## Error Handling Reference

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `AuthenticationError` | Missing/invalid credentials | Check google-ads.yaml config |
| `CampaignNotFoundError` | Wrong campaign ID | Use `pmax list --campaigns` to find ID |
| `AssetGroupNotFoundError` | Wrong asset group ID | Use `pmax list --asset-groups` to find ID |
| `DuplicateSignalError` | Theme already exists | Use `signals list` first, or ignore error |
| `QuotaExceededError` | API rate limit hit | Wait and retry (automatic with backoff) |
| `ValidationError` | Invalid query/parameter | Check GAQL syntax, use `--show-query` |
| `BudgetError` | Budget operation blocked | Check hooks/guardrails |

### Error Recovery Pattern

```python
from xwander_ads import get_client, pmax
from xwander_ads.exceptions import AdsError, QuotaExceededError

try:
    client = get_client()
    campaigns = pmax.list_campaigns(client, "2425288235")
except QuotaExceededError:
    # Wait and retry
    time.sleep(60)
    campaigns = pmax.list_campaigns(client, "2425288235")
except AdsError as e:
    # Log and handle gracefully
    print(f"Operation failed: {e}")
    print(f"Exit code: {e.exit_code}")
```

---

## Module Architecture

### CLI Entry Point (`xwander_ads/cli.py`)

**Function:** `main(args=None)`

- **Parameters:** `args` - Optional list for programmatic usage
- **Returns:** None (exits with status code)
- **Usage:**
  ```python
  # From CLI (via xw command)
  $ xw ads pmax list --customer-id 2425288235 --campaigns

  # Programmatically
  from xwander_ads.cli import main
  main(['pmax', 'list', '--customer-id', '2425288235', '--campaigns'])
  ```

### PMax Module (`xwander_ads/pmax/`)

**Key Functions:**

- `list_campaigns(client, customer_id, enabled_only=False)` → List[Dict]
- `get_campaign(client, customer_id, campaign_id)` → Dict
- `list_asset_groups(client, customer_id, campaign_id=None)` → List[Dict]
- `list_signals(client, customer_id, asset_group_id)` → List[Dict]
- `add_search_theme(client, customer_id, asset_group_id, theme)` → str (resource_name)
- `bulk_add_themes(client, customer_id, asset_group_id, themes)` → List[str]
- `remove_signal(client, customer_id, resource_name)` → None

### Reporting Module (`xwander_ads/reporting/`)

**Query Templates:**

- `templates.campaign_performance(days, enabled_only, limit)`
- `templates.conversion_performance(days, limit)`
- `templates.search_terms(days, campaign_id, limit)`
- `templates.asset_group_performance(campaign_id, days, limit)`

**Functions:**

- `execute_query(client, customer_id, query)` → List[Dict]
- `validate_query(query)` → None (raises ValidationError)
- `format_query(query)` → str (pretty-printed GAQL)
- `export_results(results, output_file, format)` → str (file path)

---

## AI Agent Best Practices

### 1. Always Use Default IDs

When user mentions "Coolcation campaign" or "our campaign":
- Customer ID: **2425288235**
- Campaign ID: **23423204148**

### 2. Check Asset Groups First

Before adding search themes:
```bash
# Get asset group ID
xw ads pmax list --customer-id 2425288235 --asset-groups --campaign-id 23423204148
```

### 3. Validate Before Bulk Operations

Before bulk adding themes:
1. List current themes to avoid duplicates
2. Validate theme file exists and is readable
3. Check theme count (warn if >100)

### 4. Use Appropriate Report Format

| Audience | Format | Command |
|----------|--------|---------|
| Human review | `--format table` | Default |
| Spreadsheet | `--format csv --output file.csv` | Excel/Sheets |
| API/Integration | `--format json --output file.json` | Automation |

### 5. Query Guardrails

**ALWAYS enforce:**
- `LIMIT` clause present (max 10000)
- No modification queries (INSERT/UPDATE/DELETE not supported)
- Customer ID validation (digits only, no hyphens)

### 6. Error Context

When operation fails, provide:
1. What was attempted
2. Error message
3. Suggested fix
4. Alternative approach

**Example:**
```
Failed to add search theme "northern lights tours"
Error: DuplicateSignalError - Theme already exists
Solution: Use 'xw ads pmax signals list' to see current themes
Alternative: Skip duplicate and continue with other themes
```

---

## Integration Points

### With Growth Toolkit (`/srv/xwander-platform/xwander.com/growth/toolkit/`)

The xwander-ads plugin complements toolkit scripts:

| Plugin Command | Toolkit Equivalent |
|----------------|-------------------|
| `xw ads pmax list --campaigns` | `python3 toolkit/reports.py --customer-id 2425288235` |
| `xw ads pmax signals bulk` | `python3 toolkit/pmax_audience_signals.py` |
| `xw ads report performance` | `python3 toolkit/reports.py --customer-id 2425288235 --days 7` |

**When to use plugin vs toolkit:**
- **Plugin:** Quick CLI operations, AI agent automation, interactive use
- **Toolkit:** Complex workflows, API development, testing

### With Knowledge Base (`/srv/xwander-platform/xwander.com/growth/knowledge/`)

Reference these files for context:
- `knowledge/google-ads-api-2026.md` - API patterns
- `knowledge/accounts.json` - Account IDs
- `knowledge/conversions.json` - Conversion actions
- `knowledge/coolcation-pmax-config.json` - Campaign configuration

---

## Testing Commands

### Quick Smoke Test

```bash
# Test authentication
xw ads auth test

# Test campaign listing
xw ads pmax list --customer-id 2425288235 --campaigns

# Test report generation
xw ads report performance --customer-id 2425288235 --days 7 --limit 5
```

### Full Test Suite

```bash
cd /srv/plugins/xwander-ads
source venv/bin/activate
pytest tests/ -v
```

---

## Changelog

See `CHANGELOG.md` for version history and bug fixes.

---

## Support

**Issues:** Report bugs or feature requests in plugin issues tracker
**Docs:** See `/srv/plugins/xwander-ads/docs/` for detailed guides
**API Reference:** `/srv/xwander-platform/xwander.com/growth/knowledge/google-ads-api-2026.md`

---

**Last Updated:** 2026-01-13
**Maintained by:** Xwander Platform Team
