---
name: gtm-list-tags
description: List and audit GTM tags with conversion and EC status
version: 1.0.1
trigger:
  keywords: ["list gtm tags", "gtm tags", "conversion tags", "ec status"]
  patterns: ["list.*tags", "show.*conversion", "audit.*gtm"]
---

# GTM List Tags Command

Lists Google Tag Manager tags with detailed configuration, focusing on conversion tags and Enhanced Conversions status.

## When to Use

- Auditing container configuration
- Checking Enhanced Conversions implementation
- Finding tag IDs for updates
- Verifying conversion tracking setup
- Troubleshooting tag firing issues

## Usage Patterns

### List All Conversion Tags

```bash
# Show all Google Ads conversion tags with EC status
xw gtm list-conversion-tags

# Output format:
# Tag ID | Name                        | Type  | Conv ID     | EC Enabled | Status
# 7      | Travel Package Form         | gaawe | 2425288235  | ❌ No      | LIVE
# 9      | Plan Your Holiday Form      | gaawe | 2425288235  | ❌ No      | LIVE
```

### List by Tag Type

```bash
# Google Ads conversion tags (gaawe)
xw gtm list-tags --type gaawe

# Custom HTML tags
xw gtm list-tags --type html

# All GA4 Event tags
xw gtm list-tags --type gaawe

# All tags (no filter)
xw gtm list-tags
```

### Get Detailed Tag Information

```bash
# Get single tag details (JSON output)
xw gtm get-tag --tag-id 32 --json

# Example: Get GA4 Configuration tag
xw gtm get-tag --tag-id 32

# Example: Check GCLID injection tag
xw gtm get-tag --tag-id 66
```

## Common Tag IDs (Xwander Container)

| Tag ID | Name | Purpose |
|--------|------|---------|
| 7 | Travel Package Form | Lead conversion |
| 9 | Plan Your Holiday Form | Lead conversion |
| 11 | Contact Form | Lead conversion |
| 20 | Mailto Click | Engagement |
| 21 | Tel Click | Engagement |
| 28 | Bokun Purchase | Ecommerce |
| 32 | GA4 Configuration | GA4 setup |
| 66 | GCLID Form Injection | GCLID capture |

## Python API Pattern

### Audit All Conversion Tags

```python
from xwander_gtm import GTMClient, TagManager

client = GTMClient()
tag_mgr = TagManager(client)

account_id = '6215694602'
container_id = '176670340'

# Get all tags
tags = tag_mgr.list_tags(account_id, container_id)

# Filter conversion tags
conversion_tags = [
    t for t in tags
    if t.get('type') in ['gaawe', 'awct'] and 'conversionId' in str(t)
]

# Check EC status
for tag in conversion_tags:
    tag_id = tag['tagId']
    name = tag['name']

    # Check for user_data_settings parameter
    params = tag.get('parameter', [])
    ec_param = next((p for p in params if p.get('key') == 'user_data_settings'), None)

    ec_status = "✓ Yes" if ec_param else "✗ No"

    print(f"{tag_id:3} | {name:30} | EC: {ec_status}")
```

### Find Tags by Conversion Action

```python
from xwander_gtm import GTMClient, TagManager

client = GTMClient()
tag_mgr = TagManager(client)

target_conversion_id = '7196325246'  # Bokun Purchase
tags = tag_mgr.list_tags('6215694602', '176670340')

matching_tags = []
for tag in tags:
    params = tag.get('parameter', [])
    for param in params:
        if param.get('key') == 'conversionId' and target_conversion_id in str(param.get('value')):
            matching_tags.append(tag)

for tag in matching_tags:
    print(f"Found: {tag['name']} (ID: {tag['tagId']})")
```

## Audit Scenarios

### Scenario 1: Enhanced Conversions Audit

**Task**: Check which conversion tags have EC enabled

```bash
# List conversion tags with EC status
xw gtm list-conversion-tags > /tmp/gtm-ec-audit.txt

# Review output for tags without EC
grep "❌ No" /tmp/gtm-ec-audit.txt
```

### Scenario 2: Verify Correct Account ID

**Task**: Ensure all tags use correct Google Ads account

```bash
# Get all conversion tags in JSON
xw gtm list-tags --type gaawe --json > /tmp/tags.json

# Parse for conversion IDs
python3 << 'EOF'
import json
with open('/tmp/tags.json') as f:
    tags = json.load(f)

for tag in tags:
    params = tag.get('parameter', [])
    for param in params:
        if param.get('key') == 'conversionId':
            conv_id = param.get('value')
            print(f"{tag['name']:30} | Conv ID: {conv_id}")
EOF

# Verify all show: 2425288235 (correct account)
```

### Scenario 3: Find Broken Tags

**Task**: Identify paused or misconfigured tags

```python
from xwander_gtm import GTMClient, TagManager

client = GTMClient()
tag_mgr = TagManager(client)

tags = tag_mgr.list_tags('6215694602', '176670340')

# Check for paused tags
paused = [t for t in tags if t.get('paused', False)]
print(f"Paused tags: {len(paused)}")
for tag in paused:
    print(f"  - {tag['name']} (ID: {tag['tagId']})")

# Check for tags missing trigger
no_trigger = [t for t in tags if not t.get('firingTriggerId')]
print(f"\nTags without triggers: {len(no_trigger)}")
for tag in no_trigger:
    print(f"  - {tag['name']} (ID: {tag['tagId']})")
```

## Output Formats

### CLI Output (Human-Readable)

```
Tag ID | Name                        | Type  | Conv ID     | EC Enabled | Status
-------|----------------------------|-------|-------------|------------|-------
7      | Travel Package Form         | gaawe | 2425288235  | ❌ No      | LIVE
9      | Plan Your Holiday Form      | gaawe | 2425288235  | ❌ No      | LIVE
11     | Contact Form                | gaawe | 2425288235  | ❌ No      | LIVE
```

### JSON Output (API Integration)

```json
[
  {
    "accountId": "6215694602",
    "containerId": "176670340",
    "tagId": "7",
    "name": "Travel Package Form",
    "type": "gaawe",
    "parameter": [
      {
        "type": "template",
        "key": "conversionId",
        "value": "2425288235"
      }
    ],
    "firingTriggerId": ["83"],
    "tagFiringOption": "oncePerEvent",
    "paused": false
  }
]
```

## Troubleshooting

### No Tags Found

```
Error: No tags found in container
```

**Causes**:
- Wrong container ID
- Authentication issue
- Empty workspace

**Fix**:
```bash
# Verify credentials
xw-auth test --api gtm

# Check container ID
# Default: accounts/6215694602/containers/176670340
```

### Permission Denied

```
Error: 403 Permission denied
```

**Fix**: Ensure credentials have readonly scope

```bash
xw-auth status
# Should show: tagmanager.readonly scope configured
```

## Container Information

**Default Container**: accounts/6215694602/containers/176670340
**Website**: xwander.com (GTM-K8ZTWM4C)
**Google Ads Account**: 2425288235

## Related Commands

- `xw gtm get-tag` - Get detailed tag information
- `xw gtm enable-ec` - Enable Enhanced Conversions on tag
- `xw gtm list-triggers` - List available triggers
- `xw gtm list-variables` - List available variables

## Documentation

- Plugin README: `/srv/plugins/xwander-gtm/README.md`
- GTM Knowledge: `/srv/xwander-platform/xwander.com/growth/knowledge/gtm.json`
- Conversion Config: `/srv/xwander-platform/xwander.com/growth/knowledge/conversions.json`
