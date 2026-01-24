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
from . import search
from . import reporting
from . import recommendations
from .conversions.actions import ConversionActionManager
from .search import ad_groups, rsa


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


# ========== SEARCH HANDLERS ==========

def handle_search_list(args):
    """Handle 'xw ads search list' command."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    campaigns = search.list_search_campaigns(
        client, customer_id,
        enabled_only=args.enabled_only,
        limit=args.limit
    )

    if args.format == 'json':
        print(json.dumps(campaigns, indent=2))
    else:
        print(f"\n=== Search Campaigns ({len(campaigns)}) ===\n")
        for c in campaigns:
            budget = format_micros(c['budget_micros'])
            cost = format_micros(c['cost_micros'])
            target_cpa = format_micros(c['target_cpa_micros']) if c['target_cpa_micros'] else "Auto"
            print(f"  {c['id']}: {c['name']}")
            print(f"    Status: {c['status']} | Budget: {budget} | Target CPA: {target_cpa}")
            print(f"    Geo Type: {c['geo_target_type']}")
            print(f"    Cost: {cost} | Impressions: {c['impressions']:,} | Clicks: {c['clicks']:,}")
            print(f"    Conversions: {c['conversions']:.1f} | Value: {format_micros(int(c['conversions_value']))}")
            print()


def handle_search_get(args):
    """Handle 'xw ads search get' command."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    campaign = search.get_search_campaign(client, customer_id, args.campaign_id)

    if args.format == 'json':
        print(json.dumps(campaign, indent=2))
    else:
        print(f"\n=== Search Campaign {campaign['id']}: {campaign['name']} ===\n")
        print(f"  Status: {campaign['status']}")
        print(f"  Budget: {format_micros(campaign['budget_micros'])}")
        print(f"  Target CPA: {format_micros(campaign['target_cpa_micros']) if campaign['target_cpa_micros'] else 'Auto'}")
        print(f"  Geo Target Type: {campaign['geo_target_type']}")
        print(f"\n  Network Settings:")
        print(f"    Google Search: {campaign['target_google_search']}")
        print(f"    Search Network: {campaign['target_search_network']}")
        print(f"    Content Network: {campaign['target_content_network']}")
        print(f"\n  Performance:")
        print(f"    Cost: {format_micros(campaign['cost_micros'])}")
        print(f"    Impressions: {campaign['impressions']:,}")
        print(f"    Clicks: {campaign['clicks']:,}")
        print(f"    Conversions: {campaign['conversions']:.1f}")
        print(f"    Value: {format_micros(int(campaign['conversions_value']))}")
        print()


