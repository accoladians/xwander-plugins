# GA4 Operations Skill

Quick GA4 operations for Xwander Nordic growth agents.

## Quick Commands

### Get Traffic Report

```bash
xwander-ga4 traffic-sources --days 30
```

Returns: source, medium, sessions, users, bounceRate

### Get Top Pages

```bash
xwander-ga4 top-pages --days 30
```

Returns: pagePath, sessions, users, avgSessionDuration

### Get Conversions

```bash
xwander-ga4 conversions --days 30
```

Returns: eventName, eventCount, eventValue

### Get Daily Summary

```bash
xwander-ga4 daily-summary --days 30
```

Returns: date, sessions, users, eventCount

### Realtime Users

```bash
xwander-ga4 realtime
```

Returns: country, activeUsers (real-time)

## Custom Reports

### Template: By Date and Source

```bash
xwander-ga4 report \
  --dimensions date source \
  --metrics sessions users eventCount \
  --days 30 \
  --format table
```

### Template: By Page Path

```bash
xwander-ga4 report \
  --dimensions pagePath \
  --metrics sessions users bounceRate \
  --days 30 \
  --limit 50
```

### Template: By Event

```bash
xwander-ga4 report \
  --dimensions eventName \
  --metrics eventCount eventValue \
  --days 30 \
  --format json
```

### Template: By Geography

```bash
xwander-ga4 report \
  --dimensions country city \
  --metrics sessions users \
  --days 30 \
  --limit 50
```

### Template: By Campaign

```bash
xwander-ga4 report \
  --dimensions campaign medium \
  --metrics sessions conversions conversionValue \
  --days 30
```

## Custom Dimensions

### Create Product Type Dimension

```bash
xwander-ga4 dimension create \
  --display-name "Product Type" \
  --parameter-name product_type \
  --scope EVENT \
  --description "Day tours vs multi-day packages"
```

### List Dimensions

```bash
xwander-ga4 dimension list
```

### List Event Dimensions

```bash
xwander-ga4 dimension list --scope EVENT
```

## Audiences

### List All Audiences

```bash
xwander-ga4 audience list
```

### List Largest Audiences

```bash
xwander-ga4 audience list --sort-by-size
```

### Search Audiences

```bash
xwander-ga4 audience search "paid search"
xwander-ga4 audience search "Northern Lights"
```

## Python API

### Quick Report

```python
from xwander_ga4 import GA4DataClient, ReportBuilder, ReportFormatter

client = GA4DataClient('358203796')
builder = ReportBuilder(client)

# Get traffic
result = builder.traffic_sources(days=30)

# Display
formatter = ReportFormatter()
print(formatter.table(result))
```

### Create Dimension

```python
from xwander_ga4 import GA4AdminClient, DimensionManager

admin = GA4AdminClient('358203796')
manager = DimensionManager(admin)

result = manager.create(
    display_name='Product Type',
    parameter_name='product_type',
    scope='EVENT'
)
print(f"Created: {result['api_name']}")
```

### List Audiences

```python
from xwander_ga4 import GA4AdminClient, AudienceManager

admin = GA4AdminClient('358203796')
manager = AudienceManager(admin)

audiences = manager.sorted_by_size()
for aud in audiences[:10]:
    print(f"{aud['name']}: {aud['member_count']:,}")
```

## Common Issues

### No Data Returned

- Check date range has data in GA4
- Verify dimensions/metrics are valid
- Try with `--format json` to see full response

### Custom Dimension Not Found

- Wait 24 hours after creation
- Events must send the parameter before it appears
- Use `xwander-ga4 dimension list` to verify creation

### API Quota Exceeded

- Check quota: `result['property_quota']['tokens_remaining']`
- Wait 1 hour and retry
- Reduce limit or date range

## Reference

- Property: 358203796 (Xwander Nordic)
- Account: 89715181
- Timezone: Europe/Helsinki
- Currency: EUR

See full docs: [API.md](../docs/API.md)
