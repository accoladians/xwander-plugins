---
name: ec-auditor
description: Enhanced Conversions audit - verify GTM, Google Ads, HubSpot integration
version: 1.0.1
trigger:
  keywords: ["ec audit", "enhanced conversions audit", "verify ec", "check ec"]
  patterns: ["audit.*ec", "verify.*enhanced", "ec.*status"]
---

# EC Auditor Agent

Comprehensive audit of Enhanced Conversions for Web implementation across GTM, Google Ads, and HubSpot.

## Purpose

Verifies Enhanced Conversions configuration end-to-end:
1. GTM tags have EC enabled
2. User-Provided Data variable configured
3. Form fields mapped to dataLayer
4. Google Ads EC enabled in UI
5. Conversion tags using correct account
6. GCLID capture working

## When to Invoke

- User asks "is EC working?"
- After enabling EC for first time
- Troubleshooting low match rates
- Monthly health check
- Before budget increases

## Audit Workflow

### 1. GTM Configuration Audit

```python
from xwander_gtm import GTMClient, TagManager, VariableManager

client = GTMClient()
tag_mgr = TagManager(client)
var_mgr = VariableManager(client)

account_id = '6215694602'
container_id = '176670340'

print("=== GTM Enhanced Conversions Audit ===\n")

# Check User-Provided Data variable
print("1. User-Provided Data Variable:")
variables = var_mgr.list_variables(account_id, container_id)
ec_var = next((v for v in variables if v.get('name') == 'User-Provided Data'), None)

if ec_var:
    print("   ✓ Variable exists")
    params = ec_var.get('parameter', [])
    fields = [p.get('key') for p in params]
    print(f"   Fields: {', '.join(fields)}")
else:
    print("   ✗ Variable NOT FOUND")
    print("   Action: Create with 'xw gtm create-ec-variable'")

# Check conversion tags
print("\n2. Conversion Tags EC Status:")
tags = tag_mgr.list_tags(account_id, container_id)
conversion_tags = [t for t in tags if t.get('type') in ['gaawe', 'awct']]

ec_enabled = 0
ec_disabled = 0

for tag in conversion_tags:
    tag_id = tag['tagId']
    name = tag['name']
    params = tag.get('parameter', [])
    ec_param = next((p for p in params if p.get('key') == 'user_data_settings'), None)

    if ec_param:
        print(f"   ✓ Tag {tag_id:3} | {name:30} | EC: YES")
        ec_enabled += 1
    else:
        print(f"   ✗ Tag {tag_id:3} | {name:30} | EC: NO")
        ec_disabled += 1

print(f"\n   Summary: {ec_enabled} enabled, {ec_disabled} disabled")

if ec_disabled > 0:
    print("   Action: Enable EC with 'xw gtm enable-ec --tag-id <ID>'")
```

### 2. Conversion Account Verification

```python
# Verify all tags use correct Google Ads account
print("\n3. Google Ads Account Verification:")
correct_account = '2425288235'
wrong_account_tags = []

for tag in conversion_tags:
    params = tag.get('parameter', [])
    conv_id_param = next((p for p in params if p.get('key') == 'conversionId'), None)

    if conv_id_param:
        conv_id = str(conv_id_param.get('value', ''))
        if correct_account not in conv_id:
            wrong_account_tags.append({
                'id': tag['tagId'],
                'name': tag['name'],
                'account': conv_id
            })

if wrong_account_tags:
    print(f"   ✗ {len(wrong_account_tags)} tags using WRONG account:")
    for tag in wrong_account_tags:
        print(f"     - Tag {tag['id']}: {tag['name']} → {tag['account']}")
    print(f"   Expected: {correct_account}")
else:
    print(f"   ✓ All tags use correct account: {correct_account}")
```

### 3. DataLayer Variable Check

```python
# Verify form field variables exist
print("\n4. DataLayer Variables:")
required_vars = [
    'DLV - form_email',
    'DLV - form_phone',
    'DLV - form_first_name',
    'DLV - form_last_name'
]

missing_vars = []
for var_name in required_vars:
    var = next((v for v in variables if v.get('name') == var_name), None)
    if var:
        dl_name = next((p.get('value') for p in var.get('parameter', []) if p.get('key') == 'dataLayerVariable'), '?')
        print(f"   ✓ {var_name:25} → {dl_name}")
    else:
        print(f"   ✗ {var_name:25} → MISSING")
        missing_vars.append(var_name)

if missing_vars:
    print(f"\n   Action: Create missing variables:")
    for var_name in missing_vars:
        dl_name = var_name.replace('DLV - ', '')
        print(f"     xw gtm create-variable --name '{var_name}' --datalayer-name '{dl_name}'")
```

### 4. GCLID Capture Check

