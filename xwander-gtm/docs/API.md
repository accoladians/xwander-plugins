# xwander-gtm API Documentation

## Module Structure

```
xwander_gtm/
├── client.py         # GTM API client
├── tags.py           # Tag operations
├── variables.py      # Variable operations
├── triggers.py       # Trigger operations
├── workspace.py      # Workspace/version operations
├── publishing.py     # Publishing operations
└── exceptions.py     # Custom exceptions
```

## GTMClient

Base client for GTM API operations.

```python
from xwander_gtm import GTMClient

client = GTMClient(credentials_path="~/.gtm-credentials.yaml")
```

### Methods

#### `get_workspace_id(account_id, container_id, workspace_name="Default Workspace")`
Get workspace ID by name.

**Returns**: `str` - Workspace ID

#### `list_resources(resource_type, account_id, container_id, workspace_id=None)`
List GTM resources (tags, triggers, variables, folders).

**Parameters**:
- `resource_type`: 'tags', 'triggers', 'variables', or 'folders'

**Returns**: `list` - List of resources

#### `get_resource(resource_type, account_id, container_id, resource_id, workspace_id=None)`
Get specific resource.

**Returns**: `dict` - Resource object

#### `create_resource(resource_type, account_id, container_id, body, workspace_id=None)`
Create resource.

**Returns**: `dict` - Created resource

#### `update_resource(resource_type, account_id, container_id, resource_id, body, workspace_id=None)`
Update resource.

**Returns**: `dict` - Updated resource

## TagManager

Manage GTM tags.

```python
from xwander_gtm import GTMClient, TagManager

client = GTMClient()
tag_mgr = TagManager(client)
```

### Methods

#### `list_tags(account_id, container_id, workspace_id=None, tag_type=None)`
List all tags.

**Parameters**:
- `tag_type`: Optional filter (e.g., 'awct', 'gaawe')

**Returns**: `list[dict]` - List of tags

#### `get_tag(account_id, container_id, tag_id, workspace_id=None)`
Get specific tag.

**Returns**: `dict` - Tag object

#### `create_tag(account_id, container_id, name, tag_type, parameters, firing_trigger_ids, workspace_id=None, folder_id=None, paused=False)`
Create new tag.

**Returns**: `dict` - Created tag

#### `update_tag(account_id, container_id, tag_id, updates, workspace_id=None)`
Update existing tag.

**Returns**: `dict` - Updated tag

#### `delete_tag(account_id, container_id, tag_id, workspace_id=None)`
Delete tag.

**Returns**: `None`

#### `list_conversion_tags(account_id, container_id, workspace_id=None, include_ec_status=True)`
List Google Ads conversion tags.

**Returns**: `list[dict]` - List with fields:
- `tagId`, `name`, `type`, `conversionId`, `conversionLabel`
- `ecEnabled`, `ecVariable` (if include_ec_status=True)

#### `update_conversion_tag(account_id, container_id, tag_id, conversion_id, label, workspace_id=None, unpause=False)`
Update conversion tag.

**Returns**: `dict` - Updated tag

#### `enable_enhanced_conversions(account_id, container_id, tag_id, user_data_variable, workspace_id=None)`
Enable Enhanced Conversions.

**Parameters**:
- `user_data_variable`: Name of User-Provided Data variable

**Returns**: `dict` - Updated tag

## VariableManager

Manage GTM variables.

```python
from xwander_gtm import GTMClient, VariableManager

client = GTMClient()
var_mgr = VariableManager(client)
```

### Methods

#### `list_variables(account_id, container_id, workspace_id=None)`
List all variables.

**Returns**: `list[dict]` - List of variables

#### `get_variable(account_id, container_id, variable_id, workspace_id=None)`
Get specific variable.

**Returns**: `dict` - Variable object

#### `create_data_layer_variable(account_id, container_id, name, data_layer_name, workspace_id=None, folder_id=None, default_value=None)`
Create Data Layer Variable.

**Returns**: `dict` - Created variable

#### `create_user_data_variable(account_id, container_id, name="EC - User Data", workspace_id=None, auto_mode=True, folder_id=None)`
Create Enhanced Conversions User-Provided Data variable.

**Parameters**:
- `auto_mode`: If True, auto-detect; if False, use dataLayer mapping

**Returns**: `dict` - Created variable

## TriggerManager

Manage GTM triggers.

```python
from xwander_gtm import GTMClient, TriggerManager

client = GTMClient()
trigger_mgr = TriggerManager(client)
```

### Methods

#### `list_triggers(account_id, container_id, workspace_id=None)`
List all triggers.

**Returns**: `list[dict]` - List of triggers

#### `get_trigger(account_id, container_id, trigger_id, workspace_id=None)`
Get specific trigger.

**Returns**: `dict` - Trigger object

#### `create_custom_event_trigger(account_id, container_id, name, event_pattern, workspace_id=None, folder_id=None, use_regex=True)`
Create custom event trigger.

**Parameters**:
- `event_pattern`: Event name or regex pattern
- `use_regex`: Use regex matching

**Returns**: `dict` - Created trigger

