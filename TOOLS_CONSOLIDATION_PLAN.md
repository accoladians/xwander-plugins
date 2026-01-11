# /srv/tools Consolidation Plan - Claude Code Plugins

**Date**: 2026-01-05
**Status**: Planning Complete
**Author**: erasoppi-agent + gemini-agent + explore-agent

---

## Executive Summary

This plan outlines the consolidation of standalone tools from `/srv/tools/` and project-specific tools into the xwander Claude Code plugin marketplace at `/srv/plugins/`.

**Goal**: Make tools discoverable and usable as Claude Code skills/agents.

---

## Current State

### Existing Plugins (5)
| Plugin | Purpose | Status |
|--------|---------|--------|
| xwander-devops | Cloudflare, GitHub, infrastructure | Mature |
| xwander-rag | Knowledge base operations | Mature |
| xwander-context | Session management, checkpoints | Mature |
| xwander-google | Analytics, Ads, GTM | Mature |
| xwander-gsheet | Google Sheets abstraction | **NEW** (2026-01-05) |

### Tools to Consolidate

#### High Priority (Immediate Use)

| Tool | Location | Proposed Plugin | Effort |
|------|----------|-----------------|--------|
| gmc (Merchant Center CLI) | `/srv/tools/gmc/` | xwander-google or erasoppi-analytics | Medium |
| stock-check | `growth/purchasing/stock-check` | erasoppi-purchasing | Low |
| nordictrail-price | `growth/purchasing/nordictrail-price` | erasoppi-purchasing | Low |
| competitor-price | `growth/purchasing/competitor-price` | erasoppi-purchasing | Low |

#### Medium Priority (Nice to Have)

| Tool | Location | Proposed Plugin | Effort |
|------|----------|-----------------|--------|
| priceapi.py | `growth/tools/priceapi.py` | erasoppi-purchasing | Low |
| woo-supplier-products | `growth/tools/woo-supplier-products` | erasoppi-purchasing | Low |
| woo-sales-by-supplier | `growth/tools/woo-sales-by-supplier` | erasoppi-purchasing | Low |

#### Low Priority (Future)

| Tool | Location | Proposed Plugin | Effort |
|------|----------|-----------------|--------|
| dashboard.py | `growth/tools/dashboard.py` | erasoppi-analytics | Medium |
| ads.py | `growth/tools/ads.py` | xwander-google | High |
| merchant_api.py | `growth/tools/merchant_api.py` | xwander-google | Medium |

---

## Proposed New Plugins

### 1. erasoppi-purchasing (High Priority)

**Purpose**: Purchasing intelligence for erasoppi.fi
**Target Date**: 2026-01-12

**Structure**:
```
/srv/plugins/erasoppi-purchasing/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── stock-check.md
│   ├── supplier-pricing.md
│   ├── competitive-intelligence.md
│   └── purchase-recommendation.md
├── commands/
│   ├── stock.md
│   ├── supplier-price.md
│   └── competitor-price.md
├── tools/
│   ├── stock-check -> symlink
│   ├── nordictrail-price -> symlink
│   └── competitor-price -> symlink
└── hooks/
    └── price-backup.py
```

**Skills**:
- `stock-check` - Query WooCommerce inventory by supplier
- `supplier-pricing` - B2B pricing from Nordic Trail portal
- `competitive-intelligence` - Multi-source competitor pricing
- `purchase-recommendation` - Full purchase workflow

**Triggers**: "stock level", "out of stock", "supplier price", "competitor price", "purchase order"

### 2. erasoppi-analytics (Medium Priority)

**Purpose**: GMC, GA4, and performance analytics
**Target Date**: 2026-01-19

**Structure**:
```
/srv/plugins/erasoppi-analytics/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── gmc-analysis.md
│   ├── gmc-pricing.md
│   └── performance-reporting.md
├── commands/
│   ├── gmc-best-sellers.md
│   └── gmc-pricing.md
├── tools/
│   └── gmc -> symlink to /srv/tools/gmc
└── agents/
    └── analytics-specialist.md
```