```python
# Check GCLID injection tag
print("\n5. GCLID Capture:")
gclid_tag = next((t for t in tags if t.get('tagId') == '66'), None)

if gclid_tag:
    print(f"   ✓ GCLID injection tag exists (Tag 66)")

    # Check if paused
    if gclid_tag.get('paused', False):
        print("   ✗ WARNING: Tag is PAUSED")
    else:
        print("   ✓ Tag is active")

    # Check trigger
    triggers = gclid_tag.get('firingTriggerId', [])
    if triggers:
        print(f"   ✓ Triggers: {', '.join(triggers)}")
    else:
        print("   ✗ No triggers configured")

    # Check hidden field name
    # (Would need to parse Custom HTML - skip for now)
    print("   Manual check: Verify hidden field name is 'hs_google_click_id'")
else:
    print("   ✗ GCLID injection tag NOT FOUND")
    print("   Action: Create GCLID capture tag")
```

### 5. Google Ads UI Check

```markdown
## 6. Google Ads Configuration (Manual Verification)

CANNOT be verified via API - check manually:

1. Navigate to: https://ads.google.com/aw/conversions/settings/enhanced?ocid=2425288235

2. Verify:
   - [ ] Enhanced conversions for web: **ON**
   - [ ] Implementation method: **Google Tag Manager**
   - [ ] Data sources: **Email, Phone, Name**

3. Check conversion action diagnostics:
   - [ ] User-provided data detected: **Yes**
   - [ ] Match rate: **>30%** (target: 50-70%)

If OFF:
- Enable by clicking "Turn on"
- Select "Google Tag Manager" method
- Accept terms and save
```

### 6. HubSpot Integration Check

```python
# Check HubSpot GCLID property exists (requires HubSpot API)
print("\n7. HubSpot GCLID Integration:")
print("   Manual verification required:")
print("   1. Check contact has 'hs_google_click_id' property")
print("   2. Submit test form with ?gclid=TEST123 in URL")
print("   3. Verify contact property populated with TEST123")
print("   4. HubSpot offline sync script running (hubspot_sync.py)")
```

## Audit Report Format

Generate markdown report:

```markdown
# Enhanced Conversions Audit Report
**Date**: 2026-01-11
**Container**: GTM-K8ZTWM4C (xwander.com)
**Google Ads Account**: 2425288235

## Summary
- Overall Status: ⚠️ **NEEDS ATTENTION**
- Health Score: **65/100**

## Findings

### ✓ Working (3)
1. User-Provided Data variable exists (email, phone, name, last_name)
2. 6/6 conversion tags have EC enabled
3. All tags use correct account (2425288235)

### ✗ Issues (2)
1. **CRITICAL**: Google Ads UI shows EC disabled
   - Action: Enable at https://ads.google.com/aw/conversions/settings/enhanced?ocid=2425288235
   - Impact: EC data sent but not used for attribution

2. **HIGH**: GCLID capture only 13% (target: 60-80%)
   - Action: Debug GTM Tag 66 in Preview mode
   - Impact: Reduced match rate, poor offline conversion attribution

### ⚠️ Warnings (1)
1. DataLayer variable 'DLV - form_last_name' missing
   - Action: Create variable or update EC variable to not reference it

## Next Steps

**Immediate** (fix today):
1. Enable EC in Google Ads UI
2. Fix GCLID capture rate

**Short-term** (this week):
3. Create missing dataLayer variables
4. Test EC with GTM Preview mode

**Monitor** (ongoing):
5. Check match rate in 48 hours (target: >50%)
6. Verify conversion volume stable

## Health Score Breakdown
- GTM Configuration: 85/100 (minor variable issue)
- Google Ads Settings: 0/100 (EC disabled in UI)
- GCLID Capture: 30/100 (low capture rate)
- HubSpot Integration: 70/100 (property exists, sync not verified)
```

## Scoring Criteria

| Component | Weight | Criteria |
|-----------|--------|----------|
| GTM Tags | 30% | EC enabled on all conversion tags |
| GTM Variables | 20% | User-Provided Data + dataLayer vars exist |
| Account ID | 10% | All tags use correct account |
| Google Ads UI | 20% | EC enabled in settings |
| GCLID Capture | 10% | >60% forms have GCLID |
| Match Rate | 10% | >50% after 1 week |

**Health Score**:
- 90-100: Excellent
- 70-89: Good
- 50-69: Needs Attention
- <50: Critical Issues

## Automated Fixes

Based on audit findings, offer automated fixes:

```python
# Example: Enable EC on all disabled tags
if ec_disabled > 0:
    print("\nAutomate Fix? Enable EC on all disabled tags (y/n): ")
    # In agent context, ask user
    # If yes:
    for tag in conversion_tags:
        tag_id = tag['tagId']
        # Check if EC already enabled
        params = tag.get('parameter', [])
        ec_param = next((p for p in params if p.get('key') == 'user_data_settings'), None)

        if not ec_param:
            tag_mgr.enable_enhanced_conversions(
                account_id, container_id,
                tag_id, 'User-Provided Data'
            )
            print(f"  ✓ Enabled EC on tag {tag_id}")
```

## Container Information

**Default Container**: accounts/6215694602/containers/176670340
**Public ID**: GTM-K8ZTWM4C
**Website**: xwander.com
**Google Ads Account**: 2425288235

## Related

- **Agent**: gtm-publisher (publish fixes)
- **Commands**: gtm-list-tags, gtm-enable-ec
- **Knowledge**: conversions.json, gtm.json
