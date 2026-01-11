# Migration Guide: v1.0 → v2.0

## Summary

xwander-gsheet v2.0 is now a **native Claude Code plugin** with proper Python packaging.

## What Changed

### Old Way (v1.0)
```python
import sys
sys.path.insert(0, '/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/lib')
from gsheet import GSheet
```

### New Way (v2.0)
```python
import sys
sys.path.insert(0, '/srv/plugins/xwander-gsheet')
from xwander_gsheet import GSheet
```

## Installation

The plugin is located at `/srv/plugins/xwander-gsheet` and can be imported by adding it to sys.path.

**Note**: pip installation in editable mode requires setuptools with PEP 660 support. For now, use sys.path approach above.

## Backward Compatibility

Old imports still work but issue deprecation warnings:
```python
from purchasing.lib import GSheet  # Works, but deprecated
```

## Migration Timeline

- **2026-01-05**: v2.0 released with backward compatibility
- **2026-Q1**: Deprecation warnings active
- **2026-Q2**: Old import path may be removed (TBD)

## Script Updates

**Before**:
```python
import sys
sys.path.insert(0, '/srv/erasoppi-platform/erasoppi.fi/growth/purchasing/lib')
from gsheet import GSheet

sheet = GSheet.create_new("Order")
```

**After**:
```python
import sys
sys.path.insert(0, '/srv/plugins/xwander-gsheet')
from xwander_gsheet import GSheet

sheet = GSheet.create_new("Order")
```

That's it! API is unchanged.

## Testing

All tests pass (30/30):
```bash
cd /srv/plugins/xwander-gsheet
python3 -m pytest tests/test_gsheet.py -v
```

## Verification

```bash
# Test new import
python3 -c "import sys; sys.path.insert(0, '/srv/plugins/xwander-gsheet'); from xwander_gsheet import GSheet; print('OK')"

# Test backward compatibility
cd /srv/erasoppi-platform/erasoppi.fi/growth/purchasing
python3 -c "from lib import GSheet; print('OK')"
```
