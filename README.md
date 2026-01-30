# Xwander Google Marketing Platform Plugins

**Monorepo for Google Marketing Platform integrations**

Repository: https://github.com/accoladians/xwander-plugins

Built: 2026-01-10 | Status: Production Ready

---

## Plugins

| Plugin | Version | Purpose | LOC | Status |
|--------|---------|---------|-----|--------|
| [xwander-google-auth](xwander-google-auth/) | 1.0.0 | Shared OAuth2 | 2,500 | Ready |
| [xwander-ads](xwander-ads/) | 1.0.0 | Google Ads API | 5,000 | Ready |
| [xwander-gtm](xwander-gtm/) | 1.0.0 | Tag Manager API | 2,335 | Ready |
| [xwander-ga4](xwander-ga4/) | 1.0.0 | Analytics 4 API | 2,885 | Ready |
| [xwander-cli](xwander-cli/) | 1.0.0 | Unified CLI | 300 | Ready |
| [xwander-gsheet](xwander-gsheet/) | 2.0.0 | Google Sheets | - | Existing |
| [xwander-airtable](xwander-airtable/) | 1.1.0 | Airtable API + MCP complement | 4,100 | Ready |

**Total:** 17,100+ LOC across 6 new plugins

---

## Quick Start

### Installation

```bash
# Install all plugins
cd /srv/plugins
pip install -e xwander-google-auth/
pip install -e xwander-ads/
pip install -e xwander-gtm/
pip install -e xwander-ga4/
pip install -e xwander-cli/

# Or with full dependencies
pip install -e "xwander-cli[full]"
```

### Setup

```bash
# One-time OAuth2 setup for all Google APIs
xw auth setup

# Test authentication
xw auth test
```

### Usage

```bash
# Google Ads
xw ads pmax list --customer-id 2425288235 --campaigns
xw ads pmax signals --asset-group-id 6655152002 list

# Analytics 4
xw ga4 report --dimensions date source --metrics sessions --days 7
xw ga4 realtime

# Tag Manager
xw gtm list-tags --container-id 176670340
xw gtm publish --container-id 176670340
```

---

## Architecture

### Unified CLI

All plugins accessible via single `xw` command:

```
xw
├── auth        → xwander-google-auth
├── ads         → xwander-ads
├── gtm         → xwander-gtm
├── ga4         → xwander-ga4
└── gmc         → xwander-gmc (future)
```

### Shared Authentication

```python
from xwander_google_auth import get_client

# Works for all Google APIs
ads_client = get_client("google-ads")
ga4_client = get_client("ga4")
gtm_client = get_client("gtm")
```

### Consistent Error Handling

All plugins use standardized exit codes:
- 0: Success
- 1: Generic error
- 2: Rate limit/quota
- 3: Authentication
- 4: Not found
- 5-8: Plugin-specific

---

## Documentation

### Quick Start Guides
- [xwander-google-auth/README.md](xwander-google-auth/README.md)
- [xwander-ads/README.md](xwander-ads/README.md)
- [xwander-gtm/README.md](xwander-gtm/README.md)
- [xwander-ga4/README.md](xwander-ga4/README.md)
- [xwander-cli/README.md](xwander-cli/README.md)

### API References
- [xwander-ads/docs/PMAX_GUIDE.md](xwander-ads/docs/PMAX_GUIDE.md)
- [xwander-ga4/docs/API.md](xwander-ga4/docs/API.md)
- [xwander-ads/xwander_ads/reporting/README.md](xwander-ads/xwander_ads/reporting/README.md)

### Quick References (RAG-Optimized)
- [xwander-ads/docs/QUICK_REFERENCE.json](xwander-ads/docs/QUICK_REFERENCE.json)
- [xwander-ga4/docs/QUICK_REFERENCE.json](xwander-ga4/docs/QUICK_REFERENCE.json)
- [xwander-cli/docs/QUICK_REFERENCE.json](xwander-cli/docs/QUICK_REFERENCE.json)

---

## Testing

```bash
# Run all tests
pytest xwander-*/tests/ -v

# Run specific plugin tests
pytest xwander-ads/tests/test_pmax.py -v
pytest xwander-ads/tests/test_reporting.py -v
pytest xwander-ga4/tests/test_ga4.py -v

# With coverage
pytest xwander-ads/tests/ --cov=xwander_ads --cov-report=html
```

---

## Examples

### Performance Max Search Themes
```bash
# List themes
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 list

# Bulk add from file
xw ads pmax signals --customer-id 2425288235 --asset-group-id 6655152002 bulk --file themes.txt
```

### GA4 Custom Dimension
```bash
xw ga4 dimension create \
  --display-name "Product Type" \
  --parameter-name product_type \
  --scope EVENT
```

### GTM Publishing
```bash
xw gtm publish --container-id 176670340 --notes "Automated deploy"
```

### GAQL Query
```bash
xw ads query --customer-id 2425288235 \
  "SELECT campaign.name, metrics.clicks FROM campaign WHERE campaign.status = ENABLED LIMIT 10"
```

---

## Development

### Building New Plugins

1. **Create directory structure:**
   ```bash
   mkdir -p xwander-newplugin/{xwander_newplugin,docs,tests,skills,.claude-plugin}
   ```

2. **Follow xwander-gsheet pattern:**
   - `.claude-plugin/plugin.json` - Metadata
   - `docs/` - Documentation
   - `skills/` - Agent skills
   - `tests/` - Tests
   - `setup.py` - Installation

3. **Add to xwander-cli routing:**
   ```python
   PLUGINS = {
       'newplugin': 'xwander_newplugin.cli',
       ...
   }
   ```

---

## Repository Structure

```
/srv/plugins/ (xwander-plugins monorepo)
├── xwander-google-auth/    # OAuth2 foundation
├── xwander-ads/            # Google Ads API
├── xwander-gtm/            # Tag Manager API
├── xwander-ga4/            # Analytics 4 API
├── xwander-cli/            # Unified CLI
├── xwander-gsheet/         # Google Sheets (existing)
├── xwander-context/        # Context management (existing)
├── .git/                   # Monorepo git
├── .gitignore
├── README.md               # This file
├── BUILD_COMPLETE.md       # Build summary
└── EXECUTIVE_SUMMARY.md    # Executive summary
```

---

## Configuration

### Credentials Location

Plugins search for credentials in order:
1. `~/.xwander-google/credentials.json` (unified, recommended)
2. `~/.google-ads.yaml` (legacy Google Ads)
3. `/srv/xwander-platform/.env/google-apis/google-ads.yaml`
4. Other platform-specific locations

### Auto-Migration

First run automatically migrates legacy credentials to unified location.

---

## Support

### Documentation
- Quick starts in each plugin's README.md
- API references in docs/ directories
- RAG-optimized JSON quick references
- Working code examples

### Issues
- Report bugs via GitHub issues
- Tag with plugin name
- Include error messages and steps to reproduce

### Contact
- Platform: Xwander Nordic
- Email: joni@accolade.fi

---

## License

Proprietary - Xwander Platform

---

## Build Info

**Date:** 2026-01-10  
**Method:** Multi-agent parallel orchestration  
**Duration:** 13 minutes  
**Total LOC:** 13,020+  
**Total Files:** 87  
**Total Tests:** 71+  
**Agents:** 6 (Gemini, Codex, Backend, Sonnet x2, Haiku)  

**Orchestrated by:** Claude Sonnet 4.5  
**Token Efficiency:** 80%+ savings via delegation  

---

For detailed information, see individual plugin README files and [BUILD_COMPLETE.md](BUILD_COMPLETE.md).
