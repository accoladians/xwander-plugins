---
name: gtm-ops
description: Trigger when user mentions GTM, Tag Manager, Enhanced Conversions, or publishing. Guide through GTM operations.
version: 1.0.1
trigger:
  keywords: ["gtm", "tag manager", "enhanced conversions", "ec", "publish gtm", "gtm tags"]
  patterns: ["gtm.*publish", "enable.*ec", "list.*tags", "gtm.*sync"]
---

# GTM Operations Skill

## Purpose
Guide Claude through common Google Tag Manager operations using the xwander-gtm plugin.

## Prerequisites
- GTM credentials configured at `~/.gtm-credentials.yaml`
- xwander-gtm plugin installed
- Access to GTM container (default: 6215694602/176670340)

## Common Operations

### 1. List and Audit Tags

```bash
# List all conversion tags with Enhanced Conversions status
xw gtm list-conversion-tags

# List specific tag type
xw gtm list-tags --type gaawe

# Get detailed tag information
xw gtm get-tag --tag-id 32 --json
```

**Use when**: Auditing container configuration, checking EC status, verifying tag setup

### 2. Enable Enhanced Conversions

```bash
# Step 1: Create User-Provided Data variable (if not exists)
xw gtm create-ec-variable --name "EC - User Data"

# Step 2: Enable EC on specific tag
xw gtm enable-ec --tag-id 7 --variable-name "EC - User Data"

# Step 3: Create version
xw gtm create-version --name "v40 - Enable Enhanced Conversions" \
    --notes "Enabled EC on conversion tags via xwander-gtm plugin"

# Step 4: Publish
xw gtm publish --latest
```

**Use when**: Implementing Enhanced Conversions for web, fixing EC configuration

### 3. Create Data Layer Variables

```bash
# Create single variable
xw gtm create-variable --name "DLV - ecommerce.value" \
    --datalayer-name "ecommerce.value"

# Create with default value
xw gtm create-variable --name "DLV - page_type" \
    --datalayer-name "page_type" \
    --default "unknown"
```

**Use when**: Setting up ecommerce tracking, adding GA4 event parameters

### 4. Create Custom Event Triggers

```bash
# Create trigger with regex matching
xw gtm create-trigger --name "GA4 | Ecommerce Events" \
    --event "purchase|add_to_cart|remove_from_cart" \
    --regex
```

**Use when**: Setting up event tracking, creating conditional triggers

### 5. Version Management

```bash
# List all versions
xw gtm list-versions

# Create version with detailed notes
xw gtm create-version --name "v41 - Fix GCLID capture" \
    --notes "Updated GTM tag 66 to use hs_google_click_id field. Tested in Preview mode."

# Publish specific version
xw gtm publish --version-id 41

# Publish latest version
xw gtm publish --latest
```

**Use when**: Deploying changes, rolling back to previous version, auditing change history

## Python API Patterns

### Batch Operations

```python
from xwander_gtm import GTMClient, TagManager, WorkspaceManager, Publisher

# Initialize
client = GTMClient()
tag_mgr = TagManager(client)
workspace_mgr = WorkspaceManager(client)
publisher = Publisher(client)

# Enable EC on multiple tags
tag_ids = ['7', '9', '11', '20', '21', '28']
for tag_id in tag_ids:
    try:
        tag_mgr.enable_enhanced_conversions(
            '6215694602', '176670340',
            tag_id, 'User-Provided Data'
        )
        print(f"✓ Enabled EC on tag {tag_id}")
    except Exception as e:
        print(f"✗ Failed on tag {tag_id}: {e}")

# Create and publish version
version = workspace_mgr.create_version(
    '6215694602', '176670340',
    version_name='Batch EC Enable',
    notes='Enabled EC on all conversion tags'
)

publisher.publish('6215694602', '176670340', version['containerVersionId'])
```

### Complex Tag Updates

```python
from xwander_gtm import GTMClient, TagManager

client = GTMClient()
tag_mgr = TagManager(client)

# Get tag
tag = tag_mgr.get_tag('6215694602', '176670340', '32')

# Add or update linker parameter for cross-domain tracking
params = tag.get('parameter', [])

# Find existing linker parameter
linker_param = None
for i, param in enumerate(params):
    if param.get('key') == 'linker':
        linker_param = i
        break

# Create/update linker domains
domains = ['xwander.com', 'xwander.fi', 'xwander.fr', 'xwander.de', 'xwander.es']
new_linker = {
    'type': 'list',
    'key': 'linker',
    'list': [{'type': 'template', 'value': d} for d in domains]
}

if linker_param is not None:
    params[linker_param] = new_linker
else:
    params.append(new_linker)

# Update tag
tag_mgr.update_tag('6215694602', '176670340', '32', {'parameter': params})
```

## Workflow Templates

### Template 1: Enable Enhanced Conversions (Full Workflow)

1. **Audit current state**
   ```bash
   xw gtm list-conversion-tags > /tmp/gtm-conversion-tags.txt
   ```

2. **Create EC variable**
   ```bash
   xw gtm create-ec-variable --name "EC - User Data"
   ```

3. **Enable on all tags** (Python)
   ```python
   # Use batch operation pattern above
   ```

4. **Test in Preview mode** (Manual in GTM UI)

