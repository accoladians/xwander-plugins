# Conversions Module

Comprehensive conversion tracking and management for Google Ads.

## Overview

The conversions module provides:

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

# Initialize client
client = get_google_ads_client()
customer_id = "2425288235"

# List conversions
manager = ConversionActionManager(client)
conversions = manager.list_conversions(customer_id)

print(f"Found {len(conversions)} conversion actions")
```

## Components

### 1. ConversionActionManager

Manage conversion actions via Google Ads API.

#### List Conversions

```python
manager = ConversionActionManager(client)

# List all enabled conversions
conversions = manager.list_conversions(customer_id)

# Include removed conversions
all_conversions = manager.list_conversions(customer_id, include_removed=True)

# Filter by status
enabled_only = manager.list_conversions(customer_id, status_filter="ENABLED")
```

#### Get Conversion Labels (for GTM)

```python
# Get conversion labels for GTM integration
labels = manager.get_conversion_labels(customer_id, webpage_only=True)

for name, info in labels.items():
    print(f"{name}:")
    print(f"  Conversion ID: {info['conversion_id']}")
    print(f"  Label: {info['conversion_label']}")
    print(f"  GTM Tag: AW-{info['conversion_id']}/{info['conversion_label']}")
```

#### Create Conversion

```python
result = manager.create_conversion(
    customer_id=customer_id,
    name="Bokun Purchase",
    category="PURCHASE",  # PURCHASE, SUBMIT_LEAD_FORM, SIGNUP, etc.
    conversion_type="WEBPAGE",
    value=100,  # Default value in EUR
    count_type="MANY_PER_CLICK",  # or ONE_PER_CLICK
    click_through_days=90,  # Attribution window
    view_through_days=1,
    include_in_goals=True  # Include in "Conversions" column
)

if result['success']:
    print(f"Created: {result['name']}")
    print(f"  Action ID: {result['action_id']}")
    print(f"  Label: {result['conversion_label']}")
```

#### Update Conversion

```python
# Pause a conversion
result = manager.update_conversion(
    customer_id=customer_id,
    conversion_id="7409115542",
    status="PAUSED"
)

# Update value settings
result = manager.update_conversion(
    customer_id=customer_id,
    conversion_id="7409115542",
    value=150,
    always_use_default_value=True
)

# Set as primary for goals (Smart Bidding)
result = manager.update_conversion(
    customer_id=customer_id,
    conversion_id="7409115542",
    primary_for_goal=True
)
```

### 2. EnhancedConversionsManager

Hash user data for Enhanced Conversions (ECW and ECL).

#### Hash User Data

```python
ec_manager = EnhancedConversionsManager(client)

# Hash customer data
hashed_data = ec_manager.hash_user_data(
    email="john.doe@gmail.com",
    phone="040 123 4567",
    first_name="John",
    last_name="Doe",
    street_address="123 Main St",
    city="Helsinki",
    region="Uusimaa",
    postal_code="00100",
    country_code="FI"
)

# Result:
# {
#     'hashed_email': 'a665a45920422f9d...',
#     'hashed_phone_number': 'b3d8f7e4...',
#     'hashed_first_name': 'f6e3c2a1...',
#     ...
# }
```

#### Normalization Rules

```python
# Email normalization
ec_manager.normalize_email("TEST@EXAMPLE.COM")
# -> "test@example.com"

ec_manager.normalize_email("john.doe@gmail.com")
# -> "johndoe@gmail.com" (Gmail dots removed)

# Phone normalization (E.164)
ec_manager.normalize_phone("040 123 4567")
# -> "+358401234567"

ec_manager.normalize_phone("+1 (555) 123-4567")
# -> "+15551234567"

# Name normalization
ec_manager.normalize_name("John O'Connor")
# -> "john oconnor"
```

#### Validate User Data

```python
validation = ec_manager.validate_user_data(
    email="test@example.com",
    phone="+358401234567",
    first_name="John"
)

if validation['valid']:
    print("Data is valid for Enhanced Conversions")
else:
    print("Issues:")
    for issue in validation['issues']:
        print(f"  - {issue}")

if validation['warnings']:
    print("Warnings:")
    for warning in validation['warnings']:
        print(f"  - {warning}")
```

### 3. HubSpotOfflineSync

Sync HubSpot deals to Google Ads as offline conversions.

#### Initialize Syncer

```python
import os

syncer = HubSpotOfflineSync(
    google_ads_client=client,
    hubspot_token=os.environ['HUBSPOT_ACCESS_TOKEN'],
    customer_id="2425288235",
    conversion_action_id="7409115542"  # HubSpot Deal Won
)
```

#### Dry Run (Preview)

```python
# Preview conversions ready to sync
results = syncer.sync(
    days=30,  # Look back 30 days
    pipeline="booking",  # Booking Pipeline (confirmed deals)
    source_filter="paid_search",  # Only PAID_SEARCH source
    limit=10,  # Preview first 10
    dry_run=True  # Don't upload
)

