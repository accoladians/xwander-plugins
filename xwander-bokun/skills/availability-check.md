# availability-check

Check tour availability in Bokun.

## Triggers

- "check availability", "availability"
- "spots available", "open slots"
- "book for", "available on"

## Commands

```bash
# Check single date
doppler run -- bokun availability {ACTIVITY_ID} 2026-01-20

# JSON output
doppler run -- bokun availability {ACTIVITY_ID} 2026-01-20 --json
```

## Python API

```python
from xwander_bokun import BokunClient

async with BokunClient() as client:
    slots = await client.check_availability(1107193, "2026-01-20")

    total = sum(s.get("availabilityCount", 0) for s in slots)
    print(f"Total spots: {total}")

    for slot in slots:
        print(f"  {slot['startTime']}: {slot['availabilityCount']} spots")
```

## Output Example

```
Availability for 1107193 on 2026-01-20
Total spots: 12

Time slots:
  20:00: 12 spots
```
