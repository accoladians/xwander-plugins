# xwander-ads

Google Ads API integration plugin for Xwander Platform - Performance Max campaigns, audiences, conversions, and more.

## Features

- **Performance Max Management**
  - List/get campaigns with detailed metrics
  - Manage asset groups
  - Add/remove search themes (bulk support)
  - Audience signals management
  - Budget operations

- **Multi-Version API Support**
  - v20 (default, stable)
  - v21 (current)
  - v22 (latest features)

- **Production-Ready**
  - Comprehensive error handling with specific exit codes
  - Batch operations (50 items per API call)
  - Clean exception hierarchy
  - Integration tests included

## Installation

```bash
cd /srv/plugins/xwander-ads
pip install -e .
```

## Quick Start

### Test Authentication

```bash
xw ads auth test
```

### List Performance Max Campaigns

```bash
xw ads pmax list --customer-id 2425288235 --campaigns
```

### Manage Search Themes

```bash
# List current themes
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 list

# Add single theme
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 add --theme "lapland summer tours"

# Bulk add from file
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 bulk --file themes.txt
```

## Documentation

- **Quick Reference:** [docs/QUICK_REFERENCE.json](docs/QUICK_REFERENCE.json)
- **Complete Guide:** [docs/PMAX_GUIDE.md](docs/PMAX_GUIDE.md)
- **Examples:** [examples/](examples/)

## Configuration

The plugin searches for `google-ads.yaml` in these locations:

1. `~/.google-ads.yaml` (standard)
2. `/srv/xwander-platform/.env/google-apis/google-ads.yaml`
3. `/srv/xwander-platform/tools/business-tools/google-ads.yaml`
4. `~/.google-ads/config.yaml`

### Config Format

```yaml
developer_token: YOUR_DEVELOPER_TOKEN
client_id: YOUR_CLIENT_ID.apps.googleusercontent.com
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
login_customer_id: 2007072401  # Optional, for MCC
use_proto_plus: True
```

## Architecture

```
xwander_ads/
├── __init__.py
├── auth.py              # Authentication (imports from xwander-google-auth)
├── cli.py               # CLI entry point
├── exceptions.py        # Custom exceptions with exit codes
└── pmax/
    ├── __init__.py
    ├── campaigns.py     # Campaign CRUD operations
    ├── signals.py       # Search themes & audience signals
    ├── assets.py        # Asset management (future)
    └── budgets.py       # Budget operations (future)
```

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | None |
| 1 | Generic error | Check error message |
| 2 | Quota exceeded | Wait and retry |
| 3 | Authentication failed | Check credentials |
| 4 | Resource not found | Verify IDs |
| 5 | Duplicate signal | Skip or remove first |
| 6 | Invalid resource | Fix format |
| 7 | Budget error | Check configuration |
| 8 | Validation error | Fix input data |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=xwander_ads --cov-report=html

# Run specific test class
pytest tests/test_pmax.py::TestSignals -v
```

## CLI Commands

### Performance Max

```bash
# List campaigns
xw ads pmax list --customer-id ID --campaigns [--enabled-only]

# Get campaign details
xw ads pmax get --customer-id ID --campaign-id CID

# List asset groups
xw ads pmax list --customer-id ID --asset-groups [--campaign-id CID]

# Manage signals
xw ads pmax signals --customer-id ID --asset-group-id AGID {list|add|bulk|remove}
  --theme TEXT          # For add action
  --file PATH           # For bulk action
  --resource-name RN    # For remove action
```

### Authentication

```bash
# Test authentication
xw ads auth test [--config PATH]
```

### API Versions

```bash
# Use specific API version (default: v20)
xw ads --api-version v22 pmax list --customer-id ID --campaigns
```

## Migration from toolkit/pmax_signals.py

This plugin replaces the standalone `toolkit/pmax_signals.py` script with a modular, extensible architecture.

### Old Script
```bash
python3 toolkit/pmax_signals.py list --customer-id 2425288235 --asset-group 6655152002
```

### New Plugin
```bash
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 list
```

All functionality is preserved with improved error handling and extensibility.

## Xwander Platform Context

### Account Details
- **Customer ID:** 2425288235
- **Account:** Xwander Nordic
- **Currency:** EUR
- **Timezone:** Europe/Helsinki

### Main Campaign
- **ID:** 23423204148
- **Name:** Xwander PMax Nordic

### Asset Groups
| Language | ID | Name |
|----------|-----|------|
| English | 6655152002 | Xwander EN |
| German | 6655251007 | Xwander DE |
| French | 6655151999 | Xwander FR |
| Spanish | 6655250848 | Xwander ES |

## Development

### Install in Development Mode

```bash
pip install -e ".[dev]"
```

### Code Style

```bash
# Format with black
black xwander_ads/

# Lint with flake8
flake8 xwander_ads/
```

### Adding New Modules

1. Create module in `xwander_ads/` (e.g., `conversions.py`)
2. Add CLI commands in `cli.py`
3. Update `__init__.py` exports
4. Add tests in `tests/`
5. Update documentation

## Plugin Integration

This plugin integrates with the Xwander CLI via `plugin.json`:

```json
{
  "name": "xwander-ads",
  "entrypoint": "xwander_ads.cli:main",
  "commands": [
    {
      "name": "ads",
      "description": "Google Ads operations"
    }
  ]
}
```

## Dependencies

- `google-ads>=24.0.0` - Google Ads API client
- `google-auth>=2.0.0` - Google authentication
- `google-auth-oauthlib>=1.0.0` - OAuth2 flow

## License

Proprietary - Xwander Platform

## Support

- **Documentation:** [docs/](docs/)
- **Issues:** Platform issue tracker
- **Contact:** joni@accolade.fi

---

**Version:** 1.0.0
**Author:** Xwander Platform
**Updated:** 2026-01-10
