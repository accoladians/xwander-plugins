"""GA4 CLI - Command line interface for GA4 operations"""

import json
import sys
from typing import List, Optional
from datetime import datetime

import click

from .client import GA4DataClient, GA4AdminClient
from .reports import ReportBuilder, ReportFormatter
from .dimensions import DimensionManager
from .audiences import AudienceManager
from .exceptions import GA4Error


# Default property ID for Xwander
DEFAULT_PROPERTY_ID = "358203796"


@click.group()
def cli():
    """Xwander GA4 - Google Analytics 4 operations"""
    pass


@cli.command(epilog="""
Examples:

  # Last 7 days by source and sessions
  xwander-ga4 report --dimensions source --metrics sessions

  # Last 30 days by page path, top 50 pages
  xwander-ga4 report --dimensions pagePath --metrics sessions --days 30 --limit 50

  # Specific date range with multiple dimensions/metrics
  xwander-ga4 report --start-date 2026-01-01 --end-date 2026-01-07 \\
    --dimensions date source --metrics sessions users --format json
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID (default: Xwander)",
)
@click.option("--dimensions", multiple=True, required=True, help="Dimension names")
@click.option("--metrics", multiple=True, required=True, help="Metric names")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.option("--days", type=int, default=7, help="Number of days if no date range")
@click.option("--limit", type=int, default=100, help="Max rows to return")
@click.option("--format", type=click.Choice(["table", "json", "summary"]), default="table")
def report(
    property_id: str,
    dimensions: tuple,
    metrics: tuple,
    start_date: Optional[str],
    end_date: Optional[str],
    days: int,
    limit: int,
    format: str,
):
    """Run a GA4 report with custom dimensions and metrics"""
    try:
        data_client = GA4DataClient(property_id)
        builder = ReportBuilder(data_client)

        if start_date and end_date:
            result = builder.date_range(
                start_date=start_date,
                end_date=end_date,
                dimensions=list(dimensions),
                metrics=list(metrics),
                limit=limit,
            )
        else:
            result = builder.last_n_days(
                days=days,
                dimensions=list(dimensions),
                metrics=list(metrics),
                limit=limit,
            )

        formatter = ReportFormatter()
        if format == "table":
            click.echo(formatter.table(result))
        elif format == "json":
            click.echo(formatter.json(result))
        else:
            click.echo(formatter.summary(result))

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(epilog="""
Examples:

  # Quick summary (active users by country)
  xwander-ga4 realtime

  # Custom dimensions
  xwander-ga4 realtime --dimensions country city source --metrics activeUsers
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.option("--dimensions", multiple=True, help="Dimension names")
@click.option("--metrics", multiple=True, help="Metric names")
def realtime(property_id: str, dimensions: tuple, metrics: tuple):
    """Run realtime GA4 report showing active users now"""
    try:
        data_client = GA4DataClient(property_id)
        builder = ReportBuilder(data_client)

        if dimensions and metrics:
            result = data_client.run_realtime_report(
                dimensions=list(dimensions),
                metrics=list(metrics),
                limit=20,
            )
        else:
            result = builder.realtime_summary()

        formatter = ReportFormatter()
        click.echo(formatter.table(result))

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("traffic-sources", epilog="""
Examples:

  # Last 30 days (default)
  xwander-ga4 traffic-sources

  # Last 7 days, top 20 sources
  xwander-ga4 traffic-sources --days 7 --limit 20
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.option("--days", type=int, default=30, help="Number of days")
@click.option("--limit", type=int, default=50, help="Max rows")
def traffic_sources(property_id: str, days: int, limit: int):
    """Get traffic breakdown by source and medium"""
    try:
        data_client = GA4DataClient(property_id)
        builder = ReportBuilder(data_client)
        result = builder.traffic_sources(days=days, limit=limit)

        formatter = ReportFormatter()
        click.echo(formatter.table(result))

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("top-pages", epilog="""
Examples:

  # Last 30 days (default)
  xwander-ga4 top-pages

  # Last 7 days, top 10 pages
  xwander-ga4 top-pages --days 7 --limit 10
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.option("--days", type=int, default=30, help="Number of days")
@click.option("--limit", type=int, default=50, help="Max rows")
def top_pages(property_id: str, days: int, limit: int):
    """Get top pages ranked by sessions"""
    try:
        data_client = GA4DataClient(property_id)
        builder = ReportBuilder(data_client)
        result = builder.top_pages(days=days, limit=limit)

        formatter = ReportFormatter()
        click.echo(formatter.table(result))

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("conversions", epilog="""
Examples:

  # Last 30 days (default)
  xwander-ga4 conversions

  # Last 7 days
  xwander-ga4 conversions --days 7
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.option("--days", type=int, default=30, help="Number of days")
@click.option("--limit", type=int, default=100, help="Max rows")
def conversions(property_id: str, days: int, limit: int):
    """Get conversion events with counts and values"""
    try:
        data_client = GA4DataClient(property_id)
        builder = ReportBuilder(data_client)
        result = builder.conversions(days=days, limit=limit)

        formatter = ReportFormatter()
        click.echo(formatter.table(result))

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("daily-summary", epilog="""
Examples:

  # Last 30 days (default)
  xwander-ga4 daily-summary

  # Last 7 days
  xwander-ga4 daily-summary --days 7
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.option("--days", type=int, default=30, help="Number of days")
def daily_summary(property_id: str, days: int):
    """Get daily metrics summary (sessions, users, events)"""
    try:
        data_client = GA4DataClient(property_id)
        builder = ReportBuilder(data_client)
        result = builder.daily_summary(days=days)

        formatter = ReportFormatter()
        click.echo(formatter.table(result))

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Dimension commands
@cli.group("dimension")
def dimension_group():
    """Manage custom dimensions"""
    pass


@dimension_group.command("create", epilog="""
Examples:

  # Create event-scoped dimension
  xwander-ga4 dimension create \\
    --display-name "Product Type" \\
    --parameter-name product_type \\
    --description "Day tours vs multi-day packages"

  # Create user-scoped dimension
  xwander-ga4 dimension create \\
    --display-name "Customer Segment" \\
    --parameter-name customer_segment \\
    --scope USER
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.option("--display-name", required=True, help="Display name")
@click.option("--parameter-name", required=True, help="Parameter name")
@click.option(
    "--scope",
    type=click.Choice(["EVENT", "USER", "ITEM"]),
    default="EVENT",
    help="Dimension scope",
)
@click.option("--description", default="", help="Description")
def create_dimension(
    property_id: str, display_name: str, parameter_name: str, scope: str, description: str
):
    """Create custom dimension (parameter name must be alphanumeric + underscore)"""
    try:
        admin_client = GA4AdminClient(property_id)
        manager = DimensionManager(admin_client)

        # Validate
        DimensionManager.validate_display_name(display_name)
        DimensionManager.validate_parameter_name(parameter_name)

        result = manager.create(
            display_name=display_name,
            parameter_name=parameter_name,
            scope=scope,
            description=description,
        )

        click.echo(f"Created: {result['api_name']}")
        click.echo(json.dumps(result, indent=2))

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@dimension_group.command("list", epilog="""
Examples:

  # List all dimensions
  xwander-ga4 dimension list

  # List only event-scoped dimensions
  xwander-ga4 dimension list --scope EVENT
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.option(
    "--scope",
    type=click.Choice(["EVENT", "USER", "ITEM"]),
    help="Filter by scope",
)
def list_dimensions(property_id: str, scope: Optional[str]):
    """List all custom dimensions for property"""
    try:
        admin_client = GA4AdminClient(property_id)
        manager = DimensionManager(admin_client)

        if scope:
            dimensions = manager.by_scope(scope)
        else:
            dimensions = manager.list()

        if not dimensions:
            click.echo("No custom dimensions found")
            return

        for dim in dimensions:
            click.echo(f"\n{dim['display_name']} ({dim['api_name']})")
            click.echo(f"  Parameter: {dim['parameter_name']}")
            click.echo(f"  Scope: {dim['scope']}")
            if dim.get("description"):
                click.echo(f"  Description: {dim['description']}")

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Audience commands
@cli.group("audience")
def audience_group():
    """Manage audiences"""
    pass


@audience_group.command("list", epilog="""
Examples:

  # List all audiences
  xwander-ga4 audience list

  # List audiences sorted by member count (largest first)
  xwander-ga4 audience list --sort-by-size
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.option("--sort-by-size", is_flag=True, help="Sort by member count")
def list_audiences(property_id: str, sort_by_size: bool):
    """List all audiences in property"""
    try:
        admin_client = GA4AdminClient(property_id)
        manager = AudienceManager(admin_client)

        if sort_by_size:
            audiences = manager.sorted_by_size()
        else:
            audiences = manager.list()

        if not audiences:
            click.echo("No audiences found")
            return

        for audience in audiences:
            click.echo(f"\n{audience['name']}")
            click.echo(f"  ID: {audience['audience_id']}")
            click.echo(f"  Members: {audience['member_count']:,}")
            if audience.get("description"):
                click.echo(f"  Description: {audience['description']}")

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@audience_group.command("search", epilog="""
Examples:

  # Search for audiences containing "Northern Lights"
  xwander-ga4 audience search "Northern Lights"

  # Search for paid search audiences
  xwander-ga4 audience search paid_search
""")
@click.option(
    "--property-id",
    default=DEFAULT_PROPERTY_ID,
    help="GA4 property ID",
)
@click.argument("name_pattern")
def search_audiences(property_id: str, name_pattern: str):
    """Search audiences by name pattern (case-insensitive)"""
    try:
        admin_client = GA4AdminClient(property_id)
        manager = AudienceManager(admin_client)
        audiences = manager.filter_by_name(name_pattern)

        if not audiences:
            click.echo(f"No audiences matching '{name_pattern}'")
            return

        for audience in audiences:
            click.echo(f"\n{audience['name']}")
            click.echo(f"  ID: {audience['audience_id']}")
            click.echo(f"  Members: {audience['member_count']:,}")

    except GA4Error as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
