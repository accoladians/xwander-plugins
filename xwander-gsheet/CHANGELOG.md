# Changelog

## [2.0.0] - 2026-01-05

### Changed
- **BREAKING**: Migrated from symlink to native plugin
- **BREAKING**: Primary import is now `from xwander_gsheet import GSheet`
- **BREAKING**: Directory renamed from `lib/` to `xwander_gsheet/` for proper Python packaging
- Made plugin installable with `pyproject.toml` (modern Python packaging)
- Moved tests to plugin directory (`tests/test_gsheet.py`)
- Moved docs to plugin directory (`docs/`)

### Added
- Backward compatibility layer in old location (issues deprecation warning)
- Plugin README with installation instructions
- Plugin directory structure with proper `__init__.py`
- pytest configuration in `pyproject.toml`
- Comprehensive test suite (30 tests, all passing)
- API documentation skeleton (`docs/API.md`)

### Deprecated
- Importing from `purchasing.lib.gsheet` (use `xwander_gsheet` instead)
- Using `sys.path.insert(...)` to access gsheet (use plugin path instead)

### Removed
- Symlink from plugin to erasoppi lib (replaced with actual code)

### Migration Notes
**Old code (deprecated but works)**:
```python
import sys
sys.path.insert(0, '/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/lib')
from gsheet import GSheet
```

**New code (recommended)**:
```python
import sys
sys.path.insert(0, '/srv/plugins/xwander-gsheet')
from xwander_gsheet import GSheet
```

## [1.0.0] - 2025-12-28

Initial release with section-based abstraction.
