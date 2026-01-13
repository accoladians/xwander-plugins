# xwander-gtm - AI Agent Guide

## Quick Decision Tree

```
User wants GTM changes?
├── READ operations (safe, no changes)
│   ├── List tags/variables/triggers → `list-*` commands
│   ├── Check workspace status → `workspace-status`
│   └── Validate before changes → `validate-workspace`
│
├── CREATE operations (reversible)
│   ├── Data Layer variable → `create-variable`
│   ├── EC User Data variable → `create-ec-variable`
│   ├── Custom event trigger → `create-trigger`
│   └── ALWAYS use `--dry-run` first!
│
├── UPDATE operations (reversible)
│   ├── Enable EC on tag → `enable-ec`
│   └── Python API for complex updates
│
└── PUBLISH operations (CAUTION - goes LIVE)
    ├── Preview first → `create-version --dry-run`
    ├── Create version → `create-version --name "..."`
    └── Publish → `publish --version-id N`
```

## IDs (Xwander Default Container)

| Resource | ID |
|----------|-----|
| Account | `6215694602` |
| Container | `176670340` |
| Public ID | `GTM-K8ZTWM4C` |

These are defaults - no need to specify unless working on different container.

## Common Workflows

### 1. Check Current State (Safe)
```bash
# What's in the workspace?
xw gtm workspace-status

# List conversion tags with EC status
xw gtm list-conversion-tags

# Validate before making changes
xw gtm validate-workspace
```

### 2. Create Enhanced Conversions Variable
```bash
# Preview first (ALWAYS do this)
xw gtm create-ec-variable --name "User-Provided Data" --dry-run

# Create AUTO mode (recommended for standard forms)
xw gtm create-ec-variable --name "User-Provided Data"

# Create MANUAL mode (for dataLayer)
xw gtm create-ec-variable --name "EC - Custom" --manual \
  --email-var "{{DLV - email}}" \
  --phone-var "{{DLV - phone}}"
```

### 3. Enable EC on Conversion Tags
```bash
# Check which tags need EC
xw gtm list-conversion-tags

# Enable EC on specific tag
xw gtm enable-ec --tag-id 7 --variable-name "User-Provided Data"
```

### 4. Create and Publish Version
```bash
# Preview changes (ALWAYS do this first)
xw gtm create-version --name "v44 - Enable EC" --dry-run

# Create version (runs validation automatically)
xw gtm create-version --name "v44 - Enable EC" --notes "Added EC to all conversion tags"

# Publish (CAUTION - goes LIVE immediately)
xw gtm publish --latest
```

## Error Handling

### Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ValidationError: awec variable missing 'mode' parameter` | EC variable created with wrong type | Use `create-ec-variable` (not manual API) |
| `ResourceNotFoundError` | Tag/variable/trigger doesn't exist | Check ID with `list-*` commands |
| `DuplicateResourceError` | Name already exists | Use different name or update existing |
| `RateLimitError` | Too many API calls | Wait 60 seconds, retry |
| `WorkspaceConflictError` | Someone else editing | Run `sync-workspace` first |

### Validation Before Version Creation

```bash
# Validation runs automatically with create-version
# To skip (NOT recommended):
xw gtm create-version --name "..." --skip-validation

# To run standalone validation:
xw gtm validate-workspace --json
```

## Variable Types Reference

| Type Code | Description | When to Use |
|-----------|-------------|-------------|
| `awec` | Google Ads Web Enhanced Conversions | EC User-Provided Data (CORRECT) |
| `gtes` | Google Tag Enhanced Settings | WRONG for EC - will cause compiler errors |
| `v` | Data Layer Variable | Reading dataLayer values |
| `c` | Constant | Static values |
| `jsm` | Custom JavaScript | Complex logic |

## GTM API Limits

- 100 requests / 100 seconds
- 1,500 requests / day
- Rate limit handling built into client

## Python API (For Complex Operations)

```python
from xwander_gtm import GTMClient, TagManager, VariableManager, WorkspaceManager

client = GTMClient()
tag_mgr = TagManager(client)
var_mgr = VariableManager(client)
ws_mgr = WorkspaceManager(client)

# Validate workspace
is_valid, issues = ws_mgr.validate_workspace('6215694602', '176670340')
for issue in issues:
    print(f"{issue['type']}: {issue['message']}")

# Create EC variable with MANUAL mode
var = var_mgr.create_user_data_variable(
    '6215694602', '176670340',
    name='EC - Form Data',
    auto_mode=False,
    email_var='{{DLV - email}}',
    phone_var='{{DLV - phone}}'
)
```

## When to Use Which

| Task | Use CLI | Use Python API |
|------|---------|----------------|
| List/check resources | ✅ | |
| Create single variable | ✅ | |
| Create single trigger | ✅ | |
| Enable EC on one tag | ✅ | |
| Batch operations | | ✅ |
| Complex conditional logic | | ✅ |
| Automated pipelines | | ✅ |
| Version + publish | ✅ | |

## Files Reference

| File | Purpose |
|------|---------|
| `xwander_gtm/cli.py` | CLI commands |
| `xwander_gtm/variables.py` | Variable operations (EC, DataLayer) |
| `xwander_gtm/workspace.py` | Validation, version creation |
| `xwander_gtm/tags.py` | Tag operations (EC enable) |
| `docs/API.md` | Full Python API reference |
| `docs/QUICK_REFERENCE.json` | JSON schema for AI parsing |

## Safety Checklist

Before any GTM change:
- [ ] Run `workspace-status` to see current state
- [ ] Run `validate-workspace` to catch issues
- [ ] Use `--dry-run` on create/version commands
- [ ] Test in GTM Preview mode before publish
- [ ] Only `publish` after verification
