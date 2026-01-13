---
name: gtm-enable-ec
description: Enable Enhanced Conversions for Web on GTM tags
version: 1.0.1
trigger:
  keywords: ["enable ec", "enhanced conversions", "enable enhanced conversions", "ec setup"]
  patterns: ["enable.*enhanced", "setup.*ec", "configure.*enhanced"]
---

# GTM Enable Enhanced Conversions Command

Enables Enhanced Conversions for Web on Google Ads conversion tags in GTM.

## What is Enhanced Conversions?

Enhanced Conversions improves conversion measurement accuracy by securely hashing first-party customer data (email, phone, name) and sending it to Google Ads. This enables better attribution when cookies are blocked or cross-device tracking is needed.

**Impact**: 10-15% improvement in conversion attribution accuracy (Google data 2025)

## Prerequisites

Before enabling EC:

1. **User-Provided Data variable exists** - Creates hidden field references
2. **Tags have conversion IDs** - Only works on conversion tags
3. **Google Ads EC enabled** - Must enable in Ads UI first
4. **Form data available** - Forms must collect email/phone

## Usage Patterns

### Enable on Single Tag

```bash
# Enable EC on specific tag
xw gtm enable-ec --tag-id 7 --variable-name "User-Provided Data"

# Verify
xw gtm get-tag --tag-id 7 --json | grep user_data_settings
```

### Enable on Multiple Tags (Batch)

```python
from xwander_gtm import GTMClient, TagManager

client = GTMClient()
tag_mgr = TagManager(client)

account_id = '6215694602'
container_id = '176670340'
tag_ids = ['7', '9', '11', '20', '21', '28']

for tag_id in tag_ids:
    try:
        tag_mgr.enable_enhanced_conversions(
            account_id, container_id,
            tag_id, 'User-Provided Data'
        )
        print(f"✓ Enabled EC on tag {tag_id}")
    except Exception as e:
        print(f"✗ Failed on tag {tag_id}: {e}")
```

### Full Workflow: Enable EC from Scratch

```bash
# Step 1: Create User-Provided Data variable
xw gtm create-ec-variable --name "User-Provided Data"

# Step 2: Enable EC on all conversion tags
python3 << 'EOF'
from xwander_gtm import GTMClient, TagManager, WorkspaceManager, Publisher

client = GTMClient()
tag_mgr = TagManager(client)
workspace_mgr = WorkspaceManager(client)
publisher = Publisher(client)

account_id = '6215694602'
container_id = '176670340'

# Conversion tag IDs
tag_ids = ['7', '9', '11', '20', '21', '28']

for tag_id in tag_ids:
    tag_mgr.enable_enhanced_conversions(
        account_id, container_id,
        tag_id, 'User-Provided Data'
    )
    print(f"✓ Tag {tag_id}")

# Create version
version = workspace_mgr.create_version(
    account_id, container_id,
    'v40 - Enable Enhanced Conversions',
    'Enabled EC on all conversion tags via xwander-gtm plugin'
)

print(f"✓ Version created: {version['containerVersionId']}")

# Publish
publisher.publish(account_id, container_id, version['containerVersionId'])
print(f"✓ Published!")
EOF

# Step 3: Enable in Google Ads UI
# Navigate to: https://ads.google.com/aw/conversions/settings/enhanced?ocid=2425288235
# Toggle "Enhanced conversions for web" ON

# Step 4: Test with GTM Preview mode
# Fill out form -> verify user_data parameter sent in Tag Assistant
```

## How It Works

### Before EC (Cookie-Only)

```
Ad Click -> Cookie Set -> User Converts -> Cookie Matched -> Conversion Attributed
                                           ❌ If cookie deleted = No attribution
```

### After EC (Cookie + Hashed Data)

```
Ad Click -> Cookie + GCLID -> User Converts -> Cookie OR Email Match -> Conversion Attributed
                                                ✓ Works even if cookie deleted
```

### Data Flow

1. **User fills form** - Email, phone, name entered
2. **GTM fires tag** - Conversion linker + User-Provided Data
3. **Data hashed** - SHA256 in browser before sending
4. **Google Ads receives** - GCLID + hashed email/phone
5. **Matching** - Google matches hashed data to signed-in accounts
6. **Attribution** - Conversion credited to correct campaign

## EC Variable Configuration

The `User-Provided Data` variable references form fields:

```json
{
  "type": "gaawc",
  "name": "User-Provided Data",
  "parameter": [
    {
      "type": "template",
      "key": "email_address",
      "value": "{{DLV - form_email}}"
    },
    {
      "type": "template",
      "key": "phone_number",
      "value": "{{DLV - form_phone}}"
    },
    {
      "type": "template",
      "key": "first_name",
      "value": "{{DLV - form_first_name}}"
    },
    {
      "type": "template",
      "key": "last_name",
      "value": "{{DLV - form_last_name}}"
    }
  ]
}
```