print(f"Deals found: {results['deals_found']}")
print(f"Conversions ready: {results['conversions_ready']}")
print(f"Total value: EUR {results['total_value']:,.2f}")
print(f"With GCLID: {results['gclid_count']}")
print(f"Email-only (ECL): {results['email_only_count']}")
```

#### Live Sync

```python
# Actually upload conversions
results = syncer.sync(
    days=90,  # Max 90 days for GCLID validity
    pipeline="booking",
    source_filter="paid_search",
    dry_run=False  # Upload to Google Ads
)

if results['uploaded'] > 0:
    print(f"Successfully uploaded {results['uploaded']} conversions")
    print(f"Total value: EUR {results['total_value']:,.2f}")
```

#### Pipeline Options

```python
# Booking Pipeline (confirmed deals - PRIMARY)
results = syncer.sync(pipeline="booking", dry_run=True)

# Sales Pipeline (pre-booking stage)
results = syncer.sync(pipeline="sales", dry_run=True)

# Ecommerce Pipeline (Bokun/WooCommerce)
results = syncer.sync(pipeline="ecommerce", dry_run=True)

# All pipelines
results = syncer.sync(pipeline="all", dry_run=True)
```

### 4. ConversionTracker

Conversion tracking health checks and diagnostics.

#### Check Account Health

```python
tracker = ConversionTracker(client)

health = tracker.check_conversion_health(customer_id, days=30)

print(f"Health Score: {health['score']}/100")
print(f"Status: {health['status']}")
print(f"Total conversions: {health['summary']['total_conversions']}")
print(f"Enabled: {health['summary']['enabled_conversions']}")
print(f"Active: {health['summary']['active_conversions']}")
print(f"Activity rate: {health['summary']['activity_rate']}")

# Show issues
for issue in health['issues']:
    print(f"[{issue['severity']}] {issue['message']}")
    print(f"  Fix: {issue['recommendation']}")
```

#### Diagnose Specific Conversion

```python
diagnosis = tracker.diagnose_conversion(
    customer_id=customer_id,
    conversion_id="7409115542",
    days=30
)

print(f"Conversion: {diagnosis['conversion']['name']}")
print(f"  Type: {diagnosis['conversion']['type']}")
print(f"  Status: {diagnosis['conversion']['status']}")
print(f"\nPerformance (last 30 days):")
print(f"  Conversions: {diagnosis['performance']['total_conversions']:.0f}")
print(f"  Value: EUR {diagnosis['performance']['total_value']:,.2f}")

if diagnosis['issues']:
    print("\nIssues:")
    for issue in diagnosis['issues']:
        print(f"  - {issue}")

if diagnosis['recommendations']:
    print("\nRecommendations:")
    for rec in diagnosis['recommendations']:
        print(f"  - {rec}")
```

## Use Cases

### Use Case 1: Setup New Conversion Actions

```python
manager = ConversionActionManager(client)

# Create standard conversions for xwander.com
conversions_to_create = [
    {
        "name": "Bokun Purchase",
        "category": "PURCHASE",
        "value": 100,
        "count_type": "MANY_PER_CLICK"
    },
    {
        "name": "Plan Your Holiday Form",
        "category": "SUBMIT_LEAD_FORM",
        "value": 50,
        "count_type": "ONE_PER_CLICK"
    },
    {
        "name": "Tour Inquiry Form",
        "category": "SUBMIT_LEAD_FORM",
        "value": 50,
        "count_type": "ONE_PER_CLICK"
    }
]

for conv in conversions_to_create:
    result = manager.create_conversion(
        customer_id=customer_id,
        **conv
    )
    if result['success']:
        print(f"Created: {result['name']}")
        print(f"  Label: {result['conversion_label']}")
```

### Use Case 2: Automated HubSpot Sync (Cron Job)

```python
#!/usr/bin/env python3
"""
Daily HubSpot -> Google Ads conversion sync
Run via cron: 0 2 * * * /path/to/hubspot_daily_sync.py
"""

import os
import logging
from xwander_ads.auth import get_google_ads_client
from xwander_ads.conversions import HubSpotOfflineSync

logging.basicConfig(level=logging.INFO)

def main():
    client = get_google_ads_client()

    syncer = HubSpotOfflineSync(
        google_ads_client=client,
        hubspot_token=os.environ['HUBSPOT_ACCESS_TOKEN'],
        customer_id="2425288235",
        conversion_action_id="7409115542"
    )

    # Sync last 7 days (covers any delays)
    results = syncer.sync(
        days=7,
        pipeline="booking",
        source_filter="paid_search",
        dry_run=False  # Actually upload
    )

    logging.info(f"Synced {results['uploaded']} conversions")
    logging.info(f"Total value: EUR {results['total_value']:,.2f}")

if __name__ == '__main__':
    main()
