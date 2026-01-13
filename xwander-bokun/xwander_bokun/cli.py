"""
Click-based CLI for xwander-bokun.

Usage:
    xw bokun search "Aurora"
    xw bokun booking XWA-12345
    xw bokun clone 1107193 --title "Aurora Camp Rovaniemi"
"""

import asyncio
import json
import sys
from typing import Optional

import click

from .client import BokunClient
from .experience import ExperienceManager
from .booking import BookingManager
from .clone import clone_experience, clone_for_rovaniemi, CloneConfig


def run_async(coro):
    """Run async function synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
def cli(ctx, debug):
    """Bokun API CLI - Bookings, Experiences, Products."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


# =============================================================================
# Experience Commands
# =============================================================================


@cli.command("search")
@click.argument("query", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--limit", default=20, help="Max results")
@click.pass_context
def search_experiences(ctx, query, as_json, limit):
    """Search experiences/activities."""

    async def _search():
        async with BokunClient(debug=ctx.obj["debug"]) as client:
            manager = ExperienceManager(client)
            results = await manager.search(query, page_size=limit)

            if as_json:
                data = [
                    {
                        "id": r.id,
                        "title": r.title,
                        "duration_hours": r.duration_hours,
                        "published": r.published,
                    }
                    for r in results
                ]
                click.echo(json.dumps(data, indent=2))
            else:
                click.echo(f"\nFound {len(results)} experiences")
                click.echo("-" * 60)
                for exp in results:
                    status = "Published" if exp.published else "Draft"
                    click.echo(f"\n{exp.id}: {exp.title}")
                    click.echo(f"   Duration: {exp.duration_hours}h | Status: {status}")

    run_async(_search())


@cli.command("get")
@click.argument("experience_id", type=int)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--components", help="Specific components (comma-separated)")
@click.pass_context
def get_experience(ctx, experience_id, as_json, components):
    """Get experience details."""

    async def _get():
        async with BokunClient(debug=ctx.obj["debug"]) as client:
            if components:
                comp_list = [c.strip() for c in components.split(",")]
                data = await client.get_experience_components(experience_id, comp_list)
            else:
                data = await client.get_experience(experience_id)

            if as_json:
                click.echo(json.dumps(data, indent=2))
            else:
                click.echo(f"\nExperience {experience_id}")
                click.echo("=" * 60)
                click.echo(f"Title: {data.get('title', 'N/A')}")
                click.echo(f"Published: {data.get('published', False)}")
                click.echo(f"Duration: {data.get('durationHours', 0)}h")
                if data.get("description"):
                    desc = data["description"][:200].replace("<p", "\n<p")
                    click.echo(f"Description: {desc}...")

    run_async(_get())


@cli.command("clone")
@click.argument("source_id", type=int)
@click.option("--title", required=True, help="New experience title")
@click.option("--city", help="New city (e.g., Rovaniemi)")
@click.option("--address", help="New address line 1")
@click.option("--lat", type=float, help="New latitude")
@click.option("--lng", type=float, help="New longitude")
@click.option("--description", help="New description")
@click.option("--dry-run", is_flag=True, help="Show payload without creating")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def clone_cmd(ctx, source_id, title, city, address, lat, lng, description, dry_run, as_json):
    """Clone an experience with modifications."""

    async def _clone():
        async with BokunClient(debug=ctx.obj["debug"]) as client:
            config = CloneConfig(
                title=title,
                new_city=city,
                new_address_line1=address,
                new_latitude=lat,
                new_longitude=lng,
                new_description=description,
                keep_unpublished=True,
            )

            result = await clone_experience(client, source_id, config, dry_run=dry_run)

            if as_json:
                click.echo(json.dumps(result, indent=2, default=str))
            elif dry_run:
                click.echo("\nDry run - payload preview:")
                click.echo(json.dumps(result["payload"], indent=2, default=str)[:2000])
                click.echo("\n... (truncated)")
            else:
                new_id = result.get("id")
                click.echo(f"\n✓ Cloned experience created!")
                click.echo(f"  Source ID: {source_id}")
                click.echo(f"  New ID: {new_id}")
                click.echo(f"  Title: {title}")
                if city:
                    click.echo(f"  Location: {city}")
                click.echo(f"\nView at: https://xwander.bokun.io/experience/{new_id}")

    run_async(_clone())


@cli.command("clone-rovaniemi")
@click.argument("source_id", type=int)
@click.option("--title", required=True, help="New experience title")
@click.option("--description", help="New description")
@click.option("--dry-run", is_flag=True, help="Show payload without creating")
@click.pass_context
def clone_rovaniemi_cmd(ctx, source_id, title, description, dry_run):
    """Clone an Ivalo experience for Rovaniemi."""

    async def _clone():
        async with BokunClient(debug=ctx.obj["debug"]) as client:
            result = await clone_for_rovaniemi(
                client,
                source_id,
                title,
                description,
                dry_run=dry_run,
            )

            if dry_run:
                click.echo("\nDry run - would create Rovaniemi version:")
                click.echo(f"  Title: {title}")
                click.echo(f"  City: Rovaniemi")
                click.echo(f"  Coordinates: 66.5039, 25.7294")
            else:
                new_id = result.get("id")
                click.echo(f"\n✓ Rovaniemi version created!")
                click.echo(f"  Source ID: {source_id}")
                click.echo(f"  New ID: {new_id}")
                click.echo(f"  Title: {title}")
                click.echo(f"\nView at: https://xwander.bokun.io/experience/{new_id}")

    run_async(_clone())


# =============================================================================
# Booking Commands
# =============================================================================


@cli.command("booking")
@click.argument("confirmation_code")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def get_booking(ctx, confirmation_code, as_json):
    """Get booking by confirmation code."""

    async def _get():
        async with BokunClient(debug=ctx.obj["debug"]) as client:
            manager = BookingManager(client)

            try:
                if as_json:
                    data = await manager.get_raw(confirmation_code)
                    click.echo(json.dumps(data, indent=2, default=str))
                else:
                    booking = await manager.get(confirmation_code)
                    click.echo(f"\nBooking: {booking.confirmation_code}")
                    click.echo("=" * 60)
                    click.echo(f"Status: {booking.status.value}")
                    click.echo(f"Customer: {booking.customer_name}")
                    click.echo(f"Email: {booking.customer_email}")
                    click.echo(f"Product: {booking.product_title}")
                    click.echo(f"Date: {booking.start_date}")
                    click.echo(f"Total: {booking.currency} {booking.total_amount}")
            except ValueError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

    run_async(_get())


@cli.command("bookings")
@click.option("--from", "date_from", help="Start date (YYYY-MM-DD)")
@click.option("--to", "date_to", help="End date (YYYY-MM-DD)")
@click.option("--email", help="Customer email")
@click.option("--status", help="Status filter (CONFIRMED, PENDING, etc.)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--limit", default=20, help="Max results")
@click.pass_context
def search_bookings(ctx, date_from, date_to, email, status, as_json, limit):
    """Search bookings."""

    async def _search():
        async with BokunClient(debug=ctx.obj["debug"]) as client:
            manager = BookingManager(client)
            statuses = [status] if status else None

            if as_json:
                result = await manager.search_raw(
                    date_from=date_from,
                    date_to=date_to,
                    customer_email=email,
                    statuses=statuses,
                    page_size=limit,
                )
                click.echo(json.dumps(result, indent=2, default=str))
            else:
                bookings = await manager.search(
                    date_from=date_from,
                    date_to=date_to,
                    customer_email=email,
                    statuses=statuses,
                    page_size=limit,
                )

                click.echo(f"\nFound {len(bookings)} bookings")
                click.echo("-" * 60)
                for b in bookings:
                    click.echo(f"\n{b.confirmation_code}: {b.product_title}")
                    click.echo(f"   {b.customer_name} | {b.start_date} | {b.status.value}")

    run_async(_search())


@cli.command("today")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def today_bookings(ctx, as_json):
    """Show today's bookings."""

    async def _today():
        async with BokunClient(debug=ctx.obj["debug"]) as client:
            manager = BookingManager(client)
            bookings = await manager.today()

            if as_json:
                data = [
                    {
                        "code": b.confirmation_code,
                        "customer": b.customer_name,
                        "product": b.product_title,
                        "status": b.status.value,
                    }
                    for b in bookings
                ]
                click.echo(json.dumps(data, indent=2))
            else:
                click.echo(f"\nToday's Bookings: {len(bookings)}")
                click.echo("=" * 60)
                for b in bookings:
                    click.echo(f"\n{b.confirmation_code}: {b.product_title}")
                    click.echo(f"   Customer: {b.customer_name}")
                    click.echo(f"   Status: {b.status.value}")

    run_async(_today())


# =============================================================================
# Availability Commands
# =============================================================================


@cli.command("availability")
@click.argument("activity_id", type=int)
@click.argument("date")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def check_availability(ctx, activity_id, date, as_json):
    """Check availability for a date."""

    async def _check():
        async with BokunClient(debug=ctx.obj["debug"]) as client:
            result = await client.check_availability(activity_id, date)

            if as_json:
                click.echo(json.dumps(result, indent=2))
            else:
                total = sum(a.get("availabilityCount", 0) for a in result)
                click.echo(f"\nAvailability for {activity_id} on {date}")
                click.echo(f"Total spots: {total}")

                if result:
                    click.echo("\nTime slots:")
                    for slot in result:
                        time = slot.get("startTime", "N/A")
                        count = slot.get("availabilityCount", 0)
                        click.echo(f"  {time}: {count} spots")

    run_async(_check())


def main():
    """Entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