## Verification Steps

### 1. Verify GTM Configuration

```bash
# Check EC enabled on tag
xw gtm get-tag --tag-id 7 --json > /tmp/tag7.json

# Look for user_data_settings parameter
grep -A5 "user_data_settings" /tmp/tag7.json
```

Expected output:
```json
{
  "type": "template",
  "key": "user_data_settings",
  "value": "{{User-Provided Data}}"
}
```

### 2. Test in GTM Preview Mode

1. Enable Preview mode in GTM UI
2. Navigate to form page
3. Fill form with test data
4. Submit form
5. Check Tag Assistant:
   - Tag fired successfully
   - `user_data` parameter present
   - Values hashed (e.g., `em: "abc123...")`)

### 3. Verify in Google Ads

Navigate to: https://ads.google.com/aw/conversions/settings/enhanced?ocid=2425288235

**Status should show**:
- Enhanced conversions for web: **ON**
- Implementation method: **GTM**
- Data sources: **Email, Phone, Name**

### 4. Check Diagnostics

After 24-48 hours:
1. Go to conversion action
2. Click "Diagnostics"
3. Verify:
   - User-provided data detected: **Yes**
   - Match rate: **>30%** (target: 50-70%)

## Common Issues

### Issue: EC Not Firing

**Symptoms**: Preview mode shows tag fires but no user_data parameter

**Causes**:
1. Form fields not mapped to dataLayer
2. Variable name mismatch
3. Form submitted before GTM loads

**Fix**:
```bash
# Check variable exists
xw gtm list-variables | grep "User-Provided"

# Verify dataLayer variables exist
xw gtm list-variables | grep "DLV - form_"

# If missing, create them
xw gtm create-variable --name "DLV - form_email" --datalayer-name "form.email"
```

### Issue: Low Match Rate (<30%)

**Symptoms**: EC enabled but match rate below 30%

**Causes**:
1. Missing GCLID (most common)
2. Invalid email formats
3. Phone numbers not E.164 format

**Fix**:
```bash
# 1. Verify GCLID capture
xw gtm get-tag --tag-id 66  # GCLID injection tag

# 2. Check GCLID in HubSpot
# Ensure hs_google_click_id property populated

# 3. Improve phone format
# Add GTM variable to normalize phone numbers to E.164
```

### Issue: Google Ads Shows EC Disabled

**Symptoms**: GTM configured but Ads UI shows "Enhanced conversions: Off"

**Fix**: Enable in Google Ads UI (cannot be done via API)

1. Navigate to: https://ads.google.com/aw/conversions/settings/enhanced?ocid=2425288235
2. Click "Turn on" next to Enhanced conversions for web
3. Select "Google Tag Manager" as implementation method
4. Accept terms and save

## Tag IDs (Xwander Container)

| Tag ID | Name | Type | Priority |
|--------|------|------|----------|
| 7 | Travel Package Form | Lead | HIGH |
| 9 | Plan Your Holiday Form | Lead | HIGH |
| 11 | Contact Form | Lead | MEDIUM |
| 20 | Mailto Click | Engagement | LOW |
| 21 | Tel Click | Engagement | LOW |
| 28 | Bokun Purchase | Ecommerce | HIGH |

## Expected Results

**Immediate** (After publish):
- Tags show EC enabled in GTM
- Preview mode shows user_data parameter

**24-48 hours** (After deployment):
- Google Ads diagnostics show EC active
- Match rate appears in conversion action

**1-2 weeks** (After data collection):
- Match rate stabilizes (target: 50-70%)
- Conversion attribution improves 10-15%

## Container Information

**Default Container**: accounts/6215694602/containers/176670340
**Website**: xwander.com (GTM-K8ZTWM4C)
**Google Ads Account**: 2425288235

## Related Commands

- `xw gtm create-ec-variable` - Create User-Provided Data variable
- `xw gtm list-conversion-tags` - List tags to enable EC on
- `xw gtm create-version` - Create version after enabling EC
- `xw gtm publish` - Publish changes to production

## Documentation

- Plugin README: `/srv/plugins/xwander-gtm/README.md`
- EC Guide: `/srv/xwander-platform/xwander.com/growth/docs/GTM-HUBSPOT-UI-GUIDE-2025.md`
- Conversions Config: `/srv/xwander-platform/xwander.com/growth/knowledge/conversions.json`
- Google Official: https://support.google.com/google-ads/answer/11062876