5. **Create version and publish**
   ```bash
   xw gtm create-version --name "v40 - Enable EC" --notes "Enabled Enhanced Conversions"
   xw gtm publish --latest
   ```

6. **Verify in Google Ads UI**
   - Navigate to: https://ads.google.com/aw/conversions/settings/enhanced?ocid=2425288235
   - Confirm EC status shows "Active"

### Template 2: Import Bokun GA4 Ecommerce Tracking

This is a complex multi-step operation. Use Python API:

```python
from xwander_gtm import GTMClient, VariableManager, TriggerManager, TagManager, WorkspaceManager, Publisher

client = GTMClient()
var_mgr = VariableManager(client)
trigger_mgr = TriggerManager(client)
tag_mgr = TagManager(client)
workspace_mgr = WorkspaceManager(client)
publisher = Publisher(client)

account_id = '6215694602'
container_id = '176670340'

# 1. Create folder (manual or API - not yet implemented in plugin)

# 2. Create ecommerce variables
ecommerce_vars = [
    ("DLV - ecommerce.items", "ecommerce.items"),
    ("DLV - ecommerce.value", "ecommerce.value"),
    ("DLV - ecommerce.currency", "ecommerce.currency"),
    ("DLV - ecommerce.transaction_id", "ecommerce.transaction_id"),
    # ... (14 total)
]

for name, dl_name in ecommerce_vars:
    try:
        var_mgr.create_data_layer_variable(account_id, container_id, name, dl_name)
    except Exception as e:
        print(f"Skipping {name}: {e}")

# 3. Create trigger
events = "view_item|view_item_list|select_item|add_to_cart|remove_from_cart|view_cart|begin_checkout|add_payment_info|add_shipping_info|purchase|search"
trigger = trigger_mgr.create_custom_event_trigger(
    account_id, container_id,
    "GA4 | Bokun Ecommerce Events",
    events,
    use_regex=True
)

# 4. Create GA4 Event tag (complex - requires nested parameters)
# Use TagManager.create_tag() with proper parameter structure

# 5. Create version and publish
version = workspace_mgr.create_version(
    account_id, container_id,
    "v38 - Bokun GA4 Ecommerce",
    "Imported Bokun widget GA4 ecommerce tracking"
)

publisher.publish(account_id, container_id, version['containerVersionId'])
```

## Error Handling

### Common Errors and Fixes

| Error | Exit Code | Fix |
|-------|-----------|-----|
| AuthenticationError | 3 | Re-run GTM OAuth setup |
| WorkspaceConflictError | 4 | Run `xw gtm sync-workspace` |
| PublishingError | 5 | Verify version exists, check permissions |
| RateLimitError | 2 | Wait and retry, or batch operations |
| DuplicateResourceError | 1 | Use different name or update existing |

### Error Recovery Pattern

```python
from xwander_gtm import GTMClient, WorkspaceManager
from xwander_gtm.exceptions import WorkspaceConflictError, GTMError

client = GTMClient()
workspace_mgr = WorkspaceManager(client)

try:
    version = workspace_mgr.create_version(
        '6215694602', '176670340',
        'My Version', 'Notes'
    )
except WorkspaceConflictError:
    # Sync and retry
    workspace_mgr.sync('6215694602', '176670340')
    version = workspace_mgr.create_version(
        '6215694602', '176670340',
        'My Version', 'Notes'
    )
except GTMError as e:
    print(f"Error: {e.message}")
    exit(e.exit_code)
```

## Best Practices

1. **Always sync before version creation** (auto-enabled by default)
2. **Test in Preview mode before publishing**
3. **Use descriptive version names and notes**
4. **Batch similar operations to avoid rate limits**
5. **Handle errors gracefully with proper exit codes**
6. **Verify changes in GTM UI after API operations**
7. **Keep credentials secure** (never commit to git)

## Quick Reference

**Default Container**: accounts/6215694602/containers/176670340

**Common Tag IDs**:
- Tag 32: GA4 Configuration
- Tag 66: GCLID Form Injection
- Tags 7, 9, 11, 20, 21, 28: Conversion tags

**Credentials**: `~/.gtm-credentials.yaml`

**Documentation**:
- `/srv/plugins/xwander-gtm/README.md`
- `/srv/plugins/xwander-gtm/docs/QUICK_REFERENCE.json`
- `/srv/xwander-platform/xwander.com/growth/knowledge/gtm.json`

## Related Operations

- **Google Ads**: Use `xw ads` commands for conversion tracking verification
- **GA4**: Use `xw ga4` commands for GA4 property configuration
- **HubSpot**: Coordinate with HubSpot offline conversion sync

## Troubleshooting

### Tags not firing
1. Check GTM Preview mode
2. Verify trigger configuration
3. Check tag paused status: `xw gtm get-tag --tag-id <ID>`

### Enhanced Conversions not working
1. Verify EC enabled in Google Ads UI
2. Check User-Provided Data variable exists
3. Verify tags reference correct variable
4. Test with GTM Debug mode

### Version not persisted
1. Ensure workspace synced before creation (auto-synced by default)
2. Check for compiler errors in version creation response
3. Verify version appears in `xw gtm list-versions`

### Publishing fails
1. Verify credentials have `tagmanager.publish` scope
2. Check version exists: `xw gtm list-versions`
3. Ensure no workspace conflicts: `xw gtm sync-workspace`
