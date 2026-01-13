# Conversions Module

Comprehensive conversion tracking and management for Google Ads.

## Features

- **Conversion Actions**: Create, list, update, and manage conversion actions
- **Enhanced Conversions**: SHA-256 hashing for ECW (Web) and ECL (Leads)
- **Offline Sync**: Sync HubSpot deals to Google Ads conversions
- **Diagnostics**: Health checks and troubleshooting tools

## Quick Start

```python
from xwander_ads.auth import get_google_ads_client
from xwander_ads.conversions import (
    ConversionActionManager,
    EnhancedConversionsManager,
    HubSpotOfflineSync,
    ConversionTracker
)

# Initialize
client = get_google_ads_client()
manager = ConversionActionManager(client)

# List conversions
conversions = manager.list_conversions("2425288235")
print(f"Found {len(conversions)} conversion actions")

# Get labels for GTM
labels = manager.get_conversion_labels("2425288235")
for name, info in labels.items():
    print(f"{name}: AW-{info['conversion_id']}/{info['conversion_label']}")
```

## Modules

### actions.py - ConversionActionManager

Manage conversion actions via Google Ads API.

**Key Methods:**
- `list_conversions()` - List all conversion actions
- `get_conversion()` - Get specific conversion by ID
- `get_conversion_labels()` - Get labels for GTM integration
- `create_conversion()` - Create new conversion action
- `update_conversion()` - Update existing conversion
- `remove_conversion()` - Remove (disable) conversion

### enhanced.py - EnhancedConversionsManager

Hash user data for Enhanced Conversions (ECW and ECL).

**Key Methods:**
- `hash_user_data()` - Normalize and hash user data
- `normalize_email()` - Normalize email for hashing
- `normalize_phone()` - Normalize phone to E.164
- `normalize_name()` - Normalize name for hashing
- `sha256_hash()` - Generate SHA-256 hash
- `validate_user_data()` - Validate user data for EC

**Normalization Rules:**
- Email: lowercase, trim, remove Gmail dots
- Phone: E.164 format (+358401234567)
- Name: lowercase, trim, remove special chars
- All: SHA-256 hash (64-char hex)

### offline_sync.py - HubSpotOfflineSync

Sync HubSpot deals to Google Ads as offline conversions.

**Key Methods:**
- `sync()` - Main sync workflow
- `get_closed_deals()` - Fetch deals from HubSpot
- `get_deal_contact()` - Get contact for deal
- `build_conversion()` - Build conversion object
- `prepare_click_conversion()` - Prepare for upload
- `upload_conversions()` - Upload to Google Ads

**Supported Pipelines:**
- `booking` - Booking Pipeline (confirmed deals)
- `sales` - Sales Pipeline (pre-booking)
- `ecommerce` - Ecommerce Pipeline (Bokun/WooCommerce)
- `all` - All pipelines

### tracking.py - ConversionTracker

Conversion tracking health checks and diagnostics.

**Key Methods:**
- `check_conversion_health()` - Account-wide health check
- `diagnose_conversion()` - Diagnose specific conversion

**Health Metrics:**
- Score: 0-100 (80+ = HEALTHY)
- Activity rate: % of enabled conversions receiving data
- Issues: Critical problems requiring immediate fix
- Warnings: Non-critical recommendations

## Common Patterns

### Create Conversion Action

```python
result = manager.create_conversion(
    customer_id="2425288235",
    name="Bokun Purchase",
    category="PURCHASE",
    value=100,
    count_type="MANY_PER_CLICK",
    click_through_days=90
)
print(f"Label: {result['conversion_label']}")
```

### Hash User Data (ECL)

```python
ec = EnhancedConversionsManager(client)

hashed = ec.hash_user_data(
    email="john.doe@gmail.com",
    phone="040 123 4567",
    first_name="John",
    last_name="Doe"
)
# Result: SHA-256 hashes ready for upload
```

### Sync HubSpot Deals

```python
syncer = HubSpotOfflineSync(
    google_ads_client=client,
    hubspot_token=os.environ['HUBSPOT_ACCESS_TOKEN'],
    customer_id="2425288235",
    conversion_action_id="7409115542"
)

# Dry run
results = syncer.sync(days=30, pipeline="booking", dry_run=True)
print(f"Ready to sync: {results['conversions_ready']}")

# Live upload
results = syncer.sync(days=30, pipeline="booking", dry_run=False)
print(f"Uploaded: {results['uploaded']}")
```

### Check Health

```python
tracker = ConversionTracker(client)
health = tracker.check_conversion_health("2425288235")

print(f"Score: {health['score']}/100")
for issue in health['issues']:
    print(f"- {issue['message']}")
```

## Architecture

```
conversions/
├── __init__.py          # Module exports
├── actions.py           # ConversionActionManager (CRUD)
├── enhanced.py          # EnhancedConversionsManager (hashing)
├── offline_sync.py      # HubSpotOfflineSync (HubSpot → Google Ads)
└── tracking.py          # ConversionTracker (diagnostics)
```

## Testing

```bash
# Run all tests
pytest tests/conversions/ -v

# Run specific test file
pytest tests/conversions/test_enhanced.py -v

# Run with coverage
pytest tests/conversions/ --cov=xwander_ads.conversions --cov-report=html
```

## Documentation

- **Full docs**: [docs/conversions.md](../../../docs/conversions.md)
- **Examples**: [examples/conversions_example.py](../../../examples/conversions_example.py)
- **API reference**: See inline docstrings

## Migration from Toolkit

If migrating from `/srv/xwander-platform/xwander.com/growth/toolkit/`:

**hubspot_sync.py → offline_sync.py**
```python
# Old
from toolkit.hubspot_sync import sync_hubspot_to_google_ads
sync_hubspot_to_google_ads(days=30, dry_run=True)

# New
from xwander_ads.conversions import HubSpotOfflineSync
syncer = HubSpotOfflineSync(client, token, customer_id, conversion_id)
syncer.sync(days=30, dry_run=True)
```

**conversion_manager.py → actions.py**
```python
# Old
from toolkit.conversion_manager import ConversionManager
manager = ConversionManager()
conversions = manager.list_conversions(customer_id)

# New
from xwander_ads.conversions import ConversionActionManager
manager = ConversionActionManager(client)
conversions = manager.list_conversions(customer_id)
```

## Best Practices

1. **Always normalize before hashing**
   - Use `normalize_email()`, `normalize_phone()`, etc.
   - Then hash with `sha256_hash()`

2. **Include as much data as possible for ECL**
   - Email + phone = 60-70% match rate
   - Email + phone + name + address = 70-80% match rate

3. **Use Booking Pipeline for conversions**
   - Booking = CONFIRMED deals (actual revenue)
   - Sales = pre-booking (leads being worked)

4. **Respect GCLID validity window**
   - Max 90 days for click-based attribution
   - Use `days=90` or less in HubSpot sync

5. **Run health checks weekly**
   - Activity rate should be >50%
   - Score should be >80
   - Diagnose any inactive conversions

## License

Part of xwander-ads plugin. See parent README for license.
