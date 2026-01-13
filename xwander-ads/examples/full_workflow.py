#!/usr/bin/env python3
"""
Complete workflow example: Query -> Execute -> Export

This demonstrates a full reporting workflow from building a query
to exporting results in multiple formats.
"""

from xwander_ads.reporting import (
    GAQLBuilder,
    templates,
    format_query,
    export_to_string,
)


def main():
    print("\n" + "=" * 70)
    print("xwander-ads Complete Reporting Workflow")
    print("=" * 70 + "\n")

    # Step 1: Build a custom query
    print("STEP 1: Build GAQL Query")
    print("-" * 70)

    query = (
        GAQLBuilder()
        .select(
            'campaign.id',
            'campaign.name',
            'campaign.status',
            'metrics.impressions',
            'metrics.clicks',
            'metrics.ctr',
            'metrics.cost_micros',
            'metrics.conversions'
        )
        .from_resource('campaign')
        .where('campaign.status = ENABLED')
        .during('LAST_7_DAYS')
        .order_by('metrics.cost_micros', desc=True)
        .limit(20)
        .build()
    )

    print("Built query:")
    print(format_query(query))
    print()

    # Step 2: Simulate query results (in real use, this would be execute_query())
    print("\nSTEP 2: Execute Query (simulated)")
    print("-" * 70)

    # Simulated results
    results = [
        {
            'campaign.id': '123456789',
            'campaign.name': 'Northern Lights Tours - Winter 2025',
            'campaign.status': 'ENABLED',
            'metrics.impressions': 15234,
            'metrics.clicks': 892,
            'metrics.ctr': 0.0586,
            'metrics.cost_micros': 15230000,  # EUR 15.23
            'metrics.conversions': 23.5,
        },
        {
            'campaign.id': '987654321',
            'campaign.name': 'Husky Sledding Experience',
            'campaign.status': 'ENABLED',
            'metrics.impressions': 8432,
            'metrics.clicks': 456,
            'metrics.ctr': 0.0541,
            'metrics.cost_micros': 8920000,  # EUR 8.92
            'metrics.conversions': 12.3,
        },
        {
            'campaign.id': '555555555',
            'campaign.name': 'Aurora Hunting Tours',
            'campaign.status': 'ENABLED',
            'metrics.impressions': 6234,
            'metrics.clicks': 321,
            'metrics.ctr': 0.0515,
            'metrics.cost_micros': 5430000,  # EUR 5.43
            'metrics.conversions': 8.7,
        },
    ]

    print(f"Query returned {len(results)} campaigns")
    print()

    # Step 3: Export to CSV
    print("\nSTEP 3: Export to CSV")
    print("-" * 70)

    csv_output = export_to_string(results, format='csv')
    print(csv_output)
    print()

    # Step 4: Export to JSON
    print("\nSTEP 4: Export to JSON")
    print("-" * 70)

    json_output = export_to_string(results, format='json')
    print(json_output)
    print()

    # Step 5: Show how to use templates
    print("\nSTEP 5: Using Pre-built Templates")
    print("-" * 70)

    # Campaign performance template
    perf_query = templates.campaign_performance(days=30, limit=50)
    print("Campaign Performance Template (30 days):")
    print(format_query(perf_query))
    print()

    # Search terms template
    search_query = templates.search_terms(days=14, limit=100)
    print("\nSearch Terms Template (14 days):")
    print(format_query(search_query))
    print()

    # Asset group performance template
    asset_query = templates.asset_group_performance(
        campaign_id='123456789',
        days=7
    )
    print("\nAsset Group Performance Template (7 days):")
    print(format_query(asset_query))
    print()

    print("=" * 70)
    print("\nWorkflow complete!")
    print("\nTo use with real data:")
    print("  1. Get authenticated client: client = get_client()")
    print("  2. Execute query: results = execute_query(client, customer_id, query)")
    print("  3. Export results: export_results(results, 'output.csv', format='csv')")
    print("\nOr use the CLI:")
    print("  xw ads report performance --customer-id 2425288235 --days 7")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
