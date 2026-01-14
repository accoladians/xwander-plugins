"""CLI entry point for xwander-ads plugin.

This module provides the command-line interface for Google Ads operations.
Registered as 'xw ads' command via plugin.json.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .auth import get_client, test_auth
from .exceptions import AdsError
from . import pmax
from . import reporting
from . import recommendations
from .conversions.actions import ConversionActionManager


def normalize_customer_id(customer_id: str) -> str:
    """Remove hyphens from customer ID."""
    return customer_id.replace('-', '')


def format_micros(micros: int, currency: str = "EUR") -> str:
    """Format micros as currency."""
    return f"{currency} {micros / 1_000_000:,.2f}"


def handle_pmax_list(args):
    """Handle 'xw ads pmax list' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    if args.campaigns:
        # List campaigns
        campaigns = pmax.list_campaigns(client, customer_id, enabled_only=args.enabled_only)

        print(f"\n=== Performance Max Campaigns ({len(campaigns)}) ===\n")
        for c in campaigns:
            budget = format_micros(c['budget_micros'])
            cost = format_micros(c['cost_micros'])
            print(f"  {c['id']}: {c['name']}")
            print(f"    Status: {c['status']} | Budget: {budget} | Spent: {cost}")
            print(f"    Impressions: {c['impressions']:,} | Clicks: {c['clicks']:,} | Conversions: {c['conversions']:.1f}")
            print()

    elif args.asset_groups:
        # List asset groups
        campaign_id = args.campaign_id if hasattr(args, 'campaign_id') else None
        asset_groups = pmax.list_asset_groups(client, customer_id, campaign_id)

        print(f"\n=== Asset Groups ({len(asset_groups)}) ===\n")
        for ag in asset_groups:
            print(f"  {ag['id']}: {ag['name']}")
            print(f"    Campaign: {ag['campaign_id']} | Status: {ag['status']}")
            print()

    else:
        print("Error: Specify --campaigns or --asset-groups")
        sys.exit(1)


def handle_pmax_signals(args):
    """Handle 'xw ads pmax signals' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    if args.action == 'list':
        signals = pmax.list_signals(client, customer_id, args.asset_group_id)
        print(f"\n=== Asset Group {args.asset_group_id} Search Themes ({len(signals)}) ===\n")
        for i, sig in enumerate(signals, 1):
            print(f"  {i}. \"{sig['text']}\"")
        print()

    elif args.action == 'add':
        if not args.theme:
            print("Error: --theme required for add action")
            sys.exit(1)

        resource_name = pmax.add_search_theme(
            client, customer_id, args.asset_group_id, args.theme
        )
        print(f"✓ Added search theme: \"{args.theme}\"")
        print(f"  Resource: {resource_name}")

    elif args.action == 'bulk':
        if not args.file:
            print("Error: --file required for bulk action")
            sys.exit(1)

        themes_file = Path(args.file)
        if not themes_file.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)

        with open(themes_file, 'r') as f:
            themes = [line.strip() for line in f if line.strip()]

        print(f"\nAdding {len(themes)} search themes to asset group {args.asset_group_id}...\n")

        results = pmax.bulk_add_themes(client, customer_id, args.asset_group_id, themes)

        print(f"\n✓ Successfully added {len(results)} themes")

    elif args.action == 'remove':
        if not args.resource_name:
            print("Error: --resource-name required for remove action")
            sys.exit(1)

        pmax.remove_signal(client, customer_id, args.resource_name)
        print(f"✓ Removed signal: {args.resource_name}")


def handle_pmax_get(args):
    """Handle 'xw ads pmax get' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    if args.campaign_id:
        # Get campaign details
        campaign = pmax.get_campaign(client, customer_id, args.campaign_id)

        print(f"\n=== Campaign {campaign['id']}: {campaign['name']} ===\n")
        print(f"  Status: {campaign['status']}")
        print(f"  Budget: {format_micros(campaign['budget_micros'])}")
        print(f"  Spent: {format_micros(campaign['cost_micros'])}")
        print(f"  Impressions: {campaign['impressions']:,}")
        print(f"  Clicks: {campaign['clicks']:,}")
        print(f"  Conversions: {campaign['conversions']:.1f}")
        print(f"  Conversion Value: {format_micros(int(campaign['conversions_value']))}")

        if campaign['target_cpa_micros']:
            print(f"  Target CPA: {format_micros(campaign['target_cpa_micros'])}")
        if campaign['target_roas']:
            print(f"  Target ROAS: {campaign['target_roas']:.2f}")

        print()


