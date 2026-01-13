---
name: gtm-sync
description: Sync GTM workspace and resolve conflicts
version: 1.0.1
trigger:
  keywords: ["sync gtm", "gtm sync", "workspace conflict", "resolve conflict"]
  patterns: ["sync.*workspace", "resolve.*conflict", "workspace.*error"]
---

# GTM Sync Workspace Command

Synchronizes GTM workspace to resolve conflicts and ensure changes are persisted.

## When to Use

- Before creating a version (auto-synced by default)
- After making changes in GTM UI
- When getting "workspace conflict" errors
- After multiple people edit same container
- When version creation fails

## What Does Sync Do?

1. **Fetches latest changes** from GTM workspace
2. **Resolves conflicts** between local and remote state
3. **Prepares workspace** for version creation
4. **Validates container** for publishing

## Usage Patterns

### Automatic Sync (Recommended)

```bash
# Auto-syncs before version creation (default behavior)
xw gtm create-version --name "v42" --notes "Changes"

# Explicitly disable auto-sync (not recommended)
xw gtm create-version --name "v42" --notes "Changes" --no-sync
```

### Manual Sync

```bash
# Sync default workspace
xw gtm sync-workspace

# Sync specific workspace
xw gtm sync-workspace --workspace-id 123
```

### Python API

```python
from xwander_gtm import GTMClient, WorkspaceManager

client = GTMClient()
workspace_mgr = WorkspaceManager(client)

account_id = '6215694602'
container_id = '176670340'

# Sync workspace
result = workspace_mgr.sync(account_id, container_id)

print(f"Synced: {result['workspace']['name']}")
print(f"Status: {result['syncStatus']['syncError']}")
```

## Common Scenarios

### Scenario 1: Workspace Conflict Error

**Symptoms**:
```
Error: WorkspaceConflictError - Container version out of sync
Exit code: 4
```

**Cause**: Changes made in GTM UI after API started working

**Fix**:
```bash
# Sync workspace
xw gtm sync-workspace

# Retry operation
xw gtm create-version --name "v42" --notes "Changes"
```

### Scenario 2: Version Not Persisting

**Symptoms**: Version created but doesn't appear in GTM UI

**Cause**: Workspace not synced before version creation

**Fix**:
```bash
# Sync first
xw gtm sync-workspace

# Then create version
xw gtm create-version --name "v42" --notes "Changes"
```

### Scenario 3: Multiple Editors

**Situation**: Claude makes changes via API, human makes changes in GTM UI

**Workflow**:
```bash
# 1. Claude enables EC on tags via API
python3 -c "from xwander_gtm import GTMClient, TagManager; ..."

# 2. Human edits Tag 66 in GTM UI for GCLID

# 3. Sync before creating version
xw gtm sync-workspace

# 4. Create version (includes both changes)
xw gtm create-version --name "v42" --notes "EC + GCLID fix"
```

## Error Recovery Pattern

```python
from xwander_gtm import GTMClient, WorkspaceManager
from xwander_gtm.exceptions import WorkspaceConflictError

client = GTMClient()
workspace_mgr = WorkspaceManager(client)

account_id = '6215694602'
container_id = '176670340'

try:
    # Try to create version
    version = workspace_mgr.create_version(
        account_id, container_id,
        'My Version', 'Notes'
    )
except WorkspaceConflictError:
    print("Workspace conflict detected, syncing...")

    # Sync and retry
    workspace_mgr.sync(account_id, container_id)

    version = workspace_mgr.create_version(
        account_id, container_id,
        'My Version', 'Notes'
    )

print(f"Version created: {version['containerVersionId']}")
```

## Sync Status Information

After sync, GTM returns status:

```json
{
  "workspace": {
    "name": "Default Workspace",
    "workspaceId": "1"
  },
  "syncStatus": {
    "syncError": false,
    "mergeConflict": []
  }
}
```

### Sync Error Codes

| syncError | mergeConflict | Meaning |
|-----------|---------------|---------|
| false | [] | Clean sync, no issues |
| true | [] | Sync failed, retry |
| false | [...] | Conflicts resolved automatically |
| true | [...] | Manual resolution required |

## Best Practices

### 1. Let Auto-Sync Handle It

```bash
# GOOD: Auto-sync enabled (default)
xw gtm create-version --name "v42" --notes "Changes"

# BAD: Manually sync unnecessarily
xw gtm sync-workspace
xw gtm create-version --name "v42" --notes "Changes" --no-sync
```

### 2. Sync After Manual UI Changes

```bash
# After editing tags in GTM UI...
xw gtm sync-workspace

# Then proceed with API operations
python3 my_gtm_script.py
```

### 3. Check Status Before Major Operations

```python
from xwander_gtm import GTMClient, WorkspaceManager

client = GTMClient()
workspace_mgr = WorkspaceManager(client)

# Sync and check status
result = workspace_mgr.sync('6215694602', '176670340')

if result['syncStatus']['syncError']:
    print("WARNING: Sync errors detected")
    print(result['syncStatus'])
else:
    print("✓ Workspace synced successfully")
    # Proceed with operations
```

## Workspace Information

**Default Workspace**: "Default Workspace" (ID: 1)
**Container**: accounts/6215694602/containers/176670340

Most GTM containers only have one workspace (Default Workspace).

## Troubleshooting

### Sync Fails Repeatedly

```
Error: Sync failed after 3 attempts
```

**Causes**:
1. Active GTM Preview mode session
2. Pending publish operation
3. API rate limit

**Fix**:
```bash
# 1. Close all GTM Preview mode tabs
# 2. Wait 30 seconds
# 3. Retry

xw gtm sync-workspace

# If still fails, check GTM UI for active operations
```

### Permission Denied

```
Error: 403 Permission denied during sync
```

**Fix**: Ensure credentials have containerversions scope

```bash
xw-auth status
# Should show: tagmanager.edit.containerversions scope
```

### Merge Conflicts Detected

```
Warning: Merge conflicts detected in 2 resources
```

**Meaning**: GTM auto-resolved conflicts but you should verify changes

**Action**:
```bash
# List versions to see what changed
xw gtm list-versions

# Verify in GTM UI that changes look correct
# https://tagmanager.google.com/#/container/accounts/6215694602/containers/176670340/workspaces
```

## Exit Codes

| Code | Error | Meaning |
|------|-------|---------|
| 0 | Success | Workspace synced |
| 3 | AuthenticationError | Re-run OAuth setup |
| 4 | WorkspaceConflictError | Retry sync |
| 5 | Other API error | Check error message |

## Related Commands

- `xw gtm create-version` - Create version after sync
- `xw gtm list-versions` - Verify version created
- `xw gtm publish` - Publish after sync
- `xw-auth test` - Test authentication

## Documentation

- Plugin README: `/srv/plugins/xwander-gtm/README.md`
- GTM Knowledge: `/srv/xwander-platform/xwander.com/growth/knowledge/gtm.json`
- Error Handling: `/srv/plugins/xwander-gtm/docs/ERROR_HANDLING.md`
