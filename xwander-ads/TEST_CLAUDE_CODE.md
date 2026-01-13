# Claude Code Plugin Test Checklist

**Plugin:** xwander-ads v1.0.1
**Test Date:** 2026-01-11
**Status:** Ready for testing

---

## 1. Plugin Discovery

### Verify Plugin Loaded

```
claude> list plugins
```

Expected: xwander-ads appears in list

### Verify Commands Available

```
claude> /ads-
```

Expected: Autocomplete shows all 5 commands:
- `/ads-pmax-list`
- `/ads-pmax-signals`
- `/ads-report`
- `/ads-conversion-sync`
- `/ads-query`

---

## 2. Command Testing

### Test: List Performance Max Campaigns

```
claude> /ads-pmax-list
```

**Expected behavior:**
1. Claude reads `/srv/plugins/xwander-ads/commands/ads-pmax-list.md`
2. Sets PYTHONPATH and executes Python CLI
3. Returns formatted campaign list with metrics

**Expected output format:**
```
=== Performance Max Campaigns (2) ===

23423204148: Xwander PMax Nordic
  Status: ENABLED | Budget: EUR 100.00 | Spent: EUR 45.67
  Impressions: 12,345 | Clicks: 456 | Conversions: 23.0
```

### Test: List Search Themes

```
claude> /ads-pmax-signals list --asset-group-id 6655152002
```

**Expected behavior:**
1. Reads command markdown
2. Executes Python CLI with correct parameters
3. Returns theme list

**Expected output format:**
```
=== Asset Group 6655152002 Search Themes (18) ===

  1. "northern lights tours"
  2. "husky sledding lapland"
  ...
```

### Test: Add Search Theme

```
claude> /ads-pmax-signals add --asset-group-id 6655152002 --theme "test theme from claude code"
```

**Expected behavior:**
1. Command executed
2. Success message displayed
3. Hook fires: "✅ Search themes added successfully..."

### Test: Generate Report

```
claude> /ads-report performance --days 7
```

**Expected behavior:**
1. Report generated with 7-day metrics
2. Formatted output displayed

### Test: Custom Query

```
claude> /ads-query "SELECT campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS LIMIT 5"
```

**Expected behavior:**
1. GAQL query executed
2. Results formatted and displayed

---

## 3. Skill Activation Testing

### Test: PMax Optimization Skill

**Trigger phrase:**
```
claude> I need to optimize our Performance Max campaigns
```

**Expected behavior:**
1. pmax-optimization skill activates
2. Claude mentions skill is loaded
3. Follows skill workflow (list campaigns → analyze → recommend)
4. Uses commands from skill: `/ads-pmax-list`, `/ads-pmax-signals`

**Verification:**
- [ ] Skill activates automatically
- [ ] Claude follows skill process
- [ ] Commands executed as per skill guidance

### Test: Conversion Tracking Skill

**Trigger phrase:**
```
claude> Can you check if our conversion tracking is working correctly?
```

**Expected behavior:**
1. conversion-tracking skill activates
2. Claude runs conversion audit
3. Uses `/ads-report conversions`
4. References knowledge base (conversions.json)

**Verification:**
- [ ] Skill activates automatically
- [ ] Conversion report generated
- [ ] Knowledge base referenced

### Test: GAQL Queries Skill

**Trigger phrase:**
```
claude> I need to run a custom GAQL query to analyze search terms
```

**Expected behavior:**
1. gaql-queries skill activates
2. Claude helps build query
3. Uses `/ads-query` command
4. Provides query templates from skill

**Verification:**
- [ ] Skill activates automatically
- [ ] Query templates suggested
- [ ] Command executed correctly

---

## 4. Agent Testing

### Test: PMax Optimizer Agent

**Invocation:**
```
claude> Invoke pmax-optimizer agent to analyze our campaigns
```

**Expected behavior:**
1. Agent persona activates
2. Follows analysis framework:
   - Data collection (list campaigns, reports, themes)
   - Analysis (ROAS, budget, signals)
   - Recommendations (prioritized P0/P1/P2)
   - Expected impact estimates
