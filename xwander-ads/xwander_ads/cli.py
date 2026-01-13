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