def handle_search_create(args):
    """Handle 'xw ads search create' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    # Parse geo targets
    geo_targets = args.geo_targets.split(',') if args.geo_targets else None

    # Parse languages
    languages = args.languages.split(',') if args.languages else None

    if args.dry_run:
        print("\n=== DRY RUN - No changes will be made ===\n")
        print(f"  Would create campaign: {args.name}")
        print(f"  Customer ID: {customer_id}")
        print(f"  Budget: EUR {args.budget:.2f}/day")
        print(f"  Target CPA: {f'EUR {args.target_cpa:.2f}' if args.target_cpa else 'Auto'}")
        print(f"  Geo Type: {args.geo_type}")
        print(f"  Geo Targets: {geo_targets or ['FINLAND']}")
        print(f"  Languages: {languages or search.TOURIST_LANGUAGES}")
        print(f"  Status: {args.status}")
        print()
        return

    result = search.create_search_campaign(
        client,
        customer_id,
        name=args.name,
        daily_budget_eur=args.budget,
        target_cpa_eur=args.target_cpa,
        geo_target_type=args.geo_type,
        geo_targets=geo_targets,
        languages=languages,
        status=args.status
    )

    print(f"\n=== Campaign Created ===\n")
    print(f"  Campaign ID: {result['campaign_id']}")
    print(f"  Name: {result['name']}")
    print(f"  Status: {result['status']}")
    print(f"  Budget: EUR {result['daily_budget_eur']:.2f}/day")
    target_cpa_str = f"EUR {result['target_cpa_eur']:.2f}" if result['target_cpa_eur'] else 'Auto'
    print(f"  Target CPA: {target_cpa_str}")
    print(f"  Geo Type: {result['geo_target_type']}")
    print(f"\n  URL: {result['url']}")
    print()


def handle_search_adjust_devices(args):
    """Handle 'xw ads search adjust-devices' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    # Convert percentage notation to multiplier
    def parse_modifier(value: str) -> float:
        """Parse modifier from +50 / -30 notation to 1.5 / 0.7"""
        if value.startswith('+'):
            return 1.0 + (float(value[1:]) / 100)
        elif value.startswith('-'):
            return 1.0 - (float(value[1:]) / 100)
        else:
            return float(value)

    mobile_mod = parse_modifier(args.mobile) if args.mobile else 1.0
    desktop_mod = parse_modifier(args.desktop) if args.desktop else 1.0
    tablet_mod = parse_modifier(args.tablet) if args.tablet else 1.0

    if args.dry_run:
        print("\n=== DRY RUN - No changes will be made ===\n")
        print(f"  Campaign: {args.campaign_id}")
        print(f"  Mobile: {mobile_mod:.2f} ({'+' if mobile_mod >= 1 else ''}{(mobile_mod - 1) * 100:.0f}%)")
        print(f"  Desktop: {desktop_mod:.2f} ({'+' if desktop_mod >= 1 else ''}{(desktop_mod - 1) * 100:.0f}%)")
        print(f"  Tablet: {tablet_mod:.2f} ({'+' if tablet_mod >= 1 else ''}{(tablet_mod - 1) * 100:.0f}%)")
        print()
        return

    result = search.set_device_bid_adjustments(
        client,
        customer_id,
        args.campaign_id,
        mobile_modifier=mobile_mod,
        desktop_modifier=desktop_mod,
        tablet_modifier=tablet_mod
    )

    print(f"\n=== Device Bid Adjustments Set ===\n")
    print(f"  Campaign: {result['campaign_id']}")
    for device, modifier in result['device_adjustments'].items():
        pct = (modifier - 1) * 100
        sign = '+' if pct >= 0 else ''
        print(f"  {device}: {modifier:.2f} ({sign}{pct:.0f}%)")
    print()


def handle_search_update_attribution(args):
    """Handle 'xw ads search update-attribution' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    if args.dry_run:
        print("\n=== DRY RUN - No changes will be made ===\n")
        print(f"  Conversion Action: {args.conversion_id}")
        print(f"  Click Window: {args.click_days} days")
        print(f"  View Window: {args.view_days} days")
        print()
        return

    result = search.update_conversion_attribution(
        client,
        customer_id,
        args.conversion_id,
        click_lookback_days=args.click_days,
        view_lookback_days=args.view_days
    )

    print(f"\n=== Attribution Window Updated ===\n")
    print(f"  Conversion Action: {result['conversion_action_id']}")
    print(f"  Click Window: {result['click_lookback_days']} days")
    print(f"  View Window: {result['view_lookback_days']} days")
    print()


def handle_search_device_performance(args):
    """Handle 'xw ads search device-performance' command."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    perf = search.get_device_performance(
        client,
        customer_id,
        args.campaign_id,
        date_range=f"LAST_{args.days}_DAYS"
    )

    if args.format == 'json':
        print(json.dumps(perf, indent=2))
    else:
        print(f"\n=== Device Performance ({args.days} days) ===\n")
        print(f"  Campaign: {args.campaign_id}\n")

        for p in perf:
            cost = format_micros(p['cost_micros'])
            print(f"  {p['device']}:")
            print(f"    Impressions: {p['impressions']:,} ({p['impression_share']:.1f}%)")
            print(f"    Clicks: {p['clicks']:,}")
            print(f"    Cost: {cost}")
            print(f"    Conversions: {p['conversions']:.1f}")
            print()


# ========== AD GROUP HANDLERS ==========