3. Structured output with action plan

**Verification:**
- [ ] Agent identity clear
- [ ] Follows defined process
- [ ] Provides prioritized recommendations
- [ ] Estimates impact with confidence levels

### Test: Conversion Auditor Agent

**Invocation:**
```
claude> Invoke conversion-auditor agent to diagnose tracking issues
```

**Expected behavior:**
1. Agent performs health assessment
2. Checks conversions.json knowledge
3. Generates audit report with:
   - Health score
   - Working vs broken conversions
   - Root cause analysis
   - Fix plans
4. Provides manual step guidance (GTM Preview, etc.)

**Verification:**
- [ ] Comprehensive audit performed
- [ ] Knowledge base consulted
- [ ] Fix steps actionable
- [ ] Manual steps documented

### Test: Signal Generator Agent

**Invocation:**
```
claude> Invoke signal-generator agent to create new search themes for summer season
```

**Expected behavior:**
1. Agent asks context questions (asset group, season, audience)
2. Generates themes based on:
   - Existing themes review
   - Product focus
   - Seasonal trends
3. Provides bulk upload format
4. Estimates expected impact

**Verification:**
- [ ] Context questions asked
- [ ] Themes generated (category-organized)
- [ ] Bulk upload file ready
- [ ] Impact estimated

---

## 5. Hook Testing

### Test: Budget Change Warning

**Command:**
```
claude> Run: xw ads campaign update --customer-id 2425288235 --campaign-id 23423204148 --budget 15000
```

**Expected behavior:**
1. PreToolUse hook fires BEFORE execution
2. Warning displayed: "⚠️ Budget change detected for Xwander Nordic..."
3. User prompted to confirm

**Verification:**
- [ ] Hook fires before execution
- [ ] Warning message displayed
- [ ] Execution pauses for confirmation

### Test: Campaign Pause Warning

**Command:**
```
claude> Pause campaign 23423204148
```

**Expected behavior:**
1. PreToolUse hook fires
2. Warning: "⚠️ Campaign pause/removal detected..."
3. Confirmation required

**Verification:**
- [ ] Hook fires
- [ ] Warning displayed
- [ ] Confirmation prompted

### Test: Bulk Add Info Tip

**Command:**
```
claude> /ads-pmax-signals bulk --asset-group-id 6655152002 --file /tmp/themes.txt
```

**Expected behavior:**
1. PreToolUse hook fires
2. Info message: "💡 Tip: For bulk theme additions, consider using --dry-run first..."
3. Execution continues (info only, not blocking)

**Verification:**
- [ ] Hook fires
- [ ] Tip displayed
- [ ] Execution not blocked

### Test: Theme Addition Success

**Command:**
```
claude> /ads-pmax-signals add --asset-group-id 6655152002 --theme "claude code test theme"
```

**Expected behavior:**
1. Command executes
2. Success detected in output
3. PostToolUse hook fires
4. Success message: "✅ Search themes added successfully. Monitor performance in 48-72 hours..."

**Verification:**
- [ ] Command succeeds
- [ ] Hook fires after execution
- [ ] Success message displayed

---

## 6. Integration Testing

### Test: Full Optimization Workflow

**Scenario:** Optimize underperforming campaign

**Steps:**
1. Say: "Analyze and optimize our PMax campaigns"
2. Skill activates: pmax-optimization
3. Claude runs: `/ads-pmax-list`
4. Identifies low performer (ROAS < 3.0)
5. Runs: `/ads-pmax-signals list --asset-group-id {id}`
6. Finds only 8 themes (below optimal 15-25)
7. Invokes signal-generator agent
8. Agent generates 12 new themes
9. Creates bulk upload file
10. Runs: `/ads-pmax-signals bulk --file /tmp/themes.txt`
11. Hook fires with success message
12. Documents changes and sets 7-day review

**Verification:**
- [ ] Workflow smooth (no gaps)
- [ ] Skill → Command → Agent → Hook chain works
- [ ] Recommendations actionable
- [ ] Changes documented

