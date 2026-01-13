# xwander-gtm

Google Tag Manager operations plugin for the xwander platform.

## Features

- Modular GTM API client with proper error handling
- Tag management (list, get, create, update, delete)
- Variable management (data layer variables, Enhanced Conversions variables)
- Trigger management (custom events, page views)
- Workspace management with automatic conflict resolution
- Version creation with proper sync validation
- Version publishing to LIVE
- CLI interface via `xw gtm` commands

## Architecture

### Modules

- **client.py**: Low-level GTM API client with authentication and error handling
- **tags.py**: Tag CRUD operations, including conversion tag management
- **variables.py**: Variable CRUD operations
- **triggers.py**: Trigger CRUD operations
- **workspace.py**: Workspace sync and version management
- **publishing.py**: Version publishing operations
- **exceptions.py**: Custom exception hierarchy with exit codes
- **cli.py**: Click-based CLI interface

### Exception Hierarchy

```
GTMError (exit_code=1)
├── AuthenticationError (exit_code=3)
├── WorkspaceConflictError (exit_code=4)
├── PublishingError (exit_code=5)
├── RateLimitError (exit_code=2)
├── ValidationError (exit_code=1)
├── ResourceNotFoundError (exit_code=1)
└── DuplicateResourceError (exit_code=1)
```

## Installation

```bash
cd /srv/plugins/xwander-gtm
pip install -e .
```

## Configuration

Place GTM OAuth credentials at `~/.gtm-credentials.yaml`:

```yaml
refresh_token: "..."
token_uri: "https://oauth2.googleapis.com/token"
client_id: "..."
client_secret: "..."
scopes:
  - https://www.googleapis.com/auth/tagmanager.readonly
  - https://www.googleapis.com/auth/tagmanager.edit.containers
  - https://www.googleapis.com/auth/tagmanager.edit.containerversions
  - https://www.googleapis.com/auth/tagmanager.publish
```

## CLI Usage

### List Tags

```bash
# List all tags
xw gtm list-tags

# List conversion tags only
xw gtm list-tags --type awct

# List conversion tags with EC status
xw gtm list-conversion-tags

# JSON output
xw gtm list-tags --json
```

### Manage Tags

```bash
# Get tag details
xw gtm get-tag --tag-id 32

# Enable Enhanced Conversions
xw gtm enable-ec --tag-id 7 --variable-name "User-Provided Data"
```

### Variables

```bash
# List all variables
xw gtm list-variables

# Create data layer variable
xw gtm create-variable --name "DLV - ecommerce.value" --datalayer-name "ecommerce.value"

# Create Enhanced Conversions variable
xw gtm create-ec-variable --name "EC - User Data"

# Manual mode (dataLayer mapping)
xw gtm create-ec-variable --name "EC - Manual Data" --manual
```

### Triggers

```bash
# List all triggers
xw gtm list-triggers

# Create custom event trigger
xw gtm create-trigger --name "GA4 | Purchase Events" --event "purchase|transaction" --regex
```

### Workspace & Versions

```bash
# Sync workspace
xw gtm sync-workspace

# Create version
xw gtm create-version --name "v39 - Fix GCLID capture" --notes "Updated GTM tag 66"

# List versions
xw gtm list-versions

# Publish version
xw gtm publish --version-id 39

# Publish latest version
xw gtm publish --latest
```

## Python API Usage

```python
from xwander_gtm import (
    GTMClient,
    TagManager,
    VariableManager,
    WorkspaceManager,
    Publisher
)

# Initialize client
client = GTMClient()

# Manage tags
tag_mgr = TagManager(client)
tags = tag_mgr.list_conversion_tags('6215694602', '176670340')

# Enable Enhanced Conversions
tag_mgr.enable_enhanced_conversions(
    '6215694602', '176670340',
    tag_id='7',
    user_data_variable='User-Provided Data'
)

# Create version
workspace_mgr = WorkspaceManager(client)
version = workspace_mgr.create_version(
    '6215694602', '176670340',
    version_name='v40 - Automated update',
    notes='Created via API'
)

# Publish
publisher = Publisher(client)
publisher.publish('6215694602', '176670340', version['containerVersionId'])
```

## Migration from Toolkit Scripts

This plugin replaces the following toolkit scripts:

- `gtm_updater.py` → `TagManager`, `VariableManager`
- `gtm_publish_version.py` → `Publisher`
- `gtm_bokun_import.py` → Combined operations using all managers
- `gtm_add_ga4_linker.py` → `TagManager.update_tag()`

### Migration Examples

#### Old: List conversion tags
```bash
python3 toolkit/gtm_updater.py list --account-id 6215694602 --container-id 176670340
```

#### New:
```bash
xw gtm list-conversion-tags
```

#### Old: Enable Enhanced Conversions
```bash
python3 toolkit/gtm_updater.py enable-ec --account-id 6215694602 --container-id 176670340 --tag-id 7 --variable-name "User-Provided Data"
```

#### New:
```bash
xw gtm enable-ec --tag-id 7 --variable-name "User-Provided Data"
```

#### Old: Publish version
```bash
python3 toolkit/gtm_publish_version.py --account-id 6215694602 --container-id 176670340 --version-id 39
```

#### New:
```bash
xw gtm publish --version-id 39
```

## Testing

```bash
# Run tests
cd /srv/plugins/xwander-gtm
pytest tests/

# Run specific test
pytest tests/test_gtm.py::test_list_tags -v
```

## Error Handling

All CLI commands handle errors gracefully:

```bash
xw gtm get-tag --tag-id 999
# Error: Resource not found during get tag 999
# Exit code: 1

xw gtm publish --version-id 999
# Error: Version 999 not found
# Exit code: 5
```

## Default Values

The plugin uses default values from `/srv/xwander-platform/xwander.com/growth/knowledge/gtm.json`:

- Account ID: `6215694602`
- Container ID: `176670340`

Override with `--account-id` and `--container-id` flags.

## Development

### Adding New Commands

1. Add method to appropriate manager class (e.g., `TagManager`)
2. Add CLI command in `cli.py`
3. Add tests in `tests/test_gtm.py`
4. Update documentation

### Code Structure

```
xwander-gtm/
├── xwander_gtm/
│   ├── __init__.py       # Package exports
│   ├── client.py         # GTM API client
│   ├── tags.py           # Tag operations
│   ├── triggers.py       # Trigger operations
│   ├── variables.py      # Variable operations
│   ├── workspace.py      # Workspace/version operations
│   ├── publishing.py     # Publishing operations
│   ├── exceptions.py     # Custom exceptions
│   └── cli.py            # CLI interface
├── docs/
│   ├── QUICK_REFERENCE.json
│   └── API.md
├── tests/
│   └── test_gtm.py
├── skills/
│   └── gtm-ops.md
├── setup.py
└── README.md
```

## License

Internal use only - Xwander Growth Team
