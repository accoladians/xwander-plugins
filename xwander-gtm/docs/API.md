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

#### `create_user_data_variable(account_id, container_id, name="EC - User Data", workspace_id=None, auto_mode=True, folder_id=None, email_var=None, phone_var=None, first_name_var=None, last_name_var=None)`
Create Enhanced Conversions User-Provided Data variable.

**Variable Type**: `awec` (Google Ads Web Enhanced Conversions)

> **Warning**: Do NOT use type `gtes` (Google Tag Enhanced Settings) for EC - it causes compiler errors.

**Parameters**:
- `name`: Variable name (default: "EC - User Data")
- `auto_mode`: If True, auto-detect form fields (recommended for standard HTML forms); if False, use dataLayer mapping
- `folder_id`: Optional folder ID
- `email_var`: MANUAL mode - GTM variable for email (e.g., "{{DLV - email}}")
- `phone_var`: MANUAL mode - GTM variable for phone
- `first_name_var`: MANUAL mode - GTM variable for first name
- `last_name_var`: MANUAL mode - GTM variable for last name

**Returns**: `dict` - Created variable with structure:
```json
{
  "variableId": "6",
  "name": "User-Provided Data",
  "type": "awec",
  "parameter": [
    {"type": "template", "key": "mode", "value": "AUTO"},
    {"type": "boolean", "key": "autoPhoneEnabled", "value": "true"},
    {"type": "boolean", "key": "autoAddressEnabled", "value": "true"},
    {"type": "boolean", "key": "autoEmailEnabled", "value": "true"}
  ]
}
```

**Raises**:
- `ValidationError`: If MANUAL mode without any field mappings
- `DuplicateResourceError`: If variable name already exists

**Example (AUTO mode)**:
```python
var = var_mgr.create_user_data_variable(
    account_id, container_id,
    name="User-Provided Data"
)
```

**Example (MANUAL mode)**:
```python
var = var_mgr.create_user_data_variable(
    account_id, container_id,
    name="EC - Custom Data",
    auto_mode=False,
    email_var="{{DLV - email}}",
    phone_var="{{DLV - phone}}"
)
```

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

#### `validate_workspace(account_id, container_id, workspace_id=None, strict=False)`
Validate workspace configuration before version creation.

Checks for common issues that cause GTM compiler errors:
1. Variable type requirements (e.g., `awec` needs `mode` parameter)
2. Undefined variable references in tags/triggers
3. Invalid trigger references in tags
4. Missing required tag parameters

**Parameters**:
- `workspace_id`: Workspace ID (auto-detected if None)
- `strict`: If True, raises ValidationError on any issue; otherwise returns issues

**Returns**: `Tuple[bool, List[Dict]]` - (is_valid, list of issues)

Each issue is a dict with:
- `type`: 'error' or 'warning'
- `resource_type`: 'variable', 'trigger', or 'tag'
- `resource_id`: GTM resource ID
- `resource_name`: Resource name
- `message`: Description of the issue

**Example**:
```python
is_valid, issues = workspace_mgr.validate_workspace(account_id, container_id)
for issue in issues:
    if issue['type'] == 'error':
        print(f"Error in {issue['resource_type']} {issue['resource_name']}: {issue['message']}")
```

**Raises**:
- `ValidationError`: If strict=True and validation fails
- `GTMError`: If API calls fail

#### `create_version(account_id, container_id, version_name, notes="", workspace_id=None, auto_sync=True, validate=True)`
Create container version.

**Parameters**:
- `version_name`: Version name (e.g., "v44 - Enable EC")
- `notes`: Version notes
- `auto_sync`: Auto-sync before creating (recommended: True)
- `validate`: Validate workspace before version creation (recommended: True)

**Returns**: `dict` - containerVersion object

**Raises**:
- `ValidationError`: If validation fails (when validate=True)
- `GTMError`: If version creation fails or compiler error
- `WorkspaceConflictError`: If workspace has unresolvable conflicts

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
    GTMError,
    ValidationError
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

    # 1. Create Enhanced Conversions variable (AUTO mode)
    ec_var = var_mgr.create_user_data_variable(
        ACCOUNT_ID, CONTAINER_ID,
        name="EC - User Data",
        auto_mode=True  # Recommended for standard forms
    )
    print(f"Created variable: {ec_var['name']} (type: {ec_var['type']})")

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

    # 4. Validate workspace before version creation
    is_valid, issues = workspace_mgr.validate_workspace(ACCOUNT_ID, CONTAINER_ID)
    if not is_valid:
        print("Validation errors found:")
        for issue in issues:
            if issue['type'] == 'error':
                print(f"  - {issue['resource_type']} '{issue['resource_name']}': {issue['message']}")
        exit(1)

    # 5. Create version (validation also runs automatically here)
    version = workspace_mgr.create_version(
        ACCOUNT_ID, CONTAINER_ID,
        version_name="Enable Enhanced Conversions",
        notes="Enabled EC on all conversion tags via API",
        validate=True  # Default - catches issues before version creation
    )
    print(f"Created version: {version['containerVersionId']}")

    # 6. Publish
    publisher.publish(ACCOUNT_ID, CONTAINER_ID, version['containerVersionId'])
    print("Published to LIVE!")

except ValidationError as e:
    print(f"Validation failed: {e.message}")
    if e.details and 'issues' in e.details:
        for issue in e.details['issues']:
            print(f"  - {issue['type'].upper()}: {issue['message']}")
    exit(e.exit_code)

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

1. **Validate workspace** before creating versions (validate=True by default)
2. **Use dry-run** for CLI commands to preview changes
3. **Always sync workspace** before creating versions (auto_sync=True by default)
4. **Use try/except** for all API operations
5. **Batch operations** to avoid rate limits
6. **Verify changes** in GTM UI after API operations
7. **Test in Preview mode** before publishing
8. **Use descriptive version names** for audit trail

## Safety Checklist

Before any GTM changes:
- [ ] Run `xw gtm validate-workspace` to catch issues early
- [ ] Use `--dry-run` to preview changes
- [ ] Test in GTM Preview mode before publishing
- [ ] Only publish after verification

## For AI Agents

See **[CLAUDE.md](../CLAUDE.md)** for:
- Decision trees for choosing operations
- Common workflow patterns
- Error handling reference
- Safety checklist optimized for automation
