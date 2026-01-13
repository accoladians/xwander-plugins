---
name: pmax-optimization
description: Activate when user asks about Performance Max campaigns, search themes, asset groups, or PMax optimization. Provides guidance on managing PMax campaigns via xwander-ads plugin.
version: 1.0.1
---

# Performance Max Optimization Skill

## Purpose

Guide Claude through Performance Max campaign management using xwander-ads plugin commands.

## When to Use

Activate this skill when user mentions:
- "Performance Max", "PMax", or "pmax"
- "search themes", "audience signals", or "signals"
- "asset groups"
- Campaign optimization or performance improvement
- Budget allocation for PMax campaigns

## How to Use

### 1. List Campaigns

Use `/ads-pmax-list` command to see all PMax campaigns with performance metrics.

```
/ads-pmax-list
```

**Analyze output for:**
- Campaign status (ENABLED vs PAUSED)
- Budget vs. actual spend (underspending if < 80%)
- ROAS (target: 3.0-4.0x minimum)
- Conversion volume (minimum 30/month for optimization)

### 2. Manage Search Themes

Use `/ads-pmax-signals` command to add/remove themes.

**List existing themes:**
```
/ads-pmax-signals list --asset-group-id 6655152002
```

**Add single theme:**
```
/ads-pmax-signals add --asset-group-id 6655152002 --theme "lapland summer activities"
```

**Bulk add (recommended for multiple themes):**
1. Create /tmp/themes.txt with one theme per line
2. Run: `/ads-pmax-signals bulk --asset-group-id 6655152002 --file /tmp/themes.txt`

### 3. Review Performance

Use `/ads-report` command for detailed metrics:

```
/ads-report performance --days 30
/ads-report search-terms --days 14
```

## Asset Group IDs (Reference)

| Language | ID | Name |
|----------|-----|------|
| English | 6655152002 | Xwander EN |
| German | 6655251007 | Xwander DE |
| French | 6655151999 | Xwander FR |
| Spanish | 6655250848 | Xwander ES |

## Best Practices

### Search Theme Guidelines

- **Optimal count:** 15-25 themes per asset group
- **Theme format:** Specific, descriptive phrases (e.g., "husky sledding rovaniemi" not "tours")
- **Language match:** Themes must match asset group language
- **Avoid duplicates:** Always check existing themes first
- **Wait 48h:** Allow time for performance data after changes

### Optimization Workflow

1. **Baseline Assessment**
   - List campaigns with `/ads-pmax-list`
   - Generate 30-day performance report
   - Identify underperformers (ROAS < 3.0)

2. **Signal Analysis**
   - List search themes for each asset group
   - Count themes (optimal: 15-25)
   - Check for language consistency

3. **Theme Enhancement**
   - Review search terms report for high-performing queries
   - Add relevant themes based on data
   - Remove low-performing themes (if ROI data available)

4. **Monitor Impact**
   - Wait 48-72 hours for data
   - Re-run performance report
   - Compare before/after metrics

### Budget Optimization

- **Underspending (< 80% budget):** Add search themes, increase bids
- **Overspending:** Review budget pacing, consider increasing budget
- **Low ROAS (< 3.0):** Audit search themes, check landing pages, review targeting

## Common Workflows

### Add Search Themes to EN Asset Group

```
1. /ads-pmax-signals list --asset-group-id 6655152002
2. Review existing 18 themes
3. /ads-pmax-signals add --asset-group-id 6655152002 --theme "northern lights photography tours"
4. Verify added successfully
```

### Optimize Underperforming Campaign

```
1. /ads-report performance --days 30
2. Identify campaign with ROAS 2.1 (below target)
3. /ads-pmax-signals list --asset-group-id {id}
4. Check theme count (only 8 themes)
5. Recommend adding 7-12 more relevant themes
6. Execute bulk add with curated theme list
7. Schedule follow-up review in 7 days
```

### Bulk Theme Addition

```
1. User provides list of 15 themes
2. Create /tmp/themes-{timestamp}.txt
3. Write themes (one per line)
4. /ads-pmax-signals bulk --asset-group-id 6655152002 --file /tmp/themes-{timestamp}.txt
5. Confirm all themes added
6. Document in optimization log
```

## Troubleshooting

### Command fails with authentication error
- Check google-ads.yaml exists
- Verify credentials in /srv/.env.master
- Run: `xw ads auth test`

### Duplicate signal error
- Theme already exists for this asset group
- List existing themes to verify
- Skip or remove existing theme first

### Invalid asset group ID
- Verify ID from asset groups list
- Ensure ID matches language/market
- Check campaign status (must be ENABLED)

## Context: Xwander Nordic

- **Customer ID:** 2425288235
- **Currency:** EUR
- **Focus:** Lapland travel packages (winter/summer)
- **Peak season:** December-March (Northern Lights), June-August (Midnight Sun)
- **Target ROAS:** 3.0-4.0x minimum

## Related Skills

- **conversion-tracking** - Optimize conversion setup
- **gaql-queries** - Advanced data analysis

## Resources

- **Quick Reference:** /srv/plugins/xwander-ads/docs/QUICK_REFERENCE.json
- **PMax Guide:** /srv/plugins/xwander-ads/docs/PMAX_GUIDE.md
- **Knowledge Base:** /srv/xwander-platform/xwander.com/growth/knowledge/
