# xwander-gtm Claude Code Migration

**Version**: 1.0.1
**Date**: 2026-01-11
**Status**: COMPLETE

---

## Overview

Transformed xwander-gtm from custom plugin structure to official Claude Code native specification.

## Changes Made

### 1. Simplified plugin.json ✓

**Before** (163 lines):
```json
{
  "name": "xwander-gtm",
  "type": "operations",
  "category": "marketing",
  "entry_points": { ... },
  "commands": [ ... ],
  "modules": { ... },
  "dependencies": { ... },
  "configuration": { ... },
  "architecture": { ... }
}
```

**After** (17 lines):
```json
{
  "name": "xwander-gtm",
  "version": "1.0.1",
  "description": "Google Tag Manager API - Workspace management, publishing, Enhanced Conversions",
  "author": { ... },
  "keywords": [...],
  "commands": "./commands/",
  "skills": "./skills/",
  "agents": "./agents/",
  "hooks": "./hooks/hooks.json"
}
```

**Token savings**: 90% (from 163 → 17 lines)

---

### 2. Created Markdown Commands ✓

**Location**: `/srv/plugins/xwander-gtm/commands/`

#### Commands Created:

1. **gtm-publish.md** (156 lines)
   - Publish GTM versions to production
   - Safety checklist, verification steps
   - Common scenarios (EC, GCLID, rollback)
   - Error handling patterns

2. **gtm-list-tags.md** (138 lines)
   - List and audit conversion tags
   - EC status checking
   - Account ID verification
   - Troubleshooting guide

3. **gtm-enable-ec.md** (182 lines)
   - Enable Enhanced Conversions
   - Full workflow (create variable → enable → publish)
   - Verification checklist
   - Common issues and fixes

4. **gtm-sync.md** (122 lines)
   - Workspace synchronization
   - Conflict resolution
   - Error recovery patterns

**Format**: YAML frontmatter + natural language instructions

**Trigger system**: Keywords and regex patterns for automatic invocation

---

### 3. Fixed Skills Structure ✓

**Before**:
```
skills/gtm-ops.md (344 lines)
```

**After**:
```
skills/
└── gtm-ops/
    └── SKILL.md (344 lines + YAML frontmatter)
```

**Added frontmatter**:
```yaml
---
name: gtm-ops
description: Trigger when user mentions GTM, Tag Manager, Enhanced Conversions, or publishing
version: 1.0.1
trigger:
  keywords: ["gtm", "tag manager", "enhanced conversions", "ec"]
  patterns: ["gtm.*publish", "enable.*ec", "list.*tags"]
---
```

---

### 4. Created Agents ✓

**Location**: `/srv/plugins/xwander-gtm/agents/`

#### Agents Created:

1. **gtm-publisher.md** (215 lines)
   - Automated publishing workflow
   - Pre-publish validation
   - Version note generation
   - Post-publish verification
   - Safety guardrails

2. **ec-auditor.md** (268 lines)
   - Comprehensive EC audit
   - GTM, Google Ads, HubSpot verification
   - Health scoring (0-100)
   - Automated fix suggestions
   - Detailed audit reports

**Purpose**: Orchestrate complex multi-step workflows

---

### 5. Added Hooks ✓

**Location**: `/srv/plugins/xwander-gtm/hooks/hooks.json`

#### Hooks Implemented:

**PreToolUse**:
1. **gtm-publish-warning** - Warn before publishing to production
2. **gtm-ec-enable-info** - Remind about Google Ads UI step
3. **gtm-container-id-check** - Verify correct container

**PostToolUse**:
1. **gtm-publish-success-checklist** - Show verification steps after publish
2. **gtm-ec-enable-next-steps** - Guide user through EC workflow

**Security level**: Light (internal server, no external exposure)

---

### 6. Integrated xwander-google-auth ✓

**File**: `xwander_gtm/client.py`

**Changes**:
```python
def __init__(self, credentials_path: str = None):
    if credentials_path:
        # Legacy for backward compatibility
        self.credentials = self._load_credentials(credentials_path)
        self.service = build('tagmanager', 'v2', credentials=self.credentials)
    else:
        # Use unified xwander-google-auth (recommended)
        from xwander_google_auth import get_client
        self.service = get_client('gtm')
```

**Benefits**:
- Unified credential management across all Google APIs
- Auto-migration from legacy ~/.gtm-credentials.yaml
- Consistent error handling
- Reduced code duplication

**Backward compatibility**: Legacy credentials_path still works

---

## File Structure

```
/srv/plugins/xwander-gtm/
├── .claude-plugin/
│   └── plugin.json                    # Simplified (v1.0.1)
├── commands/
│   ├── gtm-publish.md                 # NEW
│   ├── gtm-list-tags.md               # NEW
│   ├── gtm-enable-ec.md               # NEW
│   └── gtm-sync.md                    # NEW
├── skills/
│   └── gtm-ops/
│       └── SKILL.md                   # Moved + frontmatter
├── agents/
│   ├── gtm-publisher.md               # NEW
│   └── ec-auditor.md                  # NEW
├── hooks/
│   └── hooks.json                     # NEW
├── xwander_gtm/
│   ├── client.py                      # Updated (xwander-google-auth)
│   ├── tags.py
│   ├── variables.py
│   ├── triggers.py
│   ├── workspace.py
│   ├── publishing.py
│   └── exceptions.py
├── CLAUDE_CODE_MIGRATION.md           # NEW (this file)
└── README.md
```

