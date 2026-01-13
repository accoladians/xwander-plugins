# experience-ops

Bokun experience/product management skill.

## Triggers

- "create experience", "create product", "create tour"
- "clone experience", "clone product", "duplicate tour"
- "update experience", "update product"
- "bokun experience", "bokun product"

## Commands

### Get Experience Details

```bash
doppler run -- bokun get {EXPERIENCE_ID}
doppler run -- bokun get {EXPERIENCE_ID} --json
doppler run -- bokun get {EXPERIENCE_ID} --components TITLE,PRICING,FLAGS
```

### Search Experiences

```bash
doppler run -- bokun search "Aurora"
doppler run -- bokun search "Northern Lights" --json --limit 50
```

### Clone Experience

Clone an existing product with modifications:

```bash
# Basic clone with new title and location
doppler run -- bokun clone {SOURCE_ID} \
  --title "New Product Name" \
  --city "Rovaniemi" \
  --lat 66.5039 \
  --lng 25.7294

# Dry run to preview
doppler run -- bokun clone {SOURCE_ID} --title "Test" --dry-run

# Clone Ivalo product for Rovaniemi (convenience)
doppler run -- bokun clone-rovaniemi {SOURCE_ID} \
  --title "Aurora Camp Rovaniemi"
```

### Python API

```python
from xwander_bokun import BokunClient, ExperienceManager, CloneConfig, clone_experience

async with BokunClient() as client:
    # Get experience
    manager = ExperienceManager(client)
    exp = await manager.get(1107193)
    print(f"Title: {exp.title}")
    print(f"Duration: {exp.duration_hours}h")

    # Clone with config
    config = CloneConfig(
        title="Aurora Camp Rovaniemi",
        new_city="Rovaniemi",
        new_latitude=66.5039,
        new_longitude=25.7294,
        add_flags=["NORTHERN_LIGHTS"],
    )
    result = await clone_experience(client, 1107193, config)
    print(f"Created: {result.get('id')}")
```

## Known Product IDs

| ID | Product | Location |
|----|---------|----------|
| 1107193 | Aurora Camp & Open Fire Dinner | Ivalo |

## Workflow: Create Rovaniemi Product

1. **Get source product**:
   ```bash
   doppler run -- bokun get 1107193 --json > /tmp/source.json
   ```

2. **Clone with modifications**:
   ```bash
   doppler run -- bokun clone-rovaniemi 1107193 \
     --title "Aurora Camp Rovaniemi"
   ```

3. **Verify in Bokun UI**: https://xwander.bokun.io/experience/{NEW_ID}

4. **Add missing content**:
   - Photos
   - Pricing
   - Availability schedule

5. **Publish when ready**

## Flags Reference

| Flag | Description |
|------|-------------|
| `INSTANT_CONFIRMATION` | No approval needed |
| `SMALL_GROUP` | Limited group size |
| `PICKUP_AVAILABLE` | Hotel pickup offered |
| `NORTHERN_LIGHTS` | Aurora experience |
| `FAMILY_FRIENDLY` | Suitable for families |

## Error Handling

- **404**: Experience not found - verify ID
- **403**: Permission denied - check API key permissions
- **429**: Rate limited - wait and retry
