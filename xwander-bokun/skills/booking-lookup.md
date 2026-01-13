# booking-lookup

Bokun booking lookup and search skill.

## Triggers

- "booking", "reservation", "confirmation code"
- "XWA-", "find booking", "lookup booking"
- "customer booking", "search booking"

## Commands

### Get Booking by Code

```bash
# With or without XWA- prefix
doppler run -- bokun booking XWA-12345
doppler run -- bokun booking 12345

# JSON output
doppler run -- bokun booking XWA-12345 --json
```

### Search Bookings

```bash
# By date range
doppler run -- bokun bookings --from 2026-01-01 --to 2026-01-31

# By customer email
doppler run -- bokun bookings --email customer@example.com

# By status
doppler run -- bokun bookings --status CONFIRMED
doppler run -- bokun bookings --status PENDING

# Combined filters
doppler run -- bokun bookings \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --status CONFIRMED \
  --json
```

### Today's Bookings

```bash
doppler run -- bokun today
doppler run -- bokun today --json
```

## Python API

```python
from xwander_bokun import BokunClient, BookingManager

async with BokunClient() as client:
    manager = BookingManager(client)

    # Get single booking
    booking = await manager.get("XWA-12345")
    print(f"Customer: {booking.customer_name}")
    print(f"Product: {booking.product_title}")
    print(f"Status: {booking.status.value}")

    # Search
    results = await manager.search(
        date_from="2026-01-01",
        date_to="2026-01-31",
        statuses=["CONFIRMED"],
    )

    # Convenience methods
    today = await manager.today()
    confirmed = await manager.confirmed(date_from="2026-01-01")
    pending = await manager.pending()
    by_email = await manager.by_customer("customer@example.com")

    # Count
    count = await manager.count(statuses=["CONFIRMED"])
```

## Booking Status Values

| Status | Description |
|--------|-------------|
| `CONFIRMED` | Booking confirmed |
| `PENDING` | Awaiting confirmation |
| `CANCELLED` | Booking cancelled |
| `ON_REQUEST` | Requires manual approval |

## Output Fields

| Field | Description |
|-------|-------------|
| `confirmation_code` | Unique booking reference |
| `status` | Booking status |
| `customer_name` | Full customer name |
| `customer_email` | Customer email |
| `start_date` | Activity date |
| `product_title` | Product/tour name |
| `total_amount` | Total price |
| `currency` | Currency code |

## Example Output

```
Booking: XWA-12345
============================================================
Status: CONFIRMED
Customer: John Smith
Email: john@example.com
Product: Aurora Camp & Open Fire Dinner
Date: 2026-01-15
Total: EUR 155.00
```

## Error Handling

- **Booking not found**: Check confirmation code format
- **Permission denied**: Verify API key has booking access