### Test: Conversion Audit Workflow

**Scenario:** Diagnose broken conversion tracking

**Steps:**
1. Say: "Check why conversions aren't tracking"
2. Skill activates: conversion-tracking
3. Claude runs: `/ads-report conversions --days 30`
4. Identifies zero-conversion actions
5. Invokes conversion-auditor agent
6. Agent checks conversions.json knowledge
7. Generates health score and root cause
8. Provides fix plan (GTM tag debugging)
9. References GTM UI guide for manual steps

**Verification:**
- [ ] Issue diagnosed correctly
- [ ] Knowledge base consulted
- [ ] Root cause identified
- [ ] Fix plan actionable (including manual steps)

---

## 7. Edge Cases

### Test: Invalid Customer ID

```
claude> /ads-pmax-list --customer-id 9999999999
```

**Expected:** Error message, suggest checking accounts.json

### Test: Invalid Asset Group ID

```
claude> /ads-pmax-signals list --asset-group-id 0000000000
```

**Expected:** Error message, list valid IDs

### Test: Authentication Failure

**Simulate:** Temporarily move google-ads.yaml

```
claude> /ads-pmax-list
```

**Expected:** Authentication error, suggest checking credentials

### Test: Quota Exceeded

**Simulate:** (Hard to test without hitting actual quota)

**Expected:** Error message, suggest waiting and retry

---

## 8. Documentation Verification

### Test: Command Help

Each command markdown should have:
- [ ] Clear description
- [ ] Usage examples
- [ ] Implementation details
- [ ] Example output
- [ ] Related commands
- [ ] Context about Xwander

### Test: Skill Documentation

Each skill should have:
- [ ] Purpose statement
- [ ] Activation triggers
- [ ] How to use (workflows)
- [ ] Best practices
- [ ] Troubleshooting
- [ ] Context

### Test: Agent Documentation

Each agent should have:
- [ ] Role definition
- [ ] Expertise areas
- [ ] Process/workflow
- [ ] Analysis frameworks
- [ ] Communication style
- [ ] Constraints (never/always)
- [ ] Success metrics

---

## 9. Performance Testing

### Test: Command Execution Time

Measure time for common commands:

- [ ] `/ads-pmax-list` - Target: < 5s
- [ ] `/ads-pmax-signals list` - Target: < 3s
- [ ] `/ads-report performance --days 7` - Target: < 8s

### Test: Skill Load Time

Measure time for skill to activate and guide:

- [ ] pmax-optimization - Target: < 2s to activate
- [ ] conversion-tracking - Target: < 2s to activate
- [ ] gaql-queries - Target: < 2s to activate

### Test: Agent Response Quality

Evaluate agent output:

- [ ] pmax-optimizer: Clear priorities, impact estimates
- [ ] conversion-auditor: Accurate diagnosis, actionable fixes
- [ ] signal-generator: Relevant themes, ready to implement

---

## 10. Backward Compatibility

### Test: Python CLI Still Works

```bash
cd /srv/plugins/xwander-ads
export PYTHONPATH="$PWD:$PYTHONPATH"
python3 -m xwander_ads.cli pmax list --customer-id 2425288235 --campaigns
```

**Expected:** Same output as before migration

### Test: Existing Scripts Unaffected

Check cron jobs, automation scripts using Python CLI directly.

**Expected:** No changes needed

---

## Results Summary

### Pass Criteria

- [ ] All 5 commands execute correctly
- [ ] All 3 skills activate on triggers
- [ ] All 3 agents follow defined processes
- [ ] All 4 hooks fire at correct times
- [ ] Integration workflows smooth
- [ ] Backward compatibility maintained
- [ ] Documentation complete and accurate

### Issues Found

(Document any issues during testing)

---

## Sign-off

**Tested by:** _________________
**Date:** _________________
**Status:** PASS / FAIL / NEEDS WORK
**Notes:** _________________

---

*Test checklist version 1.0 - 2026-01-11*
