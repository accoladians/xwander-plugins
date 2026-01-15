# Search Campaigns Module Guide

**xwander-ads plugin v1.0.0**

Complete guide to managing Google Ads Search campaigns via CLI for Day Tours, Multiday Packages, and Sponsored Tickets.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Overview](#overview)
3. [Campaign Creation](#campaign-creation)
4. [Device Bid Adjustments](#device-bid-adjustments)
5. [Attribution Windows](#attribution-windows)
6. [CLI Examples](#cli-examples)
7. [API Usage Examples](#api-usage-examples)
8. [Common Patterns](#common-patterns)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

---

## Quick Start

### List Search Campaigns

```bash
xw ads search list --customer-id 2425288235
```

**Output:**
```
=== Search Campaigns (3) ===

  19830717557: Search | EN | Lapland
    Status: ENABLED | Budget: EUR 40.00 | Spent: EUR 2,345.67
    Impressions: 12,345 | Clicks: 432 | Conversions: 18.5

  22554233946: Search | EN | Other
    Status: PAUSED | Budget: EUR 20.00 | Spent: EUR 0.00
    Impressions: 0 | Clicks: 0 | Conversions: 0.0
```

### Get Campaign Details

```bash
xw ads search get --customer-id 2425288235 --campaign-id 19830717557
```

**Output:**
```
=== Search Campaign 19830717557: Search | EN | Lapland ===

  Status: ENABLED
  Budget: EUR 40.00
  Bidding: MANUAL_CPC (Enhanced CPC enabled)
  Geo Target Type: LOCATION_OF_PRESENCE
  Google Search: True
  Search Network: True
  Cost: EUR 2,345.67
  Impressions: 12,345
  Clicks: 432
  Conversions: 18.5
```

### Create New Campaign (Day Tours Example)

```bash
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Day Tours | Lapland" \
  --daily-budget-eur 50.0 \
  --target-cpa-eur 40.0 \
  --geo-target-type LOCATION_OF_PRESENCE \
  --geo-targets FINLAND \
  --languages ENGLISH FRENCH GERMAN \
  --status PAUSED
```

---

## Overview

### What is Search Campaign?

Search campaigns display your ads on Google Search results when users search for keywords related to your products. Unlike Performance Max (broad reach), Search campaigns give you precise keyword control and lower cost-per-acquisition.

### Key Use Cases at Xwander

| Product | Campaign | Geo Target | Attribution | Device Bias |
|---------|----------|-----------|-------------|------------|
| **Day Tours** | Search \| Day Tours \| {location} | LOCATION_OF_PRESENCE (tourists in Finland) | 7 days | Mobile +50% |
| **Multiday** | Search \| Multiday \| {country} | AREA_OF_INTEREST (tourists planning travel) | 90 days | Balanced |
| **Sponsored Tickets** | Search \| Tours \| {type} | PRESENCE_OR_INTEREST | 14 days | Mobile +30% |

### Geo Targeting Types Explained

**LOCATION_OF_PRESENCE** (Day Tours)
- Targets tourists **physically in Finland**
- Best for in-destination activities
- Highest conversion rate (70%+ day-of booking)
- Use case: "Husky safari TODAY from Ivalo"

**AREA_OF_INTEREST** (Multiday Packages)
- Targets tourists planning travel **from their home country**
- Best for advance bookings
- Longer attribution window (90 days)
- Use case: "Book your Arctic expedition" (search from UK, France, etc.)

**PRESENCE_OR_INTEREST** (Both)
- Targets both groups simultaneously
- Not recommended (mixes different buyer journeys)
- Use only when maintaining single campaign is critical

### Campaign Separation Benefits

**Problem:** Single campaign with 30x AOV variance (€100 Day Tours vs €3,000 Multiday) confuses Smart Bidding algorithms.

**Solution:** Separate campaigns allow:
- Distinct attribution windows (7d vs 90d)
- Precise target CPA optimization per product
- Isolated device bid adjustments
- Clear performance reporting

---

## Campaign Creation

### Basic Campaign (Manual CPC)

```bash
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Multiday | France" \
  --daily-budget-eur 75.0 \
  --geo-targets FRANCE \
  --languages FRENCH ENGLISH \
  --status PAUSED
```

**Creates:**
- EUR 75/day budget
- Manual CPC bidding (with Enhanced CPC)
- French and English language targeting
- Paused (safe for review before launch)

### Advanced Campaign (Target CPA)

```bash
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Day Tours | Ivalo" \
  --daily-budget-eur 50.0 \
  --target-cpa-eur 40.0 \
  --geo-target-type LOCATION_OF_PRESENCE \
  --geo-targets FINLAND \
  --languages ENGLISH FRENCH GERMAN \
  --status PAUSED
```

**Creates:**
- EUR 50/day budget
- Portfolio Target CPA bidding (€40 per acquisition)
- Google automatically optimizes bids to hit target CPA
- Requires conversion history (2-15 conversions in last 30 days)

### Multi-Country Campaign

```bash
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Multiday | EU Capitals" \
  --daily-budget-eur 100.0 \
  --target-cpa-eur 50.0 \
  --geo-target-type AREA_OF_INTEREST \
  --geo-targets FRANCE SPAIN GERMANY ITALY \
  --languages FRENCH SPANISH GERMAN ITALIAN \
  --status PAUSED
```

**Result:** Single campaign optimizes across all EU source markets with combined budget.

### Campaign Creation Response

```json
{
  "resource_name": "customers/2425288235/campaigns/12345678901",
  "campaign_id": "12345678901",
  "budget_id": "9876543210",
  "budget_resource": "customers/2425288235/campaignBudgets/9876543210",
  "name": "Search | Day Tours | Ivalo",
  "status": "PAUSED",
  "daily_budget_eur": 50.0,
  "target_cpa_eur": 40.0,
  "bidding_type": "TARGET_CPA",
  "bidding_strategy_id": "2468135790",
  "geo_target_type": "LOCATION_OF_PRESENCE",
  "url": "https://ads.google.com/aw/overview?campaignId=12345678901&__e=2425288235"
}
```

### Important Campaign Creation Notes

1. **Status defaults to PAUSED** - Review and test before enabling
2. **Target CPA requires conversion history** - Minimum 2-15 conversions in last 30 days
3. **Device adjustments cannot be set during creation** - Must call separately (see Device Bid Adjustments)
4. **EU political advertising flag is automatic** - Set to "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING"
5. **Network settings are hardcoded:**
   - Google Search: Enabled
   - Search Network: Enabled
   - Display Network: Disabled
   - Partner Search Network: Disabled

---

## Device Bid Adjustments

### Why Device Adjustments?

Device performance varies dramatically:

**Day Tours:** 87% mobile traffic (tourists searching on-the-go)
- Mobile: +50% bid (maximize visibility)
- Desktop: -30% bid (mostly Finnish locals checking prices)
- Tablet: Baseline (small audience)

**Multiday Packages:** 60% mobile traffic (planning searches)
- Mobile: +20% bid (still primary)
- Desktop: Baseline (detailed research)
- Tablet: Baseline (small audience)

### Set Device Adjustments

```bash
# Day Tours: Mobile-first strategy
xw ads search set-device-adjustments \
  --customer-id 2425288235 \
  --campaign-id 12345678901 \
  --mobile-modifier 1.5 \
  --desktop-modifier 0.7 \
  --tablet-modifier 1.0
```

**Output:**
```
✓ Set 3 device adjustments for campaign 12345678901
  MOBILE: 1.50 (50% higher bids)
  DESKTOP: 0.70 (30% lower bids)
  TABLET: 1.00 (no adjustment)
```

### Modifier Values Reference

| Modifier | Effect | Use Case |
|----------|--------|----------|
| 0.1 | -90% bid (almost exclude) | Device type not converting |
| 0.5 | -50% bid | Lower priority device |
| 0.7 | -30% bid | **Day Tours desktop** |
| 1.0 | No change (baseline) | Neutral device |
| 1.5 | +50% bid | **Day Tours mobile** |
| 2.0 | +100% bid (double bids) | High-priority device |
| 10.0 | +900% bid (max) | Emergency boost |

### Recommended Adjustments by Product

**Day Tours (In-destination, impulse)**
```bash
--mobile-modifier 1.5      # +50%
--desktop-modifier 0.7     # -30%
--tablet-modifier 1.0      # baseline
```

**Multiday Packages (Planning, research)**
```bash
--mobile-modifier 1.2      # +20%
--desktop-modifier 1.0     # baseline
--tablet-modifier 1.0      # baseline
```

**Sponsored Tickets (Mixed)**
```bash
--mobile-modifier 1.3      # +30%
--desktop-modifier 0.9     # -10%
--tablet-modifier 1.0      # baseline
```

### Verify Device Adjustments

```bash
xw ads search get-device-performance \
  --customer-id 2425288235 \
  --campaign-id 12345678901 \
  --date-range LAST_30_DAYS
```

**Output:**
```
=== Device Performance (Last 30 Days) ===

  MOBILE: 72.5% impressions (18,965 total)
    Clicks: 324 | Cost: EUR 890 | Conversions: 14.5

  DESKTOP: 18.2% impressions (4,756 total)
    Clicks: 78 | Cost: EUR 235 | Conversions: 2.1

  TABLET: 9.3% impressions (2,431 total)
    Clicks: 30 | Cost: EUR 87 | Conversions: 1.2
```

**Validation:** Day Tours should show 70%+ mobile impressions after adjustments.

---

## Attribution Windows

### What is Attribution Window?

Attribution window = How long after a click a conversion is counted.

**Example:** User clicks ad on Day 1, books on Day 3
- 7-day window: ✓ Conversion counted
- 3-day window: ✗ Conversion NOT counted (window closed)

### Day Tours vs Multiday

**Day Tours (7-day window)**
- 78% book within 48 hours (high urgency)
- Impulse purchasing (tourists already in Finland)
- Quick decision cycles
- **Recommendation:** 7 days click, 1 day view

**Multiday Packages (90-day window)**
- 4-5 month booking lead time (family planning)
- Advance bookings from source markets
- Complex decision cycles (multiple decision makers)
- **Recommendation:** 90 days click, 30 days view

### Update Attribution Window

```bash
# Day Tours: 7-day window
xw ads search update-attribution \
  --customer-id 2425288235 \
  --conversion-action-id 7452944340 \
  --click-lookback-days 7 \
  --view-lookback-days 1
```

**Output:**
```
✓ Updated conversion action 7452944340
  Click-through window: 7 days
  View-through window: 1 day
```

```bash
# Multiday: 90-day window
xw ads search update-attribution \
  --customer-id 2425288235 \
  --conversion-action-id 7452944343 \
  --click-lookback-days 90 \
  --view-lookback-days 30
```

### Attribution Window Ranges

| Window | Min | Max | Typical Use |
|--------|-----|-----|------------|
| Click-through | 1 day | 90 days | Day Tours (7), Multiday (90) |
| View-through | 1 day | 30 days | Branding (30), Performance (1) |

**CRITICAL:** Attribution changes affect **ALL campaigns** using this conversion action.

**Solution:** Create product-specific conversion actions:
- `Purchase - Day Tours` (7-day window)
- `Purchase - Multiday` (90-day window)
- `Purchase - Tickets` (14-day window)

### Bulk Update Multiple Conversions

```bash
xw ads search bulk-update-attributions \
  --customer-id 2425288235 \
  --updates '[
    {"conversion_action_id": "7452944340", "click_lookback_days": 7},
    {"conversion_action_id": "7452944343", "click_lookback_days": 90, "view_lookback_days": 30}
  ]'
```

---

## CLI Examples

### List Commands

**List all Search campaigns:**
```bash
xw ads search list --customer-id 2425288235
```

**List only enabled campaigns:**
```bash
xw ads search list --customer-id 2425288235 --enabled-only
```

**List with limit:**
```bash
xw ads search list --customer-id 2425288235 --limit 10
```

### Get Commands

**Get full campaign details:**
```bash
xw ads search get --customer-id 2425288235 --campaign-id 19830717557
```

**Get campaign targeting criteria (geo, language, devices):**
```bash
xw ads search get-criteria --customer-id 2425288235 --campaign-id 19830717557
```

### Create Commands

**Create basic campaign (Manual CPC):**
```bash
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Multiday | Spain" \
  --daily-budget-eur 50.0 \
  --geo-targets SPAIN \
  --languages SPANISH
```

**Create with Target CPA:**
```bash
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Day Tours | Oulu" \
  --daily-budget-eur 40.0 \
  --target-cpa-eur 35.0 \
  --geo-target-type LOCATION_OF_PRESENCE \
  --geo-targets FINLAND
```

**Create multi-country campaign:**
```bash
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Multiday | EU" \
  --daily-budget-eur 100.0 \
  --target-cpa-eur 50.0 \
  --geo-target-type AREA_OF_INTEREST \
  --geo-targets FRANCE SPAIN GERMANY ITALY \
  --languages FRENCH SPANISH GERMAN ITALIAN \
  --status PAUSED
```

### Device Adjustment Commands

**Set Day Tours device bids:**
```bash
xw ads search set-device-adjustments \
  --customer-id 2425288235 \
  --campaign-id 12345678901 \
  --mobile-modifier 1.5 \
  --desktop-modifier 0.7 \
  --tablet-modifier 1.0
```

**Get device performance:**
```bash
xw ads search get-device-performance \
  --customer-id 2425288235 \
  --campaign-id 12345678901
```

### Attribution Commands

**Update attribution for Day Tours conversion action:**
```bash
xw ads search update-attribution \
  --customer-id 2425288235 \
  --conversion-action-id 7452944340 \
  --click-lookback-days 7
```

**Update attribution for Multiday conversion action:**
```bash
xw ads search update-attribution \
  --customer-id 2425288235 \
  --conversion-action-id 7452944343 \
  --click-lookback-days 90 \
  --view-lookback-days 30
```

**Bulk update multiple actions:**
```bash
xw ads search bulk-update-attributions \
  --customer-id 2425288235 \
  --conversion-action-id 7452944340 --click-lookback-days 7 \
  --conversion-action-id 7452944343 --click-lookback-days 90
```

### Link Conversion Goals

**Link specific conversion actions to campaign:**
```bash
xw ads search link-conversions \
  --customer-id 2425288235 \
  --campaign-id 12345678901 \
  --conversion-action-ids 7452944340 7452944341 7452944342
```

---

## API Usage Examples

### Python Script: Create Day Tours Campaign

```python
from xwander_ads import get_client
from xwander_ads.search import (
    create_search_campaign,
    set_device_bid_adjustments,
    update_conversion_attribution,
    link_conversion_actions
)

# Get authenticated client
client = get_client()
customer_id = "2425288235"

# Step 1: Create campaign
campaign = create_search_campaign(
    client=client,
    customer_id=customer_id,
    name="Search | Day Tours | Lapland",
    daily_budget_eur=50.0,
    target_cpa_eur=40.0,
    geo_target_type="LOCATION_OF_PRESENCE",
    geo_targets=["FINLAND"],
    languages=["ENGLISH", "FRENCH", "GERMAN"],
    status="PAUSED"
)

campaign_id = campaign['campaign_id']
print(f"✓ Created campaign: {campaign_id}")
print(f"  URL: {campaign['url']}")

# Step 2: Set device adjustments (must be after campaign creation)
adjustments = set_device_bid_adjustments(
    client=client,
    customer_id=customer_id,
    campaign_id=campaign_id,
    mobile_modifier=1.5,   # +50%
    desktop_modifier=0.7,  # -30%
    tablet_modifier=1.0
)
print(f"✓ Set device adjustments: {adjustments['device_adjustments']}")

# Step 3: Update attribution window for Day Tours conversion action
attribution = update_conversion_attribution(
    client=client,
    customer_id=customer_id,
    conversion_action_id="7452944340",  # Day Tours purchase
    click_lookback_days=7,
    view_lookback_days=1
)
print(f"✓ Updated attribution to {attribution['click_lookback_days']} days")

# Step 4: Link Day Tours conversion actions to campaign
linked = link_conversion_actions(
    client=client,
    customer_id=customer_id,
    campaign_id=campaign_id,
    conversion_action_ids=["7452944340", "7459612447"]
)
print(f"✓ Linked {linked['linked_actions']} conversion actions")
```

### Python Script: Create Multiday Campaign

```python
from xwander_ads import get_client
from xwander_ads.search import create_search_campaign, update_conversion_attribution

client = get_client()
customer_id = "2425288235"

# Multi-country Multiday campaign
campaign = create_search_campaign(
    client=client,
    customer_id=customer_id,
    name="Search | Multiday | EU",
    daily_budget_eur=100.0,
    target_cpa_eur=50.0,
    geo_target_type="AREA_OF_INTEREST",  # Planning searches from home
    geo_targets=["FRANCE", "SPAIN", "GERMANY", "ITALY", "UNITED_KINGDOM"],
    languages=["FRENCH", "SPANISH", "GERMAN", "ITALIAN", "ENGLISH"],
    status="PAUSED"
)

campaign_id = campaign['campaign_id']

# Update Multiday conversion attribution (90 days, longer window)
update_conversion_attribution(
    client=client,
    customer_id=customer_id,
    conversion_action_id="7452944343",  # Multiday purchase
    click_lookback_days=90,
    view_lookback_days=30
)

print(f"Campaign {campaign_id} ready (Multiday, 90-day attribution)")
```

### Python Script: Get Campaign and Performance

```python
from xwander_ads.search import (
    get_search_campaign,
    get_campaign_criteria,
    get_device_performance
)

campaign = get_search_campaign(client, "2425288235", "19830717557")

print(f"Campaign: {campaign['name']}")
print(f"Status: {campaign['status']}")
print(f"Budget: EUR {campaign['budget_micros'] / 1_000_000:.2f}")
print(f"Target CPA: EUR {campaign['target_cpa_micros'] / 1_000_000:.2f}" if campaign['target_cpa_micros'] else "Target CPA: N/A")
print(f"Conversions: {campaign['conversions']:.1f}")
print(f"Conversion Value: EUR {campaign['conversions_value'] / 1_000_000:.2f}")

# Get targeting criteria
criteria = get_campaign_criteria(client, "2425288235", "19830717557")
print(f"\nGeo Targets: {len(criteria['geo_targets'])} locations")
print(f"Languages: {len(criteria['languages'])} languages")
print(f"Device Modifiers: {criteria['device_modifiers']}")

# Get device performance
perf = get_device_performance(client, "2425288235", "19830717557")
for p in perf:
    print(f"\n{p['device']}: {p['impression_share']:.1f}% impressions")
    print(f"  Clicks: {p['clicks']} | Cost: EUR {p['cost_micros'] / 1_000_000:.2f}")
    print(f"  Conversions: {p['conversions']:.1f}")
```

---

## Common Patterns

### Pattern 1: Day Tours Campaign (Complete Setup)

**Scenario:** Create and configure a complete Day Tours campaign with all optimizations.

```bash
#!/bin/bash
CUSTOMER_ID="2425288235"
LOCATION="Ivalo"
BUDGET=50.0
TARGET_CPA=40.0
DAY_TOURS_CONV="7452944340"

# Create campaign
CAMPAIGN=$(xw ads search create \
  --customer-id $CUSTOMER_ID \
  --name "Search | Day Tours | $LOCATION" \
  --daily-budget-eur $BUDGET \
  --target-cpa-eur $TARGET_CPA \
  --geo-target-type LOCATION_OF_PRESENCE \
  --geo-targets FINLAND \
  --languages ENGLISH FRENCH GERMAN \
  --status PAUSED)

CAMPAIGN_ID=$(echo $CAMPAIGN | jq -r '.campaign_id')
echo "Created campaign: $CAMPAIGN_ID"

# Set device adjustments
xw ads search set-device-adjustments \
  --customer-id $CUSTOMER_ID \
  --campaign-id $CAMPAIGN_ID \
  --mobile-modifier 1.5 \
  --desktop-modifier 0.7 \
  --tablet-modifier 1.0

# Update attribution
xw ads search update-attribution \
  --customer-id $CUSTOMER_ID \
  --conversion-action-id $DAY_TOURS_CONV \
  --click-lookback-days 7

echo "✓ Day Tours campaign ready: $CAMPAIGN_ID"
```

### Pattern 2: Multiday Campaign (EU Split)

**Scenario:** Create separate Multiday campaigns for different EU countries with country-specific languages.

```bash
#!/bin/bash
CUSTOMER_ID="2425288235"

# France
xw ads search create \
  --customer-id $CUSTOMER_ID \
  --name "Search | Multiday | France" \
  --daily-budget-eur 40.0 \
  --target-cpa-eur 50.0 \
  --geo-targets FRANCE \
  --languages FRENCH ENGLISH \
  --status PAUSED

# Spain
xw ads search create \
  --customer-id $CUSTOMER_ID \
  --name "Search | Multiday | Spain" \
  --daily-budget-eur 40.0 \
  --target-cpa-eur 50.0 \
  --geo-targets SPAIN \
  --languages SPANISH ENGLISH \
  --status PAUSED

# Germany
xw ads search create \
  --customer-id $CUSTOMER_ID \
  --name "Search | Multiday | Germany" \
  --daily-budget-eur 40.0 \
  --target-cpa-eur 50.0 \
  --geo-targets GERMANY \
  --languages GERMAN ENGLISH \
  --status PAUSED

echo "✓ Created 3 Multiday campaigns by country"
```

### Pattern 3: Sponsored Tickets Campaign

**Scenario:** Create campaigns for sponsored tickets with moderate mobile boost.

```bash
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Sponsored Tickets | Finland" \
  --daily-budget-eur 25.0 \
  --target-cpa-eur 15.0 \
  --geo-target-type LOCATION_OF_PRESENCE \
  --geo-targets FINLAND \
  --languages ENGLISH FINNISH \
  --status PAUSED
```

Then set device adjustments:

```bash
xw ads search set-device-adjustments \
  --customer-id 2425288235 \
  --campaign-id CAMPAIGN_ID \
  --mobile-modifier 1.3 \
  --desktop-modifier 0.9 \
  --tablet-modifier 1.0
```

And attribution:

```bash
xw ads search update-attribution \
  --customer-id 2425288235 \
  --conversion-action-id 7459612447 \
  --click-lookback-days 14
```

---

## Error Handling

### Exit Codes

| Code | Error | Solution |
|------|-------|----------|
| 0 | Success | None |
| 1 | Generic error | Check error message |
| 2 | Quota exceeded | Wait 5-10 minutes, retry |
| 3 | Authentication failed | Check credentials with `xw ads auth test` |
| 4 | Campaign not found | Verify campaign ID |
| 5 | Invalid parameter | Check flags and values |
| 6 | Bidding strategy issue | Ensure conversion history exists |
| 7 | API error | Check network, retry later |
| 8 | Validation error | Fix input data |

### Common Errors

**Error: Target CPA requires conversion history**

```
✗ Error: Failed to create campaign: Portfolio bidding strategy requires conversion history
```

**Solution:**
1. Use Manual CPC (no `--target-cpa-eur`) for new campaigns
2. Wait 30 days for conversion data to accumulate
3. Switch to Target CPA after hitting 15+ conversions

**Error: Campaign not found**

```
✗ Error: Campaign 99999999999 not found for customer 2425288235
```

**Solution:** Verify campaign ID with `xw ads search list --customer-id 2425288235`

**Error: Invalid geo target**

```
✗ Error: Unknown geo target: GREENLAND
```

**Solution:** Use valid country codes. Supported targets:
- FINLAND, FRANCE, SPAIN, UNITED_KINGDOM, GERMANY, ITALY, NETHERLANDS

**Error: Attribution window out of range**

```
✗ Error: click_lookback_days must be 1-90, got 120
```

**Solution:** Click-through windows: 1-90 days. View-through: 1-30 days.

---

## Best Practices

### Campaign Naming Convention

Follow Xwander standard naming:

```
Search | {Product} | {Target}

Examples:
- Search | Day Tours | Lapland
- Search | Multiday | France
- Search | Sponsored Tickets | Finland
```

### Budget Allocation

**Day Tours (In-destination):**
- Budget: €40-60/day
- Target CPA: €35-45
- Reason: High conversion rate, tourists already committed

**Multiday (Planning):**
- Budget: €40-100/day
- Target CPA: €50-80
- Reason: Longer sales cycle, needs reach across source markets

**Sponsored Tickets:**
- Budget: €20-40/day
- Target CPA: €10-20
- Reason: Lower AOV, impulse purchases

### Language Strategy

**Tourists in Finland (Day Tours):**
```
--languages ENGLISH FRENCH GERMAN SPANISH ITALIAN DUTCH
```
(Tourist languages, not Finnish locals)

**From Source Markets (Multiday):**
```
--languages FRENCH ENGLISH          # France campaign
--languages SPANISH ENGLISH         # Spain campaign
--languages GERMAN ENGLISH          # Germany campaign
```
(Local language + English as backup)

### Device Adjustment Validation

After setting device adjustments, verify performance in 3-5 days:

```bash
xw ads search get-device-performance \
  --customer-id 2425288235 \
  --campaign-id CAMPAIGN_ID \
  --date-range LAST_7_DAYS
```

**Expectations:**
- Day Tours: 70%+ mobile impressions
- Multiday: 50-60% mobile impressions
- Tickets: 60%+ mobile impressions

### Attribution Window Review

Review attribution windows quarterly or when:
- Booking patterns change (seasonal)
- Product mix changes
- New conversion tracking implemented

**Current Xwander Setup:**
- Day Tours: 7 days (high urgency)
- Multiday: 90 days (planning window)
- Tickets: 14 days (balanced)

### Geo Targeting Rules

**Day Tours:** ALWAYS use LOCATION_OF_PRESENCE
- Only targets people physically in Finland
- Highest conversion rate
- Lowest cost per acquisition

**Multiday:** Use AREA_OF_INTEREST or PRESENCE_OR_INTEREST
- Targets planning searches from source markets
- Longer attribution window needed
- Regional approach (France, Spain, Germany separately)

**Sponsored Tickets:** Use PRESENCE_OR_INTEREST
- Target both in-destination and planners
- Lower AOV, cast wider net
- Shorter attribution window

---

## Advanced Topics

### Multi-Campaign Strategy

**Recommended structure for complex portfolio:**

```
Search | Day Tours | Lapland        (LOCATION_OF_PRESENCE, 7-day)
Search | Day Tours | Oulu           (LOCATION_OF_PRESENCE, 7-day)
Search | Multiday | France          (AREA_OF_INTEREST, 90-day)
Search | Multiday | Spain           (AREA_OF_INTEREST, 90-day)
Search | Multiday | Germany         (AREA_OF_INTEREST, 90-day)
Search | Tickets | Finland          (PRESENCE_OR_INTEREST, 14-day)
```

Each campaign:
- Has product-specific conversion actions
- Uses appropriate attribution window
- Allows independent budget allocation
- Enables separate keyword strategies

### Performance Monitoring

**Weekly checklist:**

```bash
# 1. Check all campaign health
xw ads search list --customer-id 2425288235

# 2. Review device performance
for CAMPAIGN_ID in 19830717557 22554233946; do
  echo "=== Campaign $CAMPAIGN_ID ==="
  xw ads search get-device-performance \
    --customer-id 2425288235 \
    --campaign-id $CAMPAIGN_ID
done

# 3. Verify targeting criteria
xw ads search get-criteria \
  --customer-id 2425288235 \
  --campaign-id 19830717557
```

---

## Xwander Platform Context

### Account Details

- **Customer ID:** 2425288235
- **Account Name:** Xwander Nordic
- **Currency:** EUR
- **Timezone:** Europe/Helsinki

### Active Search Campaigns

| ID | Name | Budget | Status | Type |
|----|------|--------|--------|------|
| 19830717557 | Search \| EN \| Lapland | €40/day | ENABLED | Day Tours |
| 22554233946 | Search \| EN \| Other | €20/day | PAUSED | Multiday |
| 21162943407 | PMax \| EN \| Winter | €60/day | ENABLED | N/A (PMax) |

### Conversion Actions

| ID | Name | Attribution | Status |
|----|------|------------|--------|
| 7452944340 | Purchase - Day Tours | 7 days | Active |
| 7452944343 | Purchase - Multiday | 90 days | Active |
| 7459612447 | Sponsored Tickets | 14 days | Active |

---

## Troubleshooting

### Campaign Creation Hangs

If campaign creation takes >30 seconds:

```bash
# Kill and retry with simpler config
xw ads search create \
  --customer-id 2425288235 \
  --name "Search | Test" \
  --daily-budget-eur 10.0 \
  --status PAUSED
```

### Device Adjustments Not Applied

```bash
# Verify with get-device-performance AFTER 24 hours
# Google needs time to process bid adjustments
xw ads search get-device-performance \
  --customer-id 2425288235 \
  --campaign-id CAMPAIGN_ID \
  --date-range LAST_7_DAYS
```

### Attribution Changes Not Reflected

Attribution changes apply to **new conversions only**:
- Existing conversions keep original attribution
- Wait 2-3 weeks to see full impact
- Check conversion action details in Google Ads UI

---

## Support & Documentation

**Documentation:**
- Quick Reference: `docs/QUICK_REFERENCE.json`
- PMax Guide: `docs/PMAX_GUIDE.md`
- This Guide: `docs/SEARCH_GUIDE.md`
- Examples: `examples/`

**Command Help:**
```bash
xw ads search --help
xw ads search create --help
xw ads search set-device-adjustments --help
```

**API Reference:**
- `xwander_ads/search/campaigns.py` - Campaign operations
- `xwander_ads/search/adjustments.py` - Device bids, attribution

---

**Last Updated:** 2026-01-15
**Plugin Version:** 1.0.0
**Author:** Xwander Platform
**Status:** Production Ready
