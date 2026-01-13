#!/usr/bin/env python3
"""
Xwander Ads - Conversions Module Examples

Demonstrates usage of the conversions module including:
- Listing and managing conversion actions
- Enhanced conversions with user data hashing
- HubSpot offline conversion sync
- Conversion tracking diagnostics
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from xwander_ads.auth import get_google_ads_client
from xwander_ads.conversions import (
    ConversionActionManager,
    EnhancedConversionsManager,
    HubSpotOfflineSync,
    ConversionTracker
)


def example_list_conversions():
    """Example: List all conversion actions"""
    print("\n" + "="*70)
    print("EXAMPLE 1: List Conversion Actions")
    print("="*70)

    client = get_google_ads_client()
    manager = ConversionActionManager(client)

    customer_id = "2425288235"

    # List all enabled conversions
    conversions = manager.list_conversions(customer_id, include_removed=False)

    print(f"\nFound {len(conversions)} enabled conversion actions:\n")

    for conv in conversions[:5]:  # Show first 5
        print(f"ID: {conv['id']}")
        print(f"  Name: {conv['name']}")
        print(f"  Type: {conv['type']}")
        print(f"  Category: {conv['category']}")
        print(f"  Status: {conv['status']}")
        print(f"  Primary: {conv['primary_for_goal']}")
        print()


def example_get_conversion_labels():
    """Example: Get conversion labels for GTM"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Get Conversion Labels for GTM")
    print("="*70)

    client = get_google_ads_client()
    manager = ConversionActionManager(client)

    customer_id = "2425288235"

    # Get labels for WEBPAGE conversions (for GTM integration)
    labels = manager.get_conversion_labels(customer_id, webpage_only=True)

    print(f"\nConversion Labels for GTM:\n")

    for name, info in list(labels.items())[:5]:  # Show first 5
        print(f"{name}:")
        print(f"  Conversion ID: {info['conversion_id']}")
        print(f"  Label: {info['conversion_label']}")
        print(f"  Category: {info['category']}")
        print()


def example_hash_user_data():
    """Example: Hash user data for Enhanced Conversions"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Hash User Data for Enhanced Conversions")
    print("="*70)

    client = get_google_ads_client()
    ec_manager = EnhancedConversionsManager(client)

    # Example customer data
    customer_data = {
        'email': 'john.doe@gmail.com',
        'phone': '040 123 4567',
        'first_name': 'John',
        'last_name': 'Doe',
        'city': 'Helsinki',
        'postal_code': '00100',
        'country_code': 'FI'
    }

    print("\nOriginal data:")
    for key, value in customer_data.items():
        print(f"  {key}: {value}")

    # Hash the data
    hashed_data = ec_manager.hash_user_data(**customer_data)

    print("\nHashed data (SHA-256):")
    for key, value in hashed_data.items():
        print(f"  {key}: {value[:32]}...")  # Show first 32 chars

    # Validate the data
    validation = ec_manager.validate_user_data(**customer_data)

    print(f"\nValidation:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Issues: {len(validation['issues'])}")
    print(f"  Warnings: {len(validation['warnings'])}")

    if validation['warnings']:
        print("\n  Warnings:")
        for warning in validation['warnings']:
            print(f"    - {warning}")


def example_hubspot_sync_dry_run():
    """Example: HubSpot offline conversion sync (dry run)"""
    print("\n" + "="*70)
    print("EXAMPLE 4: HubSpot Offline Conversion Sync (Dry Run)")
    print("="*70)

    # Get credentials
    client = get_google_ads_client()
    hubspot_token = os.environ.get('HUBSPOT_ACCESS_TOKEN')

    if not hubspot_token:
        print("\nERROR: HUBSPOT_ACCESS_TOKEN not set")
        print("Set environment variable: export HUBSPOT_ACCESS_TOKEN=your_token")
        return

    # Initialize sync
    syncer = HubSpotOfflineSync(
        google_ads_client=client,
        hubspot_token=hubspot_token,
        customer_id="2425288235",
        conversion_action_id="7409115542"  # HubSpot Deal Won
    )

    # Dry run: preview conversions ready to sync
    results = syncer.sync(
        days=30,
        pipeline="booking",  # Booking Pipeline (confirmed deals)
        source_filter="paid_search",  # Only PAID_SEARCH source
        limit=10,
        dry_run=True  # Don't actually upload
    )

    print(f"\nSync Results (Dry Run):")
    print(f"  Deals found: {results['deals_found']}")
    print(f"  Conversions ready: {results['conversions_ready']}")
    print(f"  Total value: EUR {results['total_value']:,.2f}")
    print(f"\n  Attribution breakdown:")
    print(f"    With GCLID: {results['gclid_count']}")
    print(f"    Email-only (ECL): {results['email_only_count']}")
    print(f"\n  Skipped:")
    print(f"    No contact: {results['skipped_no_contact']}")
    print(f"    No identifier: {results['skipped_no_identifier']}")
    print(f"    Evaneos deals: {results['skipped_evaneos']}")

    print("\nTo upload: Set dry_run=False")


def example_check_conversion_health():
    """Example: Check conversion tracking health"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Check Conversion Tracking Health")
    print("="*70)

    client = get_google_ads_client()
    tracker = ConversionTracker(client)

    customer_id = "2425288235"

    # Check overall health
    health = tracker.check_conversion_health(customer_id, days=30)

    print(f"\nConversion Tracking Health Report:")
    print(f"  Score: {health['score']}/100")
    print(f"  Status: {health['status']}")
    print(f"\n  Summary:")
    print(f"    Total conversions: {health['summary']['total_conversions']}")
    print(f"    Enabled: {health['summary']['enabled_conversions']}")
    print(f"    Active (receiving data): {health['summary']['active_conversions']}")
    print(f"    Activity rate: {health['summary']['activity_rate']}")
    print(f"\n  Last 30 days:")
    print(f"    Total conversions: {health['summary']['total_conversions_last_30d']:.0f}")
    print(f"    Total value: EUR {health['summary']['total_value_last_30d']:,.2f}")

    # Show critical issues
    if health['issues']:
        print(f"\n  Critical Issues ({len(health['issues'])}):")
        for issue in health['issues']:
            print(f"    - [{issue['severity']}] {issue['message']}")
            if 'recommendation' in issue:
                print(f"      Fix: {issue['recommendation']}")

    # Show warnings
    if health['warnings']:
        print(f"\n  Warnings ({len(health['warnings'])}):")
        for warning in health['warnings'][:3]:  # Show first 3
            print(f"    - {warning['message']}")


