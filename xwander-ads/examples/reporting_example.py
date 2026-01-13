#!/usr/bin/env python3
"""
Example usage of xwander-ads reporting module.

This script demonstrates:
- Building GAQL queries with GAQLBuilder
- Using pre-built query templates
- Executing queries
- Exporting results to different formats
"""

from xwander_ads.reporting import (
    GAQLBuilder,
    templates,
    execute_query,
    export_results,
    TableFormatter,
    format_query,
)
from xwander_ads.auth import get_client


def example_1_basic_query():
    """Example 1: Build and execute a basic query."""
    print("\n=== Example 1: Basic Query Builder ===\n")

    # Build query
    query = (
        GAQLBuilder()
        .select('campaign.id', 'campaign.name', 'campaign.status')
        .from_resource('campaign')
        .where('campaign.status != REMOVED')
        .limit(10)
        .build()
    )

    # Show formatted query
    print("Query:")
    print(format_query(query))
    print()

    # Execute (requires authentication)
    # client = get_client()
    # results = execute_query(client, '2425288235', query)
    # print(f"Found {len(results)} campaigns")


def example_2_campaign_performance():
    """Example 2: Campaign performance report."""
    print("\n=== Example 2: Campaign Performance Report ===\n")

    # Use pre-built template
    query = templates.campaign_performance(
        days=7,
        enabled_only=True,
        limit=20
    )

    print("Query:")
    print(format_query(query))
    print()

    # Execute and format (requires authentication)
    # client = get_client()
    # results = execute_query(client, '2425288235', query)
    # print(TableFormatter.format_performance(results))


def example_3_search_terms():
    """Example 3: Search terms analysis."""
    print("\n=== Example 3: Search Terms Report ===\n")

    query = templates.search_terms(
        days=14,
        campaign_id='12345678',  # Optional: filter by campaign
        limit=50
    )

    print("Query:")
    print(format_query(query))
    print()


def example_4_custom_query():
    """Example 4: Custom query with multiple conditions."""
    print("\n=== Example 4: Custom Query ===\n")

    query = (
        GAQLBuilder()
        .select(
            'campaign.id',
            'campaign.name',
            'ad_group.id',
            'ad_group.name',
            'metrics.impressions',
            'metrics.clicks',
            'metrics.ctr',
            'metrics.cost_micros',
            'metrics.conversions'
        )
        .from_resource('ad_group')
        .where('campaign.status = ENABLED')
        .where('ad_group.status = ENABLED')
        .during('LAST_30_DAYS')
        .order_by('metrics.conversions', desc=True)
        .limit(50)
        .build()
    )

    print("Query:")
    print(format_query(query))
    print()


def example_5_conversion_performance():
    """Example 5: Conversion action performance."""
    print("\n=== Example 5: Conversion Performance ===\n")

    query = templates.conversion_performance(days=30, limit=25)

    print("Query:")
    print(format_query(query))
    print()


def example_6_export_formats():
    """Example 6: Export to different formats."""
    print("\n=== Example 6: Export Formats ===\n")

    # Sample data
    results = [
        {
            'campaign.name': 'Northern Lights Tours',
            'metrics.clicks': 1523,
            'metrics.cost_micros': 15230000,
            'metrics.conversions': 43.5,
        },
        {
            'campaign.name': 'Husky Sledding',
            'metrics.clicks': 892,
            'metrics.cost_micros': 8920000,
            'metrics.conversions': 21.3,
        },
    ]

    # Export to CSV file
    # export_results(results, '/tmp/report.csv', format='csv')
    # print("Exported to: /tmp/report.csv")

    # Export to JSON
    # export_results(results, '/tmp/report.json', format='json')
    # print("Exported to: /tmp/report.json")

    # Export to Markdown
    # export_results(results, '/tmp/report.md', format='markdown', title="Campaign Report")
    # print("Exported to: /tmp/report.md")

    print("Export examples (uncomment to run):")
    print("  - CSV: export_results(results, '/tmp/report.csv', format='csv')")
    print("  - JSON: export_results(results, '/tmp/report.json', format='json')")
    print("  - Markdown: export_results(results, '/tmp/report.md', format='markdown')")


def example_7_asset_group_performance():
    """Example 7: Performance Max asset group performance."""
    print("\n=== Example 7: Asset Group Performance (Performance Max) ===\n")

    query = templates.asset_group_performance(
        campaign_id='12345678',
        days=30,
        limit=20
    )

    print("Query:")
    print(format_query(query))
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("xwander-ads Reporting Module Examples")
    print("=" * 70)

    example_1_basic_query()
    example_2_campaign_performance()
    example_3_search_terms()
    example_4_custom_query()
    example_5_conversion_performance()
    example_6_export_formats()
    example_7_asset_group_performance()

    print("\n" + "=" * 70)
    print("\nNote: Query execution examples are commented out.")
    print("To execute queries, uncomment the lines that call:")
    print("  - get_client()")
    print("  - execute_query()")
    print("  - export_results()")
    print("\nMake sure you have valid Google Ads credentials in ~/.google-ads.yaml")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