#### `create_page_view_trigger(account_id, container_id, name, url_pattern=None, workspace_id=None, folder_id=None)`
Create page view trigger.

**Returns**: `dict` - Created trigger

## WorkspaceManager

Manage workspaces and versions.

```python
from xwander_gtm import GTMClient, WorkspaceManager

client = GTMClient()
workspace_mgr = WorkspaceManager(client)
```

### Methods

#### `sync(account_id, container_id, workspace_id=None)`
Sync workspace before version creation.

**Important**: This is CRITICAL for proper version persistence.

**Returns**: `dict` - Sync response with potential mergeConflict field

#### `create_version(account_id, container_id, version_name, notes="", workspace_id=None, auto_sync=True)`
Create container version.

**Parameters**:
- `auto_sync`: Auto-sync before creating (recommended: True)

**Returns**: `dict` - containerVersion object

#### `list_versions(account_id, container_id, include_deleted=False)`
List container versions.

**Returns**: `list[dict]` - List of version headers

#### `get_version(account_id, container_id, version_id)`
Get specific version.

**Returns**: `dict` - containerVersion object

#### `get_latest_version(account_id, container_id)`
Get latest version.

**Returns**: `dict` - Latest containerVersion object

## Publisher

Publish container versions.

```python
from xwander_gtm import GTMClient, Publisher

client = GTMClient()
publisher = Publisher(client)
```

### Methods

#### `publish(account_id, container_id, version_id)`
Publish version to LIVE.

**Returns**: `dict` - Published version metadata

#### `get_live_version(account_id, container_id)`
Get currently live version.

**Returns**: `dict` - Live containerVersion object

## Exceptions

```python
from xwander_gtm.exceptions import (
    GTMError,
    AuthenticationError,
    WorkspaceConflictError,
    PublishingError,
    RateLimitError,
    ValidationError,
    ResourceNotFoundError,
    DuplicateResourceError
)
```

### Exception Hierarchy

- `GTMError` (base, exit_code=1)
  - `AuthenticationError` (exit_code=3)
  - `WorkspaceConflictError` (exit_code=4)
  - `PublishingError` (exit_code=5)
  - `RateLimitError` (exit_code=2)
  - `ValidationError` (exit_code=1)
  - `ResourceNotFoundError` (exit_code=1)
  - `DuplicateResourceError` (exit_code=1)

### Exception Attributes

- `message`: Error message string
- `details`: Dictionary with additional error context
- `exit_code`: Exit code for CLI

## Complete Example

```python
from xwander_gtm import (
    GTMClient,
    TagManager,
    VariableManager,
    WorkspaceManager,
    Publisher,
    GTMError
)

# Configuration
ACCOUNT_ID = "6215694602"
CONTAINER_ID = "176670340"

try:
    # Initialize
    client = GTMClient()
    tag_mgr = TagManager(client)
    var_mgr = VariableManager(client)
    workspace_mgr = WorkspaceManager(client)
    publisher = Publisher(client)

    # 1. Create Enhanced Conversions variable
    ec_var = var_mgr.create_user_data_variable(
        ACCOUNT_ID, CONTAINER_ID,
        name="EC - User Data",
        auto_mode=True
    )
    print(f"Created variable: {ec_var['name']}")

    # 2. List conversion tags
    conv_tags = tag_mgr.list_conversion_tags(ACCOUNT_ID, CONTAINER_ID)
    print(f"Found {len(conv_tags)} conversion tags")

    # 3. Enable EC on tags
    for tag in conv_tags:
        if not tag['ecEnabled']:
            tag_mgr.enable_enhanced_conversions(
                ACCOUNT_ID, CONTAINER_ID,
                tag['tagId'], "EC - User Data"
            )
            print(f"Enabled EC on: {tag['name']}")

    # 4. Create version
    version = workspace_mgr.create_version(
        ACCOUNT_ID, CONTAINER_ID,
        version_name="Enable Enhanced Conversions",
        notes="Enabled EC on all conversion tags via API"
    )
    print(f"Created version: {version['containerVersionId']}")

    # 5. Publish
    publisher.publish(ACCOUNT_ID, CONTAINER_ID, version['containerVersionId'])
    print("Published to LIVE!")

except GTMError as e:
    print(f"Error: {e.message}")
    if e.details:
        print(f"Details: {e.details}")
    exit(e.exit_code)
```

## Rate Limits

GTM API rate limits (as of 2026):
- 100 requests per 100 seconds
- 1,500 requests per day

Handle rate limits:

```python
from xwander_gtm.exceptions import RateLimitError
import time

for tag_id in tag_ids:
    try:
        tag_mgr.enable_enhanced_conversions(account_id, container_id, tag_id, var_name)
    except RateLimitError:
        print("Rate limit hit, waiting 60 seconds...")
        time.sleep(60)
        tag_mgr.enable_enhanced_conversions(account_id, container_id, tag_id, var_name)
```

## Best Practices

1. **Always sync workspace** before creating versions (auto_sync=True by default)
2. **Use try/except** for all API operations
3. **Batch operations** to avoid rate limits
4. **Verify changes** in GTM UI after API operations
5. **Test in Preview mode** before publishing
6. **Use descriptive version names** for audit trail