---

## Implementation Steps

### Phase 1: erasoppi-purchasing (Week of 2026-01-06)

1. **Create plugin directory structure**
   ```bash
   mkdir -p /srv/plugins/erasoppi-purchasing/{.claude-plugin,skills,commands,tools,hooks}
   ```

2. **Create plugin.json manifest**
   - Define skills, commands, tools
   - Set configuration (database, credentials)

3. **Create skill files**
   - Write markdown files with YAML frontmatter
   - Document triggers, usage, examples

4. **Symlink existing tools**
   ```bash
   ln -s /srv/erasoppi-platform/erasoppi.fi/growth/purchasing/stock-check \
         /srv/plugins/erasoppi-purchasing/tools/stock-check
   ```

5. **Update marketplace index**
   - Add to `/srv/plugins/.claude-plugin/plugin.json`

6. **Test skills activation**
   - Verify skills trigger on relevant prompts
   - Test tool execution through skills

### Phase 2: erasoppi-analytics (Week of 2026-01-13)

1. Follow same pattern as Phase 1
2. Move GMC tool into plugin structure
3. Create analysis skills for GMC queries

### Phase 3: Cleanup (Week of 2026-01-20)

1. Archive original tool locations (symlinks remain)
2. Update CLAUDE.md files to reference plugins
3. Document plugin usage in RAG

---

## Migration Strategy

### Symlinks vs Copy

**Recommendation**: Use symlinks

**Why**:
- Tools remain in their original locations (version control intact)
- Plugin provides discovery layer only
- No code duplication
- Easy rollback

```bash
# Create symlink (preserves original location)
ln -s /srv/tools/gmc/gmc /srv/plugins/erasoppi-analytics/tools/gmc
```

### Backward Compatibility

- Keep original tool paths working
- Add skill layer on top for discoverability
- Gradual migration: skills first, then deprecate direct tool calls

---

## Skill Duplication Cleanup

### Current Issue

6 skills are duplicated between `/srv/.claude/skills/` and plugins:
- session-handoff
- checkpoint-optimizer
- context-externalization
- token-budget
- cloudflare-ops
- github-coach

### Resolution

1. Keep plugin versions as source of truth
2. Replace local copies with README pointing to plugin
3. Keep only project-specific skills local:
   - smart-delegation
   - agent-coordination
   - gdocs-formatting

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Plugins in marketplace | 7 (currently 5) |
| Tools consolidated | 10+ |
| Skill coverage | 80% of common tasks |
| Test coverage | 80%+ per plugin |

---

## Timeline

| Week | Deliverable |
|------|-------------|
| 2026-01-06 | erasoppi-purchasing plugin |
| 2026-01-13 | erasoppi-analytics plugin |
| 2026-01-20 | Skill duplication cleanup |
| 2026-01-27 | Documentation + RAG updates |

---

## Files Created/Modified

### New Plugin (this session)
- `/srv/plugins/xwander-gsheet/.claude-plugin/plugin.json`
- `/srv/plugins/xwander-gsheet/skills/gsheet-ops.md`
- `/srv/plugins/xwander-gsheet/examples/create_purchase_order.py`
- `/srv/plugins/xwander-gsheet/lib/gsheet.py` -> symlink

### Updated
- `/srv/plugins/.claude-plugin/plugin.json` - Added xwander-gsheet

### Library (Codex agent)
- `/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/lib/gsheet.py`
- `/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/lib/test_gsheet.py`

### RAG Documents
- `erasoppi/gsheet-py-v2-documentation.md`
- `ai-tools/claude-code-plugins-architecture-2026.md`

---

## Next Steps

1. [ ] Create erasoppi-purchasing plugin (Phase 1)
2. [ ] Test skill activation with purchasing prompts
3. [ ] Create erasoppi-analytics plugin (Phase 2)
4. [ ] Clean up skill duplication
5. [ ] Update all CLAUDE.md files to reference plugins
