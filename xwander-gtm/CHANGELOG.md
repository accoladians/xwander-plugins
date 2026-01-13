# Changelog

All notable changes to xwander-gtm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-13

### Fixed
- **CRITICAL**: Changed Enhanced Conversions variable type from `gtes` to `awec`
  - The `gtes` type was incorrect and caused GTM compiler errors
  - Updated `create_user_data_variable()` to use proper `awec` type
  - Added AUTO mode parameters: `mode`, `autoPhoneEnabled`, `autoEmailEnabled`, `autoAddressEnabled`
  - Added MANUAL mode with GTM variable reference support
  - Added validation for empty MANUAL mode configurations

### Added
- **Workspace validation system** - comprehensive pre-publish checks:
  - Validates `awec` variables have required `mode` parameter
  - Detects incorrect `gtes` type usage (should be `awec` for Enhanced Conversions)
  - Verifies all variable references resolve to existing variables
  - Checks all trigger references in tags are valid
  - Validates conversion tags (`awct`) have required `conversionId` and `conversionLabel`
  - Expanded GTM built-in variables whitelist (Click, Page, Event, Form, Video, History, Error variables)
- **Dry-run mode** for safe operations:
  - `--dry-run` flag for `create-version` command - preview changes without creating
  - `--dry-run` flag for `create-ec-variable` command - preview configuration
- **New CLI command**: `validate-workspace` - run validation checks without creating version
- **Enhanced CLI help** - added usage examples to main CLI and key commands

### Changed
- Version creation now validates workspace by default (use `--skip-validation` to disable)
- Improved error messages with detailed validation feedback
- Better workspace conflict resolution during sync operations

### Breaking Changes
- Enhanced Conversions variable type changed from `gtes` to `awec`
  - If you have existing EC variables created with this tool, they may need to be recreated
  - Manual GTM variables are not affected

## [1.0.0] - 2026-01-11

### Added
- Initial release of xwander-gtm plugin
- GTM API client with authentication
- Workspace management operations
- Tag operations (list, get, create, update, delete)
- Variable operations with Enhanced Conversions support
- Trigger operations
- Publishing workflow (sync, create version, publish)
- Comprehensive CLI with 20+ commands
- Exception handling and error recovery
- Claude Code integration with agents, commands, skills, and hooks

[1.1.0]: https://github.com/accoladians/xwander-plugins/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/accoladians/xwander-plugins/releases/tag/v1.0.0