def handle_report(args):
    """Handle 'xw ads report' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    # Build query based on report type
    if args.report_type == 'performance':
        query = reporting.templates.campaign_performance(
            days=args.days,
            enabled_only=args.enabled_only,
            limit=args.limit
        )
    elif args.report_type == 'conversions':
        query = reporting.templates.conversion_performance(
            days=args.days,
            limit=args.limit
        )
    elif args.report_type == 'search-terms':
        query = reporting.templates.search_terms(
            days=args.days,
            campaign_id=args.campaign_id,
            limit=args.limit
        )
    elif args.report_type == 'asset-groups':
        query = reporting.templates.asset_group_performance(
            campaign_id=args.campaign_id,
            days=args.days,
            limit=args.limit
        )
    else:
        print(f"Error: Unknown report type: {args.report_type}")
        sys.exit(1)

    # Show query if requested
    if args.show_query:
        print("Query:")
        print(reporting.format_query(query))
        print()

    # Execute query
    results = reporting.execute_query(client, customer_id, query)

    # Output results
    if args.output:
        # Export to file
        output_file = reporting.export_results(
            results,
            args.output,
            format=args.format
        )
        print(f"\nExported {len(results)} rows to: {output_file}")
    else:
        # Print to stdout
        if args.format == 'table':
            if args.report_type == 'performance':
                print(reporting.TableFormatter.format_performance(results))
            else:
                print(reporting.TableFormatter.format(results))
        elif args.format == 'csv':
            print(reporting.export_to_string(results, format='csv'))
        elif args.format == 'json':
            print(reporting.export_to_string(results, format='json'))
        else:
            print(f"Error: Unknown format: {args.format}")
            sys.exit(1)


def handle_recommendations(args):
    """Handle 'xw ads recs' command - fetch recommendations from API."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    recs = recommendations.fetch_recommendations(
        client, customer_id,
        types=args.types.split(',') if args.types else None,
        limit=args.limit
    )

    if args.format == 'json':
        print(json.dumps(recs, indent=2))
    else:
        print(f"\n=== Google Ads Recommendations ({len(recs)}) ===\n")
        for rec in recs:
            campaign = rec.get('campaign_name') or 'Account-level'
            print(f"  {rec['type']}: {campaign}")
        print()


def handle_query(args):
    """Handle 'xw ads query' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    # Get query from args or file
    if args.file:
        query_file = Path(args.file)
        if not query_file.exists():
            print(f"Error: Query file not found: {args.file}")
            sys.exit(1)
        query = query_file.read_text().strip()
    else:
        query = args.query

    # Validate query
    try:
        reporting.validate_query(query)
    except ValueError as e:
        print(f"Error: Invalid query: {e}")
        sys.exit(1)

    # Show formatted query if requested
    if args.show_query:
        print("Query:")
        print(reporting.format_query(query))
        print()

    # Execute query
    results = reporting.execute_query(client, customer_id, query)

    # Output results
    if args.output:
        # Export to file
        output_file = reporting.export_results(
            results,
            args.output,
            format=args.format
        )
        print(f"\nExported {len(results)} rows to: {output_file}")
    else:
        # Print to stdout
        if args.format == 'table':
            print(reporting.TableFormatter.format(results))
        elif args.format == 'csv':
            print(reporting.export_to_string(results, format='csv'))
        elif args.format == 'json':
            print(reporting.export_to_string(results, format='json'))
        else:
            print(f"Error: Unknown format: {args.format}")
            sys.exit(1)


def handle_conversion_list(args):
    """Handle 'xw ads conversion list' command."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    manager = ConversionActionManager(client)
    conversions = manager.list_conversions(customer_id, include_removed=False)

    if args.format == 'json':
        print(json.dumps(conversions, indent=2))
    else:
        # Table format
        print(f"\n=== Conversion Actions ({len(conversions)}) ===\n")
        for conv in conversions:
            primary = "PRIMARY" if conv['primary_for_goal'] else "SECONDARY"
            value = f"€{conv['default_value']:.2f}" if conv['default_value'] else "Variable"
            print(f"  {conv['id']}: {conv['name']}")
            print(f"    Type: {conv['type']} | Category: {conv['category']}")
            print(f"    Status: {conv['status']} | Goal: {primary} | Value: {value}")
            if conv.get('tag_info', {}).get('conversion_label'):
                print(f"    Label: {conv['tag_info']['conversion_label']}")
            print()


