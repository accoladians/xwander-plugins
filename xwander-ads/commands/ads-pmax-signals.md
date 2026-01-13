---
description: Manage Performance Max search themes (signals)
argument-hint: <action> --asset-group-id ID [--theme TEXT] [--file PATH]
allowed-tools: [Bash, Read, Write]
---

# Manage Performance Max Search Themes

Add, list, or remove search themes (audience signals) for Performance Max asset groups.

## Usage

```
/ads-pmax-signals list --asset-group-id 6655152002
/ads-pmax-signals add --asset-group-id 6655152002 --theme "lapland summer activities"
/ads-pmax-signals bulk --asset-group-id 6655152002 --file /tmp/themes.txt
/ads-pmax-signals remove --asset-group-id 6655152002 --resource-name "customers/2425288235/..."
```

## Actions

### list
List all current search themes for an asset group.

### add
Add a single search theme.

**Parameters:**
- `--theme TEXT` - Theme text (e.g., "northern lights tours")

### bulk
Add multiple themes from a file (one per line).

**Parameters:**
- `--file PATH` - Path to file with themes (one per line)

**Workflow:**
1. Create themes file if user provides themes list
2. Write to /tmp/themes-{timestamp}.txt
3. Execute bulk add command

### remove
Remove a search theme by resource name.

**Parameters:**
- `--resource-name TEXT` - Full resource name from list output

## Implementation

```bash
export PYTHONPATH="/srv/plugins/xwander-ads:$PYTHONPATH"
cd /srv/plugins/xwander-ads
python3 -m xwander_ads.cli pmax signals --customer-id 2425288235 --asset-group-id {id} {action} [options]
```

## Asset Group IDs

| Language | ID | Name |
|----------|-----|------|
| English | 6655152002 | Xwander EN |
| German | 6655251007 | Xwander DE |
| French | 6655151999 | Xwander FR |
| Spanish | 6655250848 | Xwander ES |

## Best Practices

- **Optimal count:** 15-25 themes per asset group
- **Theme format:** Specific, descriptive (e.g., "husky sledding lapland" not "tours")
- **Avoid duplicates:** Check existing themes first with `list` action
- **Language match:** Themes should match asset group language
- **Wait 48h:** Allow time for performance data after changes

## Example Output

```
=== Asset Group 6655152002 Search Themes (18) ===

  1. "northern lights tours"
  2. "husky sledding lapland"
  3. "rovaniemi winter activities"
  ...

✓ Added search theme: "lapland summer hiking"
  Resource: customers/2425288235/assetGroupSignals/6655152002~123456
```

## Related Commands

- `/ads-pmax-list` - List campaigns and asset groups
- `/ads-report` - Check performance after signal changes