def example_diagnose_conversion():
    """Example: Diagnose a specific conversion action"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Diagnose Specific Conversion Action")
    print("="*70)

    client = get_google_ads_client()
    tracker = ConversionTracker(client)

    customer_id = "2425288235"
    conversion_id = "7409115542"  # HubSpot Deal Won

    # Diagnose conversion
    diagnosis = tracker.diagnose_conversion(customer_id, conversion_id, days=30)

    print(f"\nConversion: {diagnosis['conversion']['name']}")
    print(f"  ID: {diagnosis['conversion']['id']}")
    print(f"  Type: {diagnosis['conversion']['type']}")
    print(f"  Category: {diagnosis['conversion']['category']}")
    print(f"  Status: {diagnosis['conversion']['status']}")
    print(f"  Primary for goals: {diagnosis['conversion']['primary_for_goal']}")
    print(f"\n  Attribution windows:")
    print(f"    Click-through: {diagnosis['conversion']['click_through_days']} days")
    print(f"    View-through: {diagnosis['conversion']['view_through_days']} days")
    print(f"\n  Value settings:")
    print(f"    Default value: EUR {diagnosis['conversion']['default_value']}")
    print(f"    Always use default: {diagnosis['conversion']['always_use_default_value']}")

    print(f"\n  Performance (last 30 days):")
    print(f"    Total conversions: {diagnosis['performance']['total_conversions']:.0f}")
    print(f"    Total value: EUR {diagnosis['performance']['total_value']:,.2f}")

    # Show issues
    if diagnosis['issues']:
        print(f"\n  Issues ({len(diagnosis['issues'])}):")
        for issue in diagnosis['issues']:
            print(f"    - {issue}")

    # Show recommendations
    if diagnosis['recommendations']:
        print(f"\n  Recommendations:")
        for rec in diagnosis['recommendations']:
            print(f"    - {rec}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("Xwander Ads - Conversions Module Examples")
    print("="*70)

    try:
        # Run examples
        example_list_conversions()
        example_get_conversion_labels()
        example_hash_user_data()
        example_hubspot_sync_dry_run()
        example_check_conversion_health()
        example_diagnose_conversion()

        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