def handle_adgroup_list(args):
    """Handle 'xw ads search adgroup list' command."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    adgroups = ad_groups.list_ad_groups(
        client,
        customer_id,
        campaign_id=args.campaign_id if hasattr(args, 'campaign_id') else None,
        enabled_only=args.enabled_only,
        limit=args.limit if hasattr(args, 'limit') else 100
    )

    if args.format == 'json':
        print(json.dumps(adgroups, indent=2))
    else:
        print(f"\n=== Ad Groups ({len(adgroups)}) ===\n")
        for ag in adgroups:
            cpc = format_micros(ag['cpc_bid_micros']) if ag['cpc_bid_micros'] else 'Auto'
            cost = format_micros(ag['cost_micros'])
            print(f"  {ag['id']}: {ag['name']}")
            print(f"    Campaign: {ag['campaign_name']} ({ag['campaign_id']})")
            print(f"    Status: {ag['status']} | Type: {ag['type']}")
            print(f"    Default CPC: {cpc}")
            print(f"    Cost: {cost} | Impressions: {ag['impressions']:,} | Clicks: {ag['clicks']:,}")
            print(f"    Conversions: {ag['conversions']:.1f}")
            print()


def handle_adgroup_create(args):
    """Handle 'xw ads search adgroup create' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    result = ad_groups.create_ad_group(
        client,
        customer_id,
        campaign_id=args.campaign_id,
        name=args.name,
        cpc_bid_eur=args.cpc_bid if hasattr(args, 'cpc_bid') else None,
        status=args.status if hasattr(args, 'status') else 'PAUSED'
    )

    print(f"\n=== Ad Group Created ===\n")
    print(f"  Ad Group ID: {result['ad_group_id']}")
    print(f"  Name: {result['name']}")
    print(f"  Campaign: {result['campaign_id']}")
    print(f"  Status: {result['status']}")
    if result['cpc_bid_eur']:
        print(f"  Default CPC: {format_micros(int(result['cpc_bid_eur'] * 1_000_000))}")
    print(f"\n  URL: {result['url']}")
    print()


