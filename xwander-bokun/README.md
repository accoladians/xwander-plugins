# xwander-bokun

AI-first Bokun booking platform integration for Claude Code.

## Features

- **Async API client** with HMAC-SHA1 authentication
- **Experience management** - create, update, search, clone products
- **Booking operations** - lookup, search, export
- **Product cloning** - duplicate experiences with location/content modifications
- **Click-based CLI** - full command-line interface
- **Skills for Claude Code** - auto-activated on booking/tour queries

## Installation

```bash
cd /srv/plugins/xwander-bokun
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Configuration

Set environment variables (via Doppler or .env):

```bash
export BOKUN_API_KEY="your-api-key"
export BOKUN_API_SECRET="your-api-secret"
export BOKUN_VENDOR_ID="46805"  # Xwander Nordic
```

## CLI Usage

```bash
# Search experiences
doppler run -- bokun search "Aurora"

# Get experience details
doppler run -- bokun get 1107193 --json

# Clone experience for new location
doppler run -- bokun clone 1107193 \
  --title "Aurora Camp Rovaniemi" \
  --city Rovaniemi \
  --lat 66.5039 \
  --lng 25.7294

# Lookup booking
doppler run -- bokun booking XWA-12345

# Search bookings
doppler run -- bokun bookings --from 2026-01-01 --to 2026-01-31

# Today's bookings
doppler run -- bokun today

# Check availability
doppler run -- bokun availability 1107193 2026-01-20
```

## Python API

```python
import asyncio
from xwander_bokun import BokunClient, ExperienceManager, BookingManager
from xwander_bokun import clone_experience, CloneConfig

async def main():
    async with BokunClient() as client:
        # Search experiences
        manager = ExperienceManager(client)
        results = await manager.search("Aurora")
        for exp in results:
            print(f"{exp.id}: {exp.title}")

        # Get booking
        bookings = BookingManager(client)
        booking = await bookings.get("XWA-12345")
        print(f"{booking.customer_name}: {booking.product_title}")

        # Clone experience
        config = CloneConfig(
            title="Aurora Camp Rovaniemi",
            new_city="Rovaniemi",
            new_latitude=66.5039,
            new_longitude=25.7294,
        )
        result = await clone_experience(client, 1107193, config)
        print(f"Created: {result.get('id')}")

asyncio.run(main())
```

## Product Cloning

Clone existing products with modifications:

```python
from xwander_bokun import clone_for_rovaniemi

async with BokunClient() as client:
    # Convenience function for Ivalo -> Rovaniemi cloning
    result = await clone_for_rovaniemi(
        client,
        source_id=1107193,
        title="Aurora Camp Rovaniemi",
        description="<p>Updated itinerary for Rovaniemi...</p>",
    )
```

### CloneConfig Options

| Field | Description |
|-------|-------------|
| `title` | New product title (required) |
| `new_city` | New city name |
| `new_address_line1` | New street address |
| `new_postal_code` | New postal code |
| `new_latitude` | New GPS latitude |
| `new_longitude` | New GPS longitude |
| `new_start_point_title` | New start point name |
| `new_description` | New HTML description |
| `new_excerpt` | New short excerpt |
| `add_flags` | Flags to add (list) |
| `add_keywords` | Keywords for SEO (list) |
| `keep_unpublished` | Keep as draft (default: True) |

## API Reference

### BokunClient

Async HTTP client with authentication:

```python
async with BokunClient(debug=True) as client:
    # Low-level API
    result = await client.get("/activity.json/123")
    result = await client.post("/booking.json/search", {"customerEmail": "..."})

    # High-level methods
    exp = await client.get_experience(123)
    bookings = await client.search_bookings(date_from="2026-01-01")
```

### ExperienceManager

Product/experience operations:

```python
manager = ExperienceManager(client)
exp = await manager.get(123)
results = await manager.search("Northern Lights")
await manager.update_title(123, "New Title")
await manager.update_duration(123, hours=4)
await manager.publish(123)
```

### BookingManager

Booking operations:

```python
bookings = BookingManager(client)
booking = await bookings.get("XWA-12345")
today = await bookings.today()
confirmed = await bookings.confirmed(date_from="2026-01-01")
count = await bookings.count(statuses=["CONFIRMED"])
```

## Skills (Claude Code)

Auto-activated skills for AI assistance:

- `booking-lookup` - "Find booking XWA-12345"
- `experience-ops` - "Create Aurora Camp for Rovaniemi"
- `availability-check` - "Check availability Dec 25"
- `product-catalog` - "List Northern Lights tours"

## Examples

See `/examples/` for complete examples:

- `clone_aurora_camp.py` - Clone Ivalo product for Rovaniemi

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=xwander_bokun --cov-report=html
```

## License

MIT - Xwander Platform
