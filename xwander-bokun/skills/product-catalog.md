# product-catalog

Browse and search Bokun product catalog.

## Triggers

- "list tours", "list products", "list experiences"
- "search tours", "find products"
- "product catalog", "tour catalog"

## Commands

```bash
# Search by query
doppler run -- bokun search "Northern Lights"
doppler run -- bokun search "Aurora" --limit 50

# JSON output
doppler run -- bokun search "Husky" --json

# Get specific product
doppler run -- bokun get {PRODUCT_ID}
doppler run -- bokun get {PRODUCT_ID} --json
```

## Python API

```python
from xwander_bokun import BokunClient, ExperienceManager

async with BokunClient() as client:
    manager = ExperienceManager(client)

    # Search
    results = await manager.search("Northern Lights", page_size=50)
    for exp in results:
        print(f"{exp.id}: {exp.title} ({exp.duration_hours}h)")

    # Get details
    exp = await manager.get(1107193)
    print(f"Title: {exp.title}")
    print(f"Duration: {exp.duration_hours}h {exp.duration_minutes}m")
    print(f"Difficulty: {exp.difficulty_level.value}")
```

## Known Products

| ID | Product | Duration | Location |
|----|---------|----------|----------|
| 1107193 | Aurora Camp & Open Fire Dinner | 3h | Ivalo |

## Search Tips

- Use specific keywords: "Aurora", "Husky", "Reindeer"
- Filter by location in results
- Check `published` status
