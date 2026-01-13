# Changelog

All notable changes to the xwander-ga4 plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-13

### Added
- **CLAUDE.md**: Comprehensive AI agent guide with quick commands, decision tree, and common workflows
- **CHANGELOG.md**: Version history and release notes
- CLI help text enrichment: All commands now include usage examples in `--help` output
- Missing docstrings:
  - `ReportFormatter` class docstring with detailed description of formatting methods
  - `DimensionManager.__init__` docstring explaining initialization parameters
  - `AudienceManager.__init__` docstring explaining initialization parameters

### Changed
- Updated version from 1.0.0 to 1.1.0
- Improved CLI command descriptions for clarity:
  - `report`: "Run a GA4 report with custom dimensions and metrics"
  - `realtime`: "Run realtime GA4 report showing active users now"
  - `traffic-sources`: "Get traffic breakdown by source and medium"
  - `top-pages`: "Get top pages ranked by sessions"
  - `conversions`: "Get conversion events with counts and values"
  - `daily-summary`: "Get daily metrics summary (sessions, users, events)"
  - `dimension create`: Added note about parameter name validation
  - `dimension list`: "List all custom dimensions for property"
  - `audience list`: "List all audiences in property"
  - `audience search`: "Search audiences by name pattern (case-insensitive)"

### Fixed
- **docs/API.md**: Corrected all command references from `xw ga4` to `xwander-ga4` (the actual installed command)

### Documentation
- Added comprehensive examples to all CLI commands via epilog parameter
- Created decision tree for command selection in CLAUDE.md
- Documented common workflows for traffic analysis, custom dimensions, and audience research
- Added error handling reference with solutions
- Documented Python API usage patterns for AI agents

## [1.0.0] - 2026-01-10

### Added
- Initial release
- GA4 Data API client wrapper
- GA4 Admin API client wrapper
- Report builder with predefined templates
- Report formatter (table, JSON, summary)
- Custom dimension management
- Audience management
- CLI with commands:
  - `report`: Custom reports
  - `realtime`: Realtime data
  - `traffic-sources`: Traffic source breakdown
  - `top-pages`: Top pages by sessions
  - `conversions`: Conversion events
  - `daily-summary`: Daily metrics
  - `dimension create/list`: Dimension management
  - `audience list/search`: Audience management
- Default property ID: 358203796 (xwander.com)
- Python package installable via pip
- Full API documentation

### Documentation
- README.md with installation instructions
- API.md with complete API reference
- Python API examples
- CLI command reference