```

### Use Case 3: Weekly Conversion Health Report

```python
#!/usr/bin/env python3
"""
Weekly conversion health report
Run via cron: 0 9 * * 1 /path/to/weekly_health_report.py
"""

from xwander_ads.auth import get_google_ads_client
from xwander_ads.conversions import ConversionTracker

def main():
    client = get_google_ads_client()
    tracker = ConversionTracker(client)

    health = tracker.check_conversion_health("2425288235", days=7)

    print("="*70)
    print("WEEKLY CONVERSION HEALTH REPORT")
    print("="*70)
    print(f"Health Score: {health['score']}/100 ({health['status']})")
    print(f"Active conversions: {health['summary']['active_conversions']}")
    print(f"Last 7 days: {health['summary']['total_conversions_last_30d']:.0f} conversions")
    print(f"Total value: EUR {health['summary']['total_value_last_30d']:,.2f}")

    if health['issues']:
        print("\nCRITICAL ISSUES:")
        for issue in health['issues']:
            print(f"  - {issue['message']}")
            print(f"    Fix: {issue['recommendation']}")

if __name__ == '__main__':
    main()
```

## Best Practices

### Enhanced Conversions

1. **Always normalize before hashing**
   ```python
   # BAD: Hash raw data
   hashed = sha256_hash(email)  # Wrong!

   # GOOD: Normalize first
   normalized = normalize_email(email)
   hashed = sha256_hash(normalized)
   ```

2. **Include as much data as possible**
   - Email + phone = 60-70% match rate
   - Email + phone + name + address = 70-80% match rate

3. **Use GCLID when available**
   - GCLID = 95%+ match rate
   - Enhanced Conversions for Leads (ECL) is a fallback

### HubSpot Sync

1. **Use Booking Pipeline for conversions**
   - Booking Pipeline = CONFIRMED deals (actual revenue)
   - Sales Pipeline = pre-booking (leads being worked)

2. **Respect GCLID validity window**
   - Max 90 days for click-based attribution
   - Use `days=90` or less

3. **Filter for PAID_SEARCH source**
   - Avoids syncing organic/referral deals
   - `source_filter="paid_search"`

4. **Run daily, sync last 7 days**
   - Covers any HubSpot delays
   - Avoids missing conversions

### Health Monitoring

1. **Check health weekly**
   - Activity rate should be >50%
   - Score should be >80

2. **Diagnose inactive conversions**
   - 0 conversions in 30 days = broken tracking
   - Check GTM tags, triggers, GA4 integration

3. **Monitor conversion value**
   - Underreported value = missing revenue signal
   - Affects Smart Bidding optimization

## Troubleshooting

### Conversion Not Receiving Data

```python
tracker = ConversionTracker(client)
diagnosis = tracker.diagnose_conversion(customer_id, conversion_id)

# Check status
if diagnosis['conversion']['status'] != 'ENABLED':
    print("Conversion is not enabled!")

# Check performance
if diagnosis['performance']['total_conversions'] == 0:
    print("No conversions in last 30 days")

    if diagnosis['conversion']['type'] == 'WEBPAGE':
        print("Check GTM tag configuration")
    elif diagnosis['conversion']['type'] == 'UPLOAD_CLICKS':
        print("Check offline sync is running")
```

### HubSpot Sync Not Working

```python
# Check for deals
results = syncer.sync(days=30, pipeline="booking", dry_run=True)

print(f"Deals found: {results['deals_found']}")
print(f"Conversions ready: {results['conversions_ready']}")

# Check skip reasons
print(f"Skipped - no contact: {results['skipped_no_contact']}")
print(f"Skipped - no identifier: {results['skipped_no_identifier']}")
print(f"Skipped - Evaneos: {results['skipped_evaneos']}")

# If no GCLID, check GCLID capture
print(f"With GCLID: {results['gclid_count']}")
print(f"Email-only (ECL): {results['email_only_count']}")
```

### Low Match Rates (ECL)

```python
# Validate sample user data
validation = ec_manager.validate_user_data(
    email="test@example.com",
    phone="+358401234567"
)

# Check warnings
for warning in validation['warnings']:
    print(f"  - {warning}")

# Add more data for better matching
hashed_data = ec_manager.hash_user_data(
    email="test@example.com",
    phone="+358401234567",
    first_name="John",
    last_name="Doe",
    city="Helsinki",
    postal_code="00100",
    country_code="FI"
)
```

## API Reference

See inline docstrings for detailed parameter descriptions:

- `ConversionActionManager`: [actions.py](../xwander_ads/conversions/actions.py)
- `EnhancedConversionsManager`: [enhanced.py](../xwander_ads/conversions/enhanced.py)
- `HubSpotOfflineSync`: [offline_sync.py](../xwander_ads/conversions/offline_sync.py)
- `ConversionTracker`: [tracking.py](../xwander_ads/conversions/tracking.py)

## Examples

See [examples/conversions_example.py](../examples/conversions_example.py) for complete working examples.