def handle_adgroup_get(args):
    """Handle 'xw ads search adgroup get' command."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    adgroup = ad_groups.get_ad_group(client, customer_id, args.adgroup_id)

    if args.format == 'json':
        print(json.dumps(adgroup, indent=2))
    else:
        print(f"\n=== Ad Group {adgroup['id']}: {adgroup['name']} ===\n")
        print(f"  Campaign: {adgroup['campaign_name']} ({adgroup['campaign_id']})")
        print(f"  Status: {adgroup['status']}")
        print(f"  Type: {adgroup['type']}")
        if adgroup['cpc_bid_micros']:
            print(f"  Default CPC: {format_micros(adgroup['cpc_bid_micros'])}")
        print(f"\n  Performance:")
        print(f"    Cost: {format_micros(adgroup['cost_micros'])}")
        print(f"    Impressions: {adgroup['impressions']:,}")
        print(f"    Clicks: {adgroup['clicks']:,}")
        print(f"    Conversions: {adgroup['conversions']:.1f}")
        print(f"    Value: {format_micros(int(adgroup['conversions_value']))}")
        print()


# ========== RSA HANDLERS ==========

def handle_rsa_list(args):
    """Handle 'xw ads search rsa list' command."""
    import json
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    rsas = rsa.list_rsas(
        client,
        customer_id,
        ad_group_id=args.adgroup_id,
        limit=args.limit if hasattr(args, 'limit') else 100
    )

    if args.format == 'json':
        print(json.dumps(rsas, indent=2))
    else:
        print(f"\n=== Responsive Search Ads ({len(rsas)}) ===\n")
        for ad in rsas:
            print(f"  {ad['ad_id']}: {ad['ad_group_name']}")
            print(f"    Campaign: {ad['campaign_name']}")
            print(f"    Status: {ad['status']} | Strength: {ad['ad_strength']}")
            print(f"    Headlines: {len(ad['headlines'])} | Descriptions: {len(ad['descriptions'])}")
            print(f"    Impressions: {ad['impressions']:,} | Clicks: {ad['clicks']:,}")
            print(f"    Conversions: {ad['conversions']:.1f}")
            print()


def handle_rsa_create(args):
    """Handle 'xw ads search rsa create' command."""
    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    # Parse headlines from comma-separated string
    headlines_list = [{"text": h.strip()} for h in args.headlines.split(',')]

    # Parse descriptions from comma-separated string
    descriptions_list = [{"text": d.strip()} for d in args.descriptions.split(',')]

    result = rsa.create_rsa(
        client,
        customer_id,
        ad_group_id=args.adgroup_id,
        headlines=headlines_list,
        descriptions=descriptions_list,
        final_urls=[args.final_url],
        path1=args.path1 if hasattr(args, 'path1') else None,
        path2=args.path2 if hasattr(args, 'path2') else None,
        status=args.status if hasattr(args, 'status') else 'PAUSED'
    )

    print(f"\n=== RSA Created ===\n")
    print(f"  Ad ID: {result['ad_id']}")
    print(f"  Ad Group: {result['ad_group_id']}")
    print(f"  Status: {result['status']}")
    print(f"  Headlines: {result['headline_count']}")
    print(f"  Descriptions: {result['description_count']}")
    print(f"\n  URL: {result['url']}")
    print()


def handle_rsa_bulk(args):
    """Handle 'xw ads search rsa bulk' command."""
    import json
    from pathlib import Path

    client = get_client(version=args.api_version)
    customer_id = normalize_customer_id(args.customer_id)

    # Load RSA configs from file
    config_file = Path(args.file)
    if not config_file.exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    with open(config_file, 'r') as f:
        rsas_list = json.load(f)

    if args.dry_run:
        print(f"\n=== DRY RUN - Would create {len(rsas_list)} RSAs ===\n")
        for i, rsa_config in enumerate(rsas_list, 1):
            print(f"  {i}. Ad Group: {rsa_config.get('ad_group_id')}")
            print(f"     Headlines: {len(rsa_config.get('headlines', []))}")
            print(f"     Descriptions: {len(rsa_config.get('descriptions', []))}")
        print()
        return

    results = rsa.bulk_create_rsas(client, customer_id, rsas_list)

    # Summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = len(results) - success_count

    print(f"\n=== Bulk RSA Creation Complete ===\n")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(results)}\n")

    # Show results
    for r in results:
        if r['status'] == 'success':
            print(f"  ✓ Index {r['index']}: Created ad {r['ad_id']}")
        else:
            print(f"  ✗ Index {r['index']}: {r['error']}")

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

    # ========== SEARCH MODULE ==========
    search_parser = subparsers.add_parser(
        'search',
        help='Search campaign operations',
        epilog='Examples:\n'
               '  # List Search campaigns\n'
               '  xw ads search list --customer-id 2425288235\n\n'
               '  # Create Day Tours campaign\n'
               '  xw ads search create --customer-id 2425288235 --name "Search | Day Tours" --budget 50 --target-cpa 40\n\n'
               '  # Set device bid adjustments\n'
               '  xw ads search adjust-devices --customer-id 2425288235 --campaign-id 12345 --mobile +50 --desktop -30',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    search_subs = search_parser.add_subparsers(dest='command', help='Command')

    # search list
    search_list_parser = search_subs.add_parser(
        'list',
        help='List Search campaigns',
        epilog='Examples:\n'
               '  xw ads search list --customer-id 2425288235\n'
               '  xw ads search list --customer-id 2425288235 --enabled-only --format json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    search_list_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    search_list_parser.add_argument('--enabled-only', action='store_true', help='Only show enabled campaigns')
    search_list_parser.add_argument('--limit', type=int, default=50, help='Max campaigns to return (default: 50)')
    search_list_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format: table | json - default: table'
    )

    # search get
    search_get_parser = search_subs.add_parser(
        'get',
        help='Get Search campaign details',
        epilog='Example:\n'
               '  xw ads search get --customer-id 2425288235 --campaign-id 12345678901',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    search_get_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    search_get_parser.add_argument('--campaign-id', required=True, help='Campaign ID')
    search_get_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format: table | json - default: table'
    )

    # search create
    search_create_parser = search_subs.add_parser(
        'create',
        help='Create Search campaign with LOCATION_OF_PRESENCE targeting',
        epilog='Examples:\n'
               '  # Create Day Tours campaign (tourists IN Finland)\n'
               '  xw ads search create --customer-id 2425288235 \\\n'
               '    --name "Search | Day Tours | Ivalo" \\\n'
               '    --budget 50 \\\n'
               '    --target-cpa 40 \\\n'
               '    --geo-type LOCATION_OF_PRESENCE \\\n'
               '    --geo-targets FINLAND \\\n'
               '    --languages ENGLISH,FRENCH,GERMAN \\\n'
               '    --dry-run\n\n'
               '  # Geo targets: FINLAND, FRANCE, SPAIN, GERMANY, ITALY, UNITED_KINGDOM, NETHERLANDS\n'
               '  # Languages: ENGLISH, FRENCH, SPANISH, GERMAN, ITALIAN, DUTCH, FINNISH',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    search_create_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    search_create_parser.add_argument('--name', required=True, help='Campaign name (e.g., "Search | Day Tours | Ivalo")')
    search_create_parser.add_argument('--budget', type=float, required=True, help='Daily budget in EUR (e.g., 50)')
    search_create_parser.add_argument('--target-cpa', type=float, help='Target CPA in EUR (optional, e.g., 40)')
    search_create_parser.add_argument(
        '--geo-type',
        choices=['LOCATION_OF_PRESENCE', 'AREA_OF_INTEREST', 'PRESENCE_OR_INTEREST'],
        default='LOCATION_OF_PRESENCE',
        help='Geo targeting type (default: LOCATION_OF_PRESENCE for tourists IN location)'
    )
    search_create_parser.add_argument(
        '--geo-targets',
        help='Comma-separated geo targets (e.g., FINLAND,GERMANY or geoTargetConstants/2246)'
    )
    search_create_parser.add_argument(
        '--languages',
        help='Comma-separated languages (e.g., ENGLISH,FRENCH,GERMAN or 1000,1002,1001)'
    )
    search_create_parser.add_argument(
        '--status',
        choices=['PAUSED', 'ENABLED'],
        default='PAUSED',
        help='Initial campaign status (default: PAUSED for safety)'
    )
    search_create_parser.add_argument('--dry-run', action='store_true', help='Show what would be created without making changes')

    # search adjust-devices
    search_adjust_parser = search_subs.add_parser(
        'adjust-devices',
        help='Set device bid adjustments for Search campaign',
        epilog='Examples:\n'
               '  # Day Tours: +50%% mobile, -30%% desktop\n'
               '  xw ads search adjust-devices --customer-id 2425288235 \\\n'
               '    --campaign-id 12345 \\\n'
               '    --mobile +50 \\\n'
               '    --desktop -30\n\n'
               '  # Using decimal notation\n'
               '  xw ads search adjust-devices --customer-id 2425288235 \\\n'
               '    --campaign-id 12345 \\\n'
               '    --mobile 1.5 \\\n'
               '    --desktop 0.7',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    search_adjust_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    search_adjust_parser.add_argument('--campaign-id', required=True, help='Campaign ID')
    search_adjust_parser.add_argument('--mobile', help='Mobile bid modifier (+50 or 1.5)')
    search_adjust_parser.add_argument('--desktop', help='Desktop bid modifier (-30 or 0.7)')
    search_adjust_parser.add_argument('--tablet', help='Tablet bid modifier (default: baseline)')
    search_adjust_parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')

    # search update-attribution
    search_attr_parser = search_subs.add_parser(
        'update-attribution',
        help='Update conversion action attribution window',
        epilog='Examples:\n'
               '  # Day Tours: 7-day window\n'
               '  xw ads search update-attribution --customer-id 2425288235 \\\n'
               '    --conversion-id 7452944340 \\\n'
               '    --click-days 7\n\n'
               '  # Multiday: 90-day window\n'
               '  xw ads search update-attribution --customer-id 2425288235 \\\n'
               '    --conversion-id 7452944343 \\\n'
               '    --click-days 90 \\\n'
               '    --view-days 30',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    search_attr_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    search_attr_parser.add_argument('--conversion-id', required=True, help='Conversion action ID')
    search_attr_parser.add_argument('--click-days', type=int, required=True, help='Click-through lookback window (1-90 days)')
    search_attr_parser.add_argument('--view-days', type=int, default=1, help='View-through lookback window (1-30 days, default: 1)')
    search_attr_parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')

    # search device-performance
    search_perf_parser = search_subs.add_parser(
        'device-performance',
        help='Get performance metrics by device type',
        epilog='Example:\n'
               '  xw ads search device-performance --customer-id 2425288235 --campaign-id 12345 --days 30',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    search_perf_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    search_perf_parser.add_argument('--campaign-id', required=True, help='Campaign ID')
    search_perf_parser.add_argument('--days', type=int, default=30, choices=[7, 14, 30], help='Date range in days (7, 14, or 30, default: 30)')
    search_perf_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format: table | json - default: table'
    )

    # ========== AD GROUP SUBCOMMANDS ==========
    adgroup_parser = search_subs.add_parser(
        'adgroup',
        help='Ad group operations',
        epilog='Examples:\n'
               '  # List ad groups\n'
               '  xw ads search adgroup list --customer-id 2425288235 --campaign-id 12345\n\n'
               '  # Create ad group\n'
               '  xw ads search adgroup create --customer-id 2425288235 --campaign-id 12345 --name "Northern Lights" --cpc-bid 1.50\n\n'
               '  # Get ad group details\n'
               '  xw ads search adgroup get --customer-id 2425288235 --adgroup-id 67890',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    adgroup_subs = adgroup_parser.add_subparsers(dest='adgroup_command', help='Ad group command')

    # adgroup list
    adgroup_list_parser = adgroup_subs.add_parser(
        'list',
        help='List ad groups',
        epilog='Examples:\n'
               '  xw ads search adgroup list --customer-id 2425288235\n'
               '  xw ads search adgroup list --customer-id 2425288235 --campaign-id 12345 --enabled-only',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    adgroup_list_parser.add_argument('--customer-id', required=True, help='Customer ID (e.g., 2425288235)')
    adgroup_list_parser.add_argument('--campaign-id', help='Filter by campaign ID')
    adgroup_list_parser.add_argument('--enabled-only', action='store_true', help='Only show enabled ad groups')
    adgroup_list_parser.add_argument('--limit', type=int, default=100, help='Max ad groups to return (default: 100)')
    adgroup_list_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format: table | json - default: table'
    )

    # adgroup create
    adgroup_create_parser = adgroup_subs.add_parser(
        'create',
        help='Create ad group',
        epilog='Examples:\n'
               '  # Create with default CPC bid\n'
               '  xw ads search adgroup create --customer-id 2425288235 \\\n'
               '    --campaign-id 12345 \\\n'
               '    --name "Northern Lights Tours" \\\n'
               '    --cpc-bid 1.50\n\n'
               '  # Create paused (recommended)\n'
               '  xw ads search adgroup create --customer-id 2425288235 \\\n'
               '    --campaign-id 12345 \\\n'
               '    --name "Husky Safari" \\\n'
               '    --cpc-bid 1.20 \\\n'
               '    --status PAUSED',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    adgroup_create_parser.add_argument('--customer-id', required=True, help='Customer ID')
    adgroup_create_parser.add_argument('--campaign-id', required=True, help='Campaign ID')
    adgroup_create_parser.add_argument('--name', required=True, help='Ad group name (e.g., "Northern Lights Tours")')
    adgroup_create_parser.add_argument('--cpc-bid', type=float, help='Default CPC bid in EUR (e.g., 1.50)')
    adgroup_create_parser.add_argument(
        '--status',
        choices=['PAUSED', 'ENABLED'],
        default='PAUSED',
        help='Initial status (default: PAUSED)'
    )

    # adgroup get
    adgroup_get_parser = adgroup_subs.add_parser(
        'get',
        help='Get ad group details',
        epilog='Example:\n'
               '  xw ads search adgroup get --customer-id 2425288235 --adgroup-id 67890',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    adgroup_get_parser.add_argument('--customer-id', required=True, help='Customer ID')
    adgroup_get_parser.add_argument('--adgroup-id', required=True, help='Ad group ID')
    adgroup_get_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format: table | json - default: table'
    )

    # ========== RSA SUBCOMMANDS ==========
    rsa_parser = search_subs.add_parser(
        'rsa',
        help='Responsive Search Ad operations',
        epilog='Examples:\n'
               '  # List RSAs in ad group\n'
               '  xw ads search rsa list --customer-id 2425288235 --adgroup-id 67890\n\n'
               '  # Create single RSA\n'
               '  xw ads search rsa create --customer-id 2425288235 --adgroup-id 67890 \\\n'
               '    --headlines "H1,H2,H3" \\\n'
               '    --descriptions "D1,D2" \\\n'
               '    --final-url https://xwander.com/tours\n\n'
               '  # Bulk create from JSON file\n'
               '  xw ads search rsa bulk --customer-id 2425288235 --file rsas.json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    rsa_subs = rsa_parser.add_subparsers(dest='rsa_command', help='RSA command')

    # rsa list
    rsa_list_parser = rsa_subs.add_parser(
        'list',
        help='List Responsive Search Ads',
        epilog='Examples:\n'
               '  xw ads search rsa list --customer-id 2425288235 --adgroup-id 67890\n'
               '  xw ads search rsa list --customer-id 2425288235 --adgroup-id 67890 --format json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    rsa_list_parser.add_argument('--customer-id', required=True, help='Customer ID')
    rsa_list_parser.add_argument('--adgroup-id', required=True, help='Ad group ID')
    rsa_list_parser.add_argument('--limit', type=int, default=100, help='Max RSAs to return (default: 100)')
    rsa_list_parser.add_argument(
        '--format',
        choices=['table', 'json'],
        default='table',
        help='Output format: table | json - default: table'
    )

    # rsa create
    rsa_create_parser = rsa_subs.add_parser(
        'create',
        help='Create Responsive Search Ad',
        epilog='Examples:\n'
               '  # Create RSA with 5 headlines, 2 descriptions\n'
               '  xw ads search rsa create --customer-id 2425288235 --adgroup-id 67890 \\\n'
               '    --headlines "Northern Lights Tours,Book Now - Best Prices,Expert Arctic Guides,Small Group Adventures,Guaranteed Aurora Viewing" \\\n'
               '    --descriptions "Experience the magical Northern Lights in Finnish Lapland. Professional guides.,Join our award-winning tours from Ivalo. Book online with instant confirmation." \\\n'
               '    --final-url https://xwander.com/northern-lights \\\n'
               '    --path1 tours \\\n'
               '    --path2 aurora',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    rsa_create_parser.add_argument('--customer-id', required=True, help='Customer ID')
    rsa_create_parser.add_argument('--adgroup-id', required=True, help='Ad group ID')
    rsa_create_parser.add_argument('--headlines', required=True, help='Comma-separated headlines (3-15, max 30 chars each)')
    rsa_create_parser.add_argument('--descriptions', required=True, help='Comma-separated descriptions (2-4, max 90 chars each)')
    rsa_create_parser.add_argument('--final-url', required=True, help='Landing page URL')
    rsa_create_parser.add_argument('--path1', help='Display URL path 1 (max 15 chars)')
    rsa_create_parser.add_argument('--path2', help='Display URL path 2 (max 15 chars)')
    rsa_create_parser.add_argument(
        '--status',
        choices=['PAUSED', 'ENABLED'],
        default='PAUSED',
        help='Initial status (default: PAUSED)'
    )

    # rsa bulk
    rsa_bulk_parser = rsa_subs.add_parser(
        'bulk',
        help='Bulk create RSAs from JSON file',
        epilog='Examples:\n'
               '  # Create multiple RSAs from file\n'
               '  xw ads search rsa bulk --customer-id 2425288235 --file rsas.json\n\n'
               '  # Dry run to validate\n'
               '  xw ads search rsa bulk --customer-id 2425288235 --file rsas.json --dry-run\n\n'
               'JSON format:\n'
               '[\n'
               '  {\n'
               '    "ad_group_id": "67890",\n'
               '    "headlines": [{"text": "H1"}, {"text": "H2"}, {"text": "H3"}],\n'
               '    "descriptions": [{"text": "D1"}, {"text": "D2"}],\n'
               '    "final_urls": ["https://xwander.com/tours"],\n'
               '    "path1": "tours",\n'
               '    "path2": "arctic"\n'
               '  }\n'
               ']',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    rsa_bulk_parser.add_argument('--customer-id', required=True, help='Customer ID')
    rsa_bulk_parser.add_argument('--file', required=True, help='Path to JSON file with RSA configs')
    rsa_bulk_parser.add_argument('--dry-run', action='store_true', help='Validate without creating')

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

        elif args.module == 'search':
            if not args.command:
                search_parser.print_help()
                sys.exit(1)

            if args.command == 'list':
                handle_search_list(args)
            elif args.command == 'get':
                handle_search_get(args)
            elif args.command == 'create':
                handle_search_create(args)
            elif args.command == 'adjust-devices':
                handle_search_adjust_devices(args)
            elif args.command == 'update-attribution':
                handle_search_update_attribution(args)
            elif args.command == 'device-performance':
                handle_search_device_performance(args)
            elif args.command == 'adgroup':
                if not hasattr(args, 'adgroup_command') or not args.adgroup_command:
                    print("Error: adgroup subcommand required (list, create, get)")
                    sys.exit(1)
                if args.adgroup_command == 'list':
                    handle_adgroup_list(args)
                elif args.adgroup_command == 'create':
                    handle_adgroup_create(args)
                elif args.adgroup_command == 'get':
                    handle_adgroup_get(args)
            elif args.command == 'rsa':
                if not hasattr(args, 'rsa_command') or not args.rsa_command:
                    print("Error: rsa subcommand required (list, create, bulk)")
                    sys.exit(1)
                if args.rsa_command == 'list':
                    handle_rsa_list(args)
                elif args.rsa_command == 'create':
                    handle_rsa_create(args)
                elif args.rsa_command == 'bulk':
                    handle_rsa_bulk(args)

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