def handle_conversion_create(args):
    """Handle 'xw ads conversion create' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    manager = ConversionActionManager(client)

    # Determine include_in_goals based on --secondary flag
    include_in_goals = not args.secondary

    result = manager.create_conversion(
        customer_id=customer_id,
        name=args.name,
        category=args.category,
        value=args.value,
        include_in_goals=include_in_goals
    )

    print(f"\n✓ Created conversion action: {result['name']}")
    print(f"  Action ID: {result['action_id']}")
    print(f"  Conversion ID: {result['conversion_id']}")
    print(f"  Conversion Label: {result['conversion_label']}")
    print(f"  Goal Setting: {'SECONDARY' if args.secondary else 'PRIMARY'}")
    print()


def handle_conversion_update(args):
    """Handle 'xw ads conversion update' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    manager = ConversionActionManager(client)

    # Build updates dictionary from provided arguments
    updates = {}

    if args.name:
        updates['name'] = args.name

    if args.value is not None:
        updates['value'] = args.value

    if args.status:
        updates['status'] = args.status

    # Handle primary/secondary flags (mutually exclusive)
    if args.primary and args.secondary:
        print("Error: Cannot specify both --primary and --secondary")
        sys.exit(1)

    if args.primary:
        updates['primary_for_goal'] = True
    elif args.secondary:
        updates['primary_for_goal'] = False

    if not updates:
        print("Error: No updates specified. Use --name, --value, --status, --primary, or --secondary")
        sys.exit(1)

    result = manager.update_conversion(
        customer_id=customer_id,
        conversion_id=args.conversion_id,
        **updates
    )

    print(f"\n✓ Updated conversion {args.conversion_id}")
    print(f"  Updated fields: {', '.join(result['updated_fields'])}")
    print()


def handle_conversion_remove(args):
    """Handle 'xw ads conversion remove' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    manager = ConversionActionManager(client)

    result = manager.remove_conversion(
        customer_id=customer_id,
        conversion_id=args.conversion_id
    )

    print(f"\n✓ Removed conversion {args.conversion_id}")
    print()


def handle_conversion_labels(args):
    """Handle 'xw ads conversion labels' command."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    manager = ConversionActionManager(client)
    labels = manager.get_conversion_labels(customer_id, webpage_only=True)

    if args.format == 'json':
        print(json.dumps(labels, indent=2))
    else:
        # Table format
        print(f"\n=== Conversion Labels for GTM ({len(labels)}) ===\n")
        for name, info in labels.items():
            print(f"  {name}")
            print(f"    Conversion ID: AW-{info['conversion_id']}")
            print(f"    Label: {info['conversion_label']}")
            print(f"    Category: {info['category']}")
            print()


