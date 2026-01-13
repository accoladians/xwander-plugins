---
name: gtm-publish
description: Publish GTM container version to production
version: 1.0.1
trigger:
  keywords: ["publish gtm", "deploy gtm", "gtm publish", "go live"]
  patterns: ["publish.*version", "deploy.*container"]
---

# GTM Publish Command

Publishes a Google Tag Manager container version to production.

## When to Use

- After testing changes in GTM Preview mode
- When workspace changes are ready for production
- Rolling back to a previous version
- Deploying Enhanced Conversions configuration

## Safety Checklist

Before publishing, ALWAYS verify:

1. **Preview Mode Testing** - All tags fire correctly in GTM Preview
2. **Version Notes** - Meaningful description of changes
3. **No Active Issues** - No workspace conflicts or errors
4. **Stakeholder Approval** - For major changes (EC, new tracking)

## Usage Patterns

### Publish Latest Version

```bash
# Create version from current workspace
xw gtm create-version --name "v42 - Fix GCLID capture" \
    --notes "Updated Tag 66 to inject hs_google_click_id field"

# Publish latest version
xw gtm publish --latest
```

### Publish Specific Version

```bash
# List available versions
xw gtm list-versions

# Publish specific version by ID
xw gtm publish --version-id 41
```

### Full Workflow (Python)

```python
from xwander_gtm import GTMClient, WorkspaceManager, Publisher

client = GTMClient()
workspace_mgr = WorkspaceManager(client)
publisher = Publisher(client)

account_id = '6215694602'
container_id = '176670340'

# Create version
version = workspace_mgr.create_version(
    account_id, container_id,
    version_name='v42 - Enhanced Conversions',
    notes='Enabled EC on all conversion tags. Tested in Preview mode.'
)

print(f"Created version {version['containerVersionId']}")

# Publish
result = publisher.publish(
    account_id, container_id,
    version['containerVersionId']
)

print(f"Published: {result['containerVersion']['name']}")
```

## Common Scenarios

### Scenario 1: Enable Enhanced Conversions

**Task**: Enable EC on conversion tags and publish

```bash
# 1. Enable EC on tags (use Python API for batch)
python3 << 'EOF'
from xwander_gtm import GTMClient, TagManager, WorkspaceManager, Publisher

client = GTMClient()
tag_mgr = TagManager(client)
workspace_mgr = WorkspaceManager(client)
publisher = Publisher(client)

account_id = '6215694602'
container_id = '176670340'
tag_ids = ['7', '9', '11', '20', '21', '28']

for tag_id in tag_ids:
    tag_mgr.enable_enhanced_conversions(
        account_id, container_id, tag_id,
        'User-Provided Data'
    )
    print(f"✓ Enabled EC on tag {tag_id}")

version = workspace_mgr.create_version(
    account_id, container_id,
    'v40 - Enable Enhanced Conversions',
    'Enabled EC on all conversion tags via xwander-gtm plugin'
)

publisher.publish(account_id, container_id, version['containerVersionId'])
print(f"✓ Published version {version['containerVersionId']}")
EOF

# 2. Verify in Google Ads UI
# Navigate to: https://ads.google.com/aw/conversions/settings/enhanced?ocid=2425288235
```

### Scenario 2: Fix GCLID Capture

**Task**: Update hidden field injection and publish

```bash
# After manually editing Tag 66 in GTM UI...

# Create version
xw gtm create-version --name "v34 - Fix GCLID field name" \
    --notes "Changed hidden field from 'gclid' to 'hs_google_click_id' for HubSpot native property"

# Publish
xw gtm publish --latest

# Verify with test form submission
# Check HubSpot contact has hs_google_click_id populated
```

### Scenario 3: Rollback to Previous Version

**Task**: Something broke, rollback to last known good

```bash
# List versions
xw gtm list-versions

# Publish previous version (e.g., v40 if v41 broke)
xw gtm publish --version-id 40
```

## Container Information

**Default Container**: accounts/6215694602/containers/176670340
**Website**: xwander.com (GTM-K8ZTWM4C)
**Google Ads Account**: 2425288235

## Verification Steps

After publishing:

1. **GTM UI** - Verify version shows as "Published" in GTM versions list
2. **Live Website** - Check source for updated GTM container version
3. **GTM Debug Mode** - Enable debug mode on live site, verify tags fire
4. **Google Ads** - Check conversion tracking status (if EC changes)
5. **GA4 DebugView** - Verify events arrive correctly (if GA4 changes)

## Error Handling

### Authentication Error (Exit 3)

```
Error: Authentication failed during publish version
```

**Fix**: Re-run OAuth setup

```bash
xw-auth setup --api gtm --force
```

### Publishing Error (Exit 5)

```
Error: Version not found
```

**Fix**: Verify version exists

```bash
xw gtm list-versions
```

### Workspace Conflict (Exit 4)

```
Error: Workspace has conflicts
```

**Fix**: Sync workspace

```bash
xw gtm sync-workspace
```

## Related Commands

- `xw gtm create-version` - Create version before publishing
- `xw gtm list-versions` - List available versions
- `xw gtm sync-workspace` - Resolve workspace conflicts
- `xw gtm list-conversion-tags` - Audit conversion tags before changes

## Documentation

- Plugin README: `/srv/plugins/xwander-gtm/README.md`
- GTM Knowledge: `/srv/xwander-platform/xwander.com/growth/knowledge/gtm.json`
- GTM UI Guide: `/srv/xwander-platform/xwander.com/growth/docs/GTM-HUBSPOT-UI-GUIDE-2025.md`
