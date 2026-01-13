# Changelog - xwander-ads Plugin

## [1.1.0] - 2026-01-13

### Fixed

#### CLI Integration
- **Issue**: `xw ads` command failed when invoked from xw CLI
- **Root Cause**: `main()` function didn't accept arguments parameter
- **Fix**: Changed signature to `def main(args=None):` and updated `parser.parse_args(args=args)`
- **Impact**: Now works with xw CLI plugin system
- **File**: `xwander_ads/cli.py`

### Improved

#### CLI Help System
- Added `epilog` with common workflow examples to main parser
- Added `epilog` with specific examples to all subcommands
- Enhanced help text descriptions with:
  - Example values (e.g., "Customer ID (e.g., 2425288235)")
  - Use case clarifications (e.g., "table (human-readable) | csv (spreadsheet)")
  - Command purpose explanations
- Added `formatter_class=argparse.RawDescriptionHelpFormatter` for proper example formatting
- **Use Case**: Makes CLI self-documenting for AI agents and users

#### Docstrings
- Enriched function docstrings with AI-friendly content:
  - "Common Use Cases" section
  - Concrete examples with expected output
  - Inline comments explaining complex logic
  - Error condition explanations
- Updated functions:
  - `list_signals()` - Search theme listing
  - `add_search_theme()` - Single theme addition
  - `bulk_add_themes()` - Batch theme operations
- **Use Case**: AI agents can better understand when/how to use functions

### Added

#### Documentation
- **CLAUDE.md** - Comprehensive AI agent guide with:
  - Decision tree for PMax operations
  - Common workflows with examples
  - Error handling reference
  - Default IDs (customer: 2425288235, campaign: 23423204148)
  - Module architecture overview
  - Integration points with growth toolkit
  - Best practices for AI agents
- **Use Case**: AI agents can quickly understand plugin capabilities

### Changed

#### Version
- Bumped version from 1.0.0 to 1.1.0
- **File**: `xwander_ads/__init__.py`

---

## [1.0.1] - 2026-01-12

### Fixed

#### GAQL Asset Groups Query Bug
- **Issue**: `list_asset_groups()` used invalid GAQL subquery syntax
- **Error**: `Error in WHERE clause: invalid value campaign.resource_name`
- **Root Cause**: GAQL does not support SQL-style `IN (SELECT ...)` subqueries
- **Fix**: Replaced subquery with GAQL implicit join pattern
- **File**: `xwander_ads/pmax/campaigns.py`

```python
# Before (buggy)
WHERE asset_group.campaign IN (
    SELECT campaign.resource_name FROM campaign WHERE ...
)

# After (fixed)
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
```

#### Protobuf Enum Handling Bug
- **Issue**: Report generation crashed on enum fields
- **Error**: `EnumMeta.__call__() missing 1 required positional argument: 'value'`
- **Root Cause**: Code tried to instantiate enum types with `type(value)()`
- **Fix**: Added `_is_default_value()` helper with safe enum detection
- **File**: `xwander_ads/reporting/reports.py`

#### Protobuf Repeated Field Bug
- **Issue**: Report generation crashed on repeated/list fields
- **Error**: `'RepeatedScalarContainer' object has no attribute 'DESCRIPTOR'`
- **Root Cause**: Repeated fields were processed as protobuf messages
- **Fix**: Check for `'Repeated' in type_name` before `_pb` access
- **File**: `xwander_ads/reporting/reports.py`

### Improved

#### Input Validation
- Added numeric validation for `campaign_id` parameter
- Prevents GAQL injection attacks
- Better error messages for invalid input

#### Efficiency
- Use `row.campaign.id` directly instead of string parsing resource names
- Added `limit` parameter to `list_asset_groups()` (default: 100, max: 10000)
- Added `campaign_name` to asset group results

### Added

#### Documentation
- `docs/GAQL_GUIDE.md` - GAQL best practices and patterns
- `CHANGELOG.md` - Version history

---

## [1.0.0] - 2026-01-10

### Initial Release

- Performance Max campaign management
- Asset group operations
- Audience signals management
- GAQL query builder
- Reporting with multiple export formats
- Conversion tracking integration

---
*Maintained by: xwander-ads plugin team*