def main(args=None):
    """Main CLI entry point.

    Args:
        args: Optional argument list for testing and integration.
              If None, uses sys.argv (default behavior).

    Usage:
        # From CLI
        $ xw ads pmax list --customer-id 2425288235 --campaigns

        # From Python code
        from xwander_ads.cli import main
        main(['pmax', 'list', '--customer-id', '2425288235', '--campaigns'])
    """
    parser = argparse.ArgumentParser(
        description='Google Ads CLI - Performance Max operations',
        prog='xw ads',
        epilog='''
Common workflows:
  # List all campaigns
  xw ads pmax list --customer-id 2425288235 --campaigns

  # Get campaign details
  xw ads pmax get --customer-id 2425288235 --campaign-id 23423204148

  # Add search themes
  xw ads pmax signals add --customer-id 2425288235 --asset-group-id 12345 --theme "northern lights tours"

  # Performance report
  xw ads report performance --customer-id 2425288235 --days 30 --format table
        '''
    )

    parser.add_argument(
        '--api-version',
        choices=['v20', 'v21', 'v22'],
        default='v20',
        help='Google Ads API version (default: v20)'
    )

    subparsers = parser.add_subparsers(dest='module', help='Module')

    # ========== PMAX MODULE ==========
    pmax_parser = subparsers.add_parser('pmax', help='Performance Max operations')
    pmax_subs = pmax_parser.add_subparsers(dest='command', help='Command')

    # pmax list
    list_parser = pmax_subs.add_parser(
        'list',
        help='List campaigns or asset groups',
        epilog='Examples:\n'
               '  xw ads pmax list --customer-id 2425288235 --campaigns\n'
               '  xw ads pmax list --customer-id 2425288235 --asset-groups\n'
               '  xw ads pmax list --customer-id 2425288235 --asset-groups --campaign-id 23423204148',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    list_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    list_parser.add_argument('--campaigns', action='store_true', help='List campaigns')
    list_parser.add_argument('--asset-groups', action='store_true', help='List asset groups')
    list_parser.add_argument('--campaign-id', help='Filter asset groups by campaign ID')
    list_parser.add_argument('--enabled-only', action='store_true', help='Only show enabled campaigns')

    # pmax get
    get_parser = pmax_subs.add_parser(
        'get',
        help='Get campaign details',
        epilog='Example:\n'
               '  xw ads pmax get --customer-id 2425288235 --campaign-id 23423204148',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    get_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    get_parser.add_argument('--campaign-id', required=True, help='Campaign ID (e.g., 23423204148)')

    # pmax signals
    signals_parser = pmax_subs.add_parser(
        'signals',
        help='Manage search themes (audience signals)',
        epilog='Examples:\n'
               '  # List current themes\n'
               '  xw ads pmax signals list --customer-id 2425288235 --asset-group-id 12345\n\n'
               '  # Add single theme\n'
               '  xw ads pmax signals add --customer-id 2425288235 --asset-group-id 12345 --theme "northern lights"\n\n'
               '  # Bulk add from file\n'
               '  xw ads pmax signals bulk --customer-id 2425288235 --asset-group-id 12345 --file themes.txt',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    signals_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    signals_parser.add_argument('--asset-group-id', required=True, help='Asset group ID (e.g., 12345678901)')
    signals_parser.add_argument(
        'action',
        choices=['list', 'add', 'bulk', 'remove'],
        help='Action: list (show themes) | add (single theme) | bulk (from file) | remove (delete theme)'
    )
    signals_parser.add_argument('--theme', help='Search theme text (for add action)')
    signals_parser.add_argument('--file', help='File with themes, one per line (for bulk action)')
    signals_parser.add_argument('--resource-name', help='Signal resource name (for remove action)')

    # ========== REPORT MODULE ==========
    report_parser = subparsers.add_parser(
        'report',
        help='Generate reports',
        epilog='Examples:\n'
               '  # Campaign performance (last 7 days)\n'
               '  xw ads report performance --customer-id 2425288235\n\n'
               '  # Conversion tracking (last 30 days, CSV)\n'
               '  xw ads report conversions --customer-id 2425288235 --days 30 --format csv\n\n'
               '  # Search terms for specific campaign\n'
               '  xw ads report search-terms --customer-id 2425288235 --campaign-id 23423204148',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    report_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    report_parser.add_argument(
        'report_type',
        choices=['performance', 'conversions', 'search-terms', 'asset-groups'],
        help='Report type: performance (campaign metrics) | conversions (tracking) | search-terms (queries) | asset-groups (ad groups)'
    )
    report_parser.add_argument('--days', type=int, default=7, help='Number of days to include (default: 7)')
    report_parser.add_argument('--limit', type=int, default=50, help='Max rows to return (default: 50, max: 10000)')
    report_parser.add_argument('--campaign-id', help='Filter by campaign ID (required for search-terms/asset-groups)')
    report_parser.add_argument('--enabled-only', action='store_true', help='Only include enabled items')
    report_parser.add_argument(
        '--format',
        choices=['table', 'csv', 'json'],
        default='table',
        help='Output format: table (human-readable) | csv (spreadsheet) | json (API) - default: table'
    )
    report_parser.add_argument('--output', help='Output file path (default: stdout)')
    report_parser.add_argument('--show-query', action='store_true', help='Display GAQL query before results')

    # ========== QUERY MODULE ==========
    query_parser = subparsers.add_parser(
        'query',
        help='Execute custom GAQL query',
        epilog='Examples:\n'
               '  # Simple query\n'
               '  xw ads query --customer-id 2425288235 "SELECT campaign.name FROM campaign LIMIT 10"\n\n'
               '  # Query from file\n'
               '  xw ads query --customer-id 2425288235 --file my-query.gaql --format csv\n\n'
               '  # Export to file\n'
               '  xw ads query --customer-id 2425288235 --file complex-query.gaql --output results.json --format json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    query_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    query_parser.add_argument('query', nargs='?', help='GAQL query string (must include LIMIT clause)')
    query_parser.add_argument('--file', help='Read query from file (alternative to query string)')
    query_parser.add_argument(
        '--format',
        choices=['table', 'csv', 'json'],
        default='table',
        help='Output format: table | csv | json - default: table'
    )
    query_parser.add_argument('--output', help='Output file path (default: stdout)')
    query_parser.add_argument('--show-query', action='store_true', help='Show formatted query before execution')

    # ========== RECOMMENDATIONS MODULE ==========
    recs_parser = subparsers.add_parser(
        'recs',
        help='Fetch recommendations from Google Ads API',
        epilog='Examples:\n'
               '  xw ads recs --customer-id 2425288235\n'
               '  xw ads recs --customer-id 2425288235 --format json\n'
               '  xw ads recs --customer-id 2425288235 --types KEYWORD,CAMPAIGN_BUDGET',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    recs_parser.add_argument('--customer-id', required=True, help='Customer ID')
    recs_parser.add_argument('--types', help='Filter by types (comma-separated)')
    recs_parser.add_argument('--limit', type=int, default=100, help='Max recommendations (default: 100)')
    recs_parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')

    # ========== CONVERSION MODULE ==========
    conversion_parser = subparsers.add_parser(
        'conversion',
        help='Manage conversion actions',
        epilog='Examples:\n'
               '  # List all conversions\n'
               '  xw ads conversion list --customer-id 2425288235\n\n'
               '  # Create new conversion\n'
               '  xw ads conversion create --customer-id 2425288235 --name "Form Submit" --value 50\n\n'
               '  # Update conversion (make secondary)\n'
               '  xw ads conversion update --customer-id 2425288235 --conversion-id 12345 --secondary\n\n'
               '  # Get conversion labels for GTM\n'
               '  xw ads conversion labels --customer-id 2425288235 --format json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    conversion_subs = conversion_parser.add_subparsers(dest='command', help='Command')

    # conversion list
    conv_list_parser = conversion_subs.add_parser(
        'list',
        help='List all conversion actions',
        epilog='Example:\n'
               '  xw ads conversion list --customer-id 2425288235 --format table',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    conv_list_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    conv_list_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format: table | json - default: table'
    )

    # conversion create
    conv_create_parser = conversion_subs.add_parser(
        'create',
        help='Create new conversion action',
        epilog='Examples:\n'
               '  # Primary conversion with default value\n'
               '  xw ads conversion create --customer-id 2425288235 --name "Purchase" --value 100\n\n'
               '  # Secondary conversion (not counted in goals)\n'
               '  xw ads conversion create --customer-id 2425288235 --name "Newsletter" --secondary',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    conv_create_parser.add_argument('--customer-id', required=True, help='Customer ID')
    conv_create_parser.add_argument('--name', required=True, help='Conversion action name')
    conv_create_parser.add_argument(
        '--category',
        default='SUBMIT_LEAD_FORM',
        help='Category: PURCHASE, SUBMIT_LEAD_FORM, SIGNUP, CONTACT, etc. (default: SUBMIT_LEAD_FORM)'
    )
    conv_create_parser.add_argument(
        '--value',
        type=float,
        default=0,
        help='Default conversion value (default: 0)'
    )
    conv_create_parser.add_argument(
        '--secondary',
        action='store_true',
        help='Create as secondary conversion (not included in conversion goals)'
    )

    # conversion update
    conv_update_parser = conversion_subs.add_parser(
        'update',
        help='Update existing conversion action',
        epilog='Examples:\n'
               '  # Update value\n'
               '  xw ads conversion update --customer-id 2425288235 --conversion-id 12345 --value 75\n\n'
               '  # Change to secondary conversion\n'
               '  xw ads conversion update --customer-id 2425288235 --conversion-id 12345 --secondary\n\n'
               '  # Pause conversion\n'
               '  xw ads conversion update --customer-id 2425288235 --conversion-id 12345 --status PAUSED',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    conv_update_parser.add_argument('--customer-id', required=True, help='Customer ID')
    conv_update_parser.add_argument('--conversion-id', required=True, help='Conversion action ID')
    conv_update_parser.add_argument('--name', help='New name for conversion')
    conv_update_parser.add_argument('--value', type=float, help='New default value')
    conv_update_parser.add_argument('--status', choices=['ENABLED', 'PAUSED', 'REMOVED'], help='New status')
    conv_update_parser.add_argument('--primary', action='store_true', help='Make primary (included in goals)')
    conv_update_parser.add_argument('--secondary', action='store_true', help='Make secondary (not in goals)')

    # conversion remove
    conv_remove_parser = conversion_subs.add_parser(
        'remove',
        help='Remove (disable) conversion action',
        epilog='Example:\n'
               '  xw ads conversion remove --customer-id 2425288235 --conversion-id 12345',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    conv_remove_parser.add_argument('--customer-id', required=True, help='Customer ID')
    conv_remove_parser.add_argument('--conversion-id', required=True, help='Conversion action ID to remove')

    # conversion labels
    conv_labels_parser = conversion_subs.add_parser(
        'labels',
        help='Get conversion labels for GTM integration',
        epilog='Examples:\n'
               '  # Table format\n'
               '  xw ads conversion labels --customer-id 2425288235\n\n'
               '  # JSON for automation\n'
               '  xw ads conversion labels --customer-id 2425288235 --format json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    conv_labels_parser.add_argument('--customer-id', required=True, help='Customer ID')
    conv_labels_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format: table | json - default: table'
    )

    # ========== AUTH MODULE ==========
    auth_parser = subparsers.add_parser('auth', help='Authentication operations')
    auth_subs = auth_parser.add_subparsers(dest='command', help='Command')

    # auth test
    test_parser = auth_subs.add_parser('test', help='Test authentication')
    test_parser.add_argument(
        '--config',
        help='Path to google-ads.yaml config file'
    )

    # Parse args (supports both CLI and programmatic usage)
    args = parser.parse_args(args=args)

    if not args.module:
        parser.print_help()
        sys.exit(1)

    try:
        # Route to handlers
        if args.module == 'pmax':
            if not args.command:
                pmax_parser.print_help()
                sys.exit(1)

            if args.command == 'list':
                handle_pmax_list(args)
            elif args.command == 'get':
                handle_pmax_get(args)
            elif args.command == 'signals':
                handle_pmax_signals(args)

        elif args.module == 'report':
            handle_report(args)

        elif args.module == 'query':
            if not args.query and not args.file:
                print("Error: Either query string or --file is required")
                query_parser.print_help()
                sys.exit(1)
            handle_query(args)

        elif args.module == 'recs':
            handle_recommendations(args)

        elif args.module == 'conversion':
            if not args.command:
                conversion_parser.print_help()
                sys.exit(1)

            if args.command == 'list':
                handle_conversion_list(args)
            elif args.command == 'create':
                handle_conversion_create(args)
            elif args.command == 'update':
                handle_conversion_update(args)
            elif args.command == 'remove':
                handle_conversion_remove(args)
            elif args.command == 'labels':
                handle_conversion_labels(args)

        elif args.module == 'auth':
            if not args.command:
                auth_parser.print_help()
                sys.exit(1)

            if args.command == 'test':
                success = test_auth(args.config if hasattr(args, 'config') else None)
                sys.exit(0 if success else 1)

    except AdsError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
