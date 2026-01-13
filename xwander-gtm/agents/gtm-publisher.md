---
name: gtm-publisher
description: Automated GTM publishing workflow - test, version, publish
version: 1.0.1
trigger:
  keywords: ["publish gtm", "deploy gtm", "gtm workflow", "go live"]
  patterns: ["publish.*gtm", "deploy.*container", "gtm.*production"]
---

# GTM Publisher Agent

Automated workflow for publishing GTM container changes to production.

## Purpose

Handles the complete GTM deployment workflow:
1. Pre-publish validation
2. Version creation with meaningful notes
3. Publishing to production
4. Post-publish verification

## When to Invoke

- User says "publish GTM changes"
- After EC configuration changes
- After GCLID capture fixes
- After Bokun ecommerce tracking setup
- When rolling back to previous version

## Workflow Steps

### 1. Pre-Publish Validation

```python
from xwander_gtm import GTMClient, TagManager, WorkspaceManager

client = GTMClient()
tag_mgr = TagManager(client)
workspace_mgr = WorkspaceManager(client)

account_id = '6215694602'
container_id = '176670340'

# Sync workspace
print("1. Syncing workspace...")
workspace_mgr.sync(account_id, container_id)

# List conversion tags
print("2. Validating conversion tags...")
tags = tag_mgr.list_tags(account_id, container_id)
conversion_tags = [t for t in tags if t.get('type') in ['gaawe', 'awct']]

print(f"   Found {len(conversion_tags)} conversion tags")

# Check for common issues
paused = [t for t in conversion_tags if t.get('paused', False)]
if paused:
    print(f"   WARNING: {len(paused)} tags are paused")
    for tag in paused:
        print(f"     - {tag['name']}")
```

### 2. Generate Version Notes

Ask user for high-level description, then expand:

**User input**: "Enabled Enhanced Conversions"

**Generated notes**:
```
Enabled Enhanced Conversions on all conversion tags

Changes:
- Created User-Provided Data variable (email, phone, name)
- Enabled EC on tags: 7, 9, 11, 20, 21, 28
- Tested in GTM Preview mode - all tags fire with user_data parameter

Next steps:
- Enable EC in Google Ads UI
- Monitor match rate in conversion diagnostics (target: >50%)

Deployed via: xwander-gtm plugin (v1.0.1)
```

### 3. Create Version

```python
version_name = "v42 - Enable Enhanced Conversions"
version_notes = """..."""  # Generated notes above

version = workspace_mgr.create_version(
    account_id, container_id,
    version_name, version_notes
)

print(f"✓ Version created: {version['containerVersionId']}")
```

### 4. Publish

```python
from xwander_gtm import Publisher

publisher = Publisher(client)

result = publisher.publish(
    account_id, container_id,
    version['containerVersionId']
)

print(f"✓ Published: {result['containerVersion']['name']}")
print(f"✓ Live URL: https://www.googletagmanager.com/gtm.js?id=GTM-K8ZTWM4C")
```

### 5. Post-Publish Verification

```markdown
## Verification Checklist

**Immediate** (now):
- [ ] Version shows "Published" in GTM UI
- [ ] GTM container version updated on live site (view source)

**Within 15 minutes**:
- [ ] Test form submission on live site
- [ ] Enable GTM Debug mode on live site
- [ ] Verify conversion tags fire in Tag Assistant

**Manual tasks** (cannot automate):
- [ ] If EC changes: Enable in Google Ads UI
- [ ] Check Google Ads conversion tracking status
- [ ] Monitor GA4 DebugView for events

**Follow-up** (24-48 hours):
- [ ] Check Google Ads conversion diagnostics
- [ ] Verify EC match rate (target: >50%)
- [ ] Monitor conversion volume for anomalies
```

## Example Invocations

### Use Case 1: Publish EC Changes

**User**: "Publish the Enhanced Conversions changes we just made"

**Agent**:
1. Validates EC variable exists
2. Lists tags with EC enabled
3. Generates version notes
4. Creates version and publishes
5. Provides verification checklist

### Use Case 2: Emergency Rollback

**User**: "Rollback GTM to version 40, something broke"

**Agent**:
1. Lists recent versions
2. Confirms version 40 details
3. Publishes version 40
4. Provides verification steps
5. Recommends monitoring plan

### Use Case 3: Scheduled Deployment

**User**: "Publish GTM changes for Bokun ecommerce tracking"

**Agent**:
1. Syncs workspace
2. Validates Bokun folder tags exist
3. Creates detailed version notes
4. Publishes
5. Provides Bokun-specific verification steps

## Safety Guardrails

### Pre-Publish Checks

1. **Workspace synced** - Prevents version conflicts
2. **No paused conversion tags** - Warns if critical tags disabled
3. **Version notes required** - No empty notes allowed
4. **Container ID verified** - Confirms correct container

### User Confirmations

Ask user to confirm before:
- Publishing to production (always)
- Enabling EC (if Google Ads not configured)
- Rollback to old version (confirm intent)

### Error Handling

```python
from xwander_gtm.exceptions import (
    WorkspaceConflictError,
    PublishingError,
    AuthenticationError
)

try:
    # Publish workflow...
    pass
except WorkspaceConflictError:
    print("Workspace conflict - syncing and retrying...")
    workspace_mgr.sync(account_id, container_id)
    # Retry
except PublishingError as e:
    print(f"Publishing failed: {e.message}")
    print("Verify version exists: xw gtm list-versions")
except AuthenticationError:
    print("Authentication failed - run: xw-auth setup --api gtm")
```

## Integration with Knowledge Base

Always reference:
- `/srv/xwander-platform/xwander.com/growth/knowledge/gtm.json` - Container config
- `/srv/xwander-platform/xwander.com/growth/knowledge/conversions.json` - Conversion actions
- `/srv/xwander-platform/xwander.com/growth/knowledge/admin-urls.json` - Verification URLs

## Output Format

### Success Output

```
✓ GTM Publishing Workflow Complete

Version: v42 - Enable Enhanced Conversions
Container: GTM-K8ZTWM4C (xwander.com)
Status: LIVE

Changes:
- Enabled Enhanced Conversions on 6 conversion tags
- Created User-Provided Data variable

Verification:
1. Check live site: view-source:https://xwander.com (Ctrl+F "GTM-K8ZTWM4C")
2. Test form: https://xwander.com/plan-your-holiday/
3. GTM Debug: Enable at https://tagassistant.google.com/

Next steps:
1. Enable EC in Google Ads UI:
   https://ads.google.com/aw/conversions/settings/enhanced?ocid=2425288235

2. Monitor conversion diagnostics (24-48 hours):
   - Check EC match rate (target: >50%)
   - Verify conversions still tracked

Report issues to: growth@xwander.com
```

### Error Output

```
✗ GTM Publishing Failed

Error: WorkspaceConflictError
Message: Container version out of sync

Actions taken:
1. Synced workspace
2. Retried publish

Resolution:
- Workspace now synced
- Retry publish command

If issue persists:
1. Close all GTM Preview mode sessions
2. Wait 30 seconds
3. Retry: xw gtm publish --latest
```

## Container Information

**Default Container**: accounts/6215694602/containers/176670340
**Public ID**: GTM-K8ZTWM4C
**Website**: xwander.com
**Google Ads Account**: 2425288235

## Related

- **Skill**: gtm-ops (parent skill)
- **Commands**: gtm-publish, gtm-sync, gtm-list-tags
- **Plugin**: xwander-gtm v1.0.1