---

## Usage Examples

### Before (Custom Plugin)

```bash
# No markdown commands, just Python CLI
xw gtm list-conversion-tags

# Skill loaded manually
# No hooks or agents
```

### After (Claude Code Native)

```bash
# Commands automatically discovered
# Triggers: "publish gtm", "list tags", "enable ec"

# User: "publish gtm changes"
# → Hooks fire warnings
# → gtm-publisher agent invoked
# → Command markdown provides context
# → Skill guides workflow
# → Hooks show verification checklist
```

**Natural language interface**: User intent → automatic tool selection

---

## Token Efficiency

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| plugin.json | 163 lines | 17 lines | 90% |
| Command docs | N/A | 4 files | Net gain (but accessible) |
| Skills | 344 lines | 344 + 8 YAML | 2% overhead |
| Agents | N/A | 2 files | Net gain |
| Hooks | N/A | 1 file | Net gain |

**Overall**: Plugin metadata 90% smaller, functionality richer

---

## Backward Compatibility

### Python API - 100% Compatible

```python
# Old code still works
from xwander_gtm import GTMClient, TagManager

client = GTMClient("~/.gtm-credentials.yaml")  # Legacy
tag_mgr = TagManager(client)
tags = tag_mgr.list_tags('6215694602', '176670340')
```

```python
# New code (recommended)
from xwander_gtm import GTMClient, TagManager

client = GTMClient()  # Uses xwander-google-auth
tag_mgr = TagManager(client)
tags = tag_mgr.list_tags('6215694602', '176670340')
```

### CLI - 100% Compatible

```bash
# All existing commands work
xw gtm list-tags
xw gtm enable-ec --tag-id 7
xw gtm publish --latest
```

---

## Migration Checklist

- [x] Simplify plugin.json to official spec
- [x] Create 4 markdown commands
- [x] Move skill to subdirectory + add frontmatter
- [x] Create 2 agent workflows
- [x] Add hooks (light security)
- [x] Integrate xwander-google-auth
- [x] Document migration
- [x] Test backward compatibility

---

## Testing

### Verify Structure

```bash
# Check files exist
ls -la /srv/plugins/xwander-gtm/.claude-plugin/plugin.json
ls -la /srv/plugins/xwander-gtm/commands/
ls -la /srv/plugins/xwander-gtm/skills/gtm-ops/SKILL.md
ls -la /srv/plugins/xwander-gtm/agents/
ls -la /srv/plugins/xwander-gtm/hooks/hooks.json
```

### Verify JSON

```bash
# Validate plugin.json
cat /srv/plugins/xwander-gtm/.claude-plugin/plugin.json | jq .

# Validate hooks
cat /srv/plugins/xwander-gtm/hooks/hooks.json | jq .
```

### Test Python Import

```bash
cd /srv/plugins/xwander-gtm
python3 << 'EOF'
from xwander_gtm import GTMClient, TagManager

# Test unified auth
try:
    client = GTMClient()  # Should use xwander-google-auth
    print("✓ Unified auth works")
except Exception as e:
    print(f"✗ Unified auth failed: {e}")

# Test legacy auth
try:
    client = GTMClient("~/.gtm-credentials.yaml")
    print("✓ Legacy auth works")
except Exception as e:
    print(f"✗ Legacy auth failed: {e}")
EOF
```

### Test CLI

```bash
# List tags (should work as before)
xw gtm list-tags | head -5

# Check help (should show all commands)
xw gtm --help
```

---

## Next Steps

### 1. Update README.md

Add sections:
- Claude Code native plugin
- Command markdown documentation
- Agent workflows
- Hook system

### 2. Create Examples

Add examples directory:
- `examples/enable-ec-workflow.py`
- `examples/audit-container.py`
- `examples/publish-with-notes.sh`

### 3. Document Triggers

Create `docs/TRIGGERS.md`:
- List all command triggers
- Keyword patterns
- Example user intents

### 4. Integration Tests

Add tests for:
- Command markdown loading
- Skill triggers
- Agent invocation
- Hook firing

---

## Related Plugins

**Dependencies**:
- `xwander-google-auth` v1.0.0+ (unified auth)

**Related**:
- `xwander-ads` v1.0.1 (similar Claude Code structure)
- `xwander-ga4` v1.0.0 (GA4 API)

---

## References

- Claude Code Plugin Spec: (official docs)
- xwander-ads migration: `/srv/plugins/xwander-ads/CLAUDE_CODE_MIGRATION.md`
- Plugin conventions: `/srv/plugins/CONVENTIONS.md`

---

**Migration completed**: 2026-01-11
**Migrated by**: Claude Sonnet 4.5 (codex-agent)
**Status**: PRODUCTION READY
