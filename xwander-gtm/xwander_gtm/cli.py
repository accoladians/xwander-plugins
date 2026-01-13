"""
CLI for xwander-gtm plugin.
"""

import sys
import json
import click
from typing import Optional

from .client import GTMClient
from .workspace import WorkspaceManager
from .publishing import Publisher
from .tags import TagManager
from .triggers import TriggerManager
from .variables import VariableManager
from .exceptions import GTMError

# Default values from gtm.json
DEFAULT_ACCOUNT_ID = "6215694602"
DEFAULT_CONTAINER_ID = "176670340"


@click.group()
def cli():
    """Google Tag Manager operations"""
    pass


# ============================================================================
# TAG COMMANDS
# ============================================================================

@cli.command('list-tags')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--type', 'tag_type', help='Filter by tag type (e.g., awct, gaawe)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list_tags_cmd(account_id, container_id, tag_type, output_json):
    """List all tags in container"""
    try:
        client = GTMClient()
        tag_mgr = TagManager(client)

        tags = tag_mgr.list_tags(account_id, container_id, tag_type=tag_type)

        if output_json:
            click.echo(json.dumps(tags, indent=2))
        else:
            click.echo(f"\nFound {len(tags)} tags:\n")
            click.echo(f"{'ID':<8} {'Name':<35} {'Type':<15} {'Paused'}")
            click.echo("-" * 70)
            for tag in tags:
                paused = "Yes" if tag.get('paused') else "No"
                click.echo(f"{tag['tagId']:<8} {tag['name']:<35} {tag['type']:<15} {paused}")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('get-tag')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--tag-id', required=True, help='Tag ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def get_tag_cmd(account_id, container_id, tag_id, output_json):
    """Get specific tag details"""
    try:
        client = GTMClient()
        tag_mgr = TagManager(client)

        tag = tag_mgr.get_tag(account_id, container_id, tag_id)

        if output_json:
            click.echo(json.dumps(tag, indent=2))
        else:
            click.echo(f"\nTag ID: {tag['tagId']}")
            click.echo(f"Name: {tag['name']}")
            click.echo(f"Type: {tag['type']}")
            click.echo(f"Paused: {tag.get('paused', False)}")
            click.echo(f"\nParameters:")
            for param in tag.get('parameter', []):
                click.echo(f"  {param['key']}: {param.get('value', 'N/A')}")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('list-conversion-tags')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list_conversion_tags_cmd(account_id, container_id, output_json):
    """List Google Ads conversion tags"""
    try:
        client = GTMClient()
        tag_mgr = TagManager(client)

        tags = tag_mgr.list_conversion_tags(account_id, container_id)

        if output_json:
            click.echo(json.dumps(tags, indent=2))
        else:
            click.echo(f"\nFound {len(tags)} conversion tags:\n")
            click.echo(f"{'ID':<8} {'Name':<25} {'Conv ID':<12} {'EC':<5} {'Status'}")
            click.echo("-" * 70)
            for tag in tags:
                ec = "Yes" if tag.get('ecEnabled') else "No"
                status = "Paused" if tag.get('paused') else "Active"
                conv_id = tag.get('conversionId', 'N/A')
                click.echo(f"{tag['tagId']:<8} {tag['name']:<25} {conv_id:<12} {ec:<5} {status}")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('enable-ec')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--tag-id', required=True, help='Tag ID to update')
@click.option('--variable-name', default='User-Provided Data', help='User Data variable name')
def enable_ec_cmd(account_id, container_id, tag_id, variable_name):
    """Enable Enhanced Conversions on a conversion tag"""
    try:
        client = GTMClient()
        tag_mgr = TagManager(client)

        click.echo(f"Enabling Enhanced Conversions on tag {tag_id}...")
        tag = tag_mgr.enable_enhanced_conversions(
            account_id, container_id, tag_id, variable_name
        )

        click.echo(f"Enhanced Conversions enabled on tag: {tag['name']}")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


# ============================================================================
# VARIABLE COMMANDS
# ============================================================================

@cli.command('list-variables')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list_variables_cmd(account_id, container_id, output_json):
    """List all variables in container"""
    try:
        client = GTMClient()
        var_mgr = VariableManager(client)

        variables = var_mgr.list_variables(account_id, container_id)

        if output_json:
            click.echo(json.dumps(variables, indent=2))
        else:
            click.echo(f"\nFound {len(variables)} variables:\n")
            click.echo(f"{'ID':<10} {'Name':<40} {'Type':<25}")
            click.echo("-" * 80)
            for var in variables:
                click.echo(f"{var['variableId']:<10} {var['name']:<40} {var['type']:<25}")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('create-variable')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--name', required=True, help='Variable name')
@click.option('--datalayer-name', required=True, help='DataLayer variable name')
@click.option('--default', 'default_value', help='Default value')
@click.option('--folder-id', help='Folder ID')
def create_variable_cmd(account_id, container_id, name, datalayer_name, default_value, folder_id):
    """Create a Data Layer variable"""
    try:
        client = GTMClient()
        var_mgr = VariableManager(client)

        click.echo(f"Creating variable '{name}'...")
        variable = var_mgr.create_data_layer_variable(
            account_id, container_id, name, datalayer_name,
            default_value=default_value, folder_id=folder_id
        )

        click.echo(f"Created variable: {variable['name']} (ID: {variable['variableId']})")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('create-ec-variable')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--name', default='User-Provided Data', help='Variable name')
@click.option('--manual', is_flag=True, help='Use manual GTM variable references')
@click.option('--email-var', help='For manual mode: GTM variable for email (e.g., "{{DLV - email}}")')
@click.option('--phone-var', help='For manual mode: GTM variable for phone')
@click.option('--first-name-var', help='For manual mode: GTM variable for first name')
@click.option('--last-name-var', help='For manual mode: GTM variable for last name')
@click.option('--folder-id', help='Folder ID')
@click.option('--dry-run', is_flag=True, help='Preview what would be created without creating')
def create_ec_variable_cmd(account_id, container_id, name, manual, email_var, phone_var,
                          first_name_var, last_name_var, folder_id, dry_run):
    """Create User-Provided Data variable for Enhanced Conversions.

    Creates a variable of type 'awec' (Google Ads Web Enhanced Conversions) that
    can be used with Google Ads conversion tags to pass user data for better
    attribution matching.

    \b
    Mode options:
      AUTO (default):   Google automatically detects form fields
                        Recommended for standard HTML forms
      MANUAL (--manual): You specify GTM variable references for each field
                        Use when data comes from dataLayer or custom sources

    \b
    Examples:
      # Create AUTO mode variable (recommended for standard forms)
      xw gtm create-ec-variable --name "User-Provided Data"

      # Create MANUAL mode with dataLayer variable references
      xw gtm create-ec-variable --name "EC - Custom Data" --manual \\
        --email-var "{{DLV - enhanced_conversion_data.email}}" \\
        --phone-var "{{DLV - enhanced_conversion_data.phone_number}}"

      # Preview what would be created
      xw gtm create-ec-variable --name "Test EC" --dry-run
    """
    try:
        if dry_run:
            mode = "MANUAL" if manual else "AUTO"
            click.echo("")
            click.echo("Dry-run: Would create User-Provided Data variable:")
            click.echo(f"  Name: {name}")
            click.echo(f"  Type: awec (Google Ads Web Enhanced Conversions)")
            click.echo(f"  Mode: {mode}")

            if manual:
                click.echo("  Field mappings:")
                if email_var:
                    click.echo(f"    email: {email_var}")
                if phone_var:
                    click.echo(f"    phoneNumber: {phone_var}")
                if first_name_var:
                    click.echo(f"    firstName: {first_name_var}")
                if last_name_var:
                    click.echo(f"    lastName: {last_name_var}")
                if not any([email_var, phone_var, first_name_var, last_name_var]):
                    click.echo("    (no field mappings specified)")
            else:
                click.echo("  Parameters:")
                click.echo("    autoPhoneEnabled: true")
                click.echo("    autoAddressEnabled: true")
                click.echo("    autoEmailEnabled: true")

            if folder_id:
                click.echo(f"  Folder ID: {folder_id}")
            click.echo("")
            click.echo("Run without --dry-run to create.")
            return

        client = GTMClient()
        var_mgr = VariableManager(client)

        click.echo(f"Creating Enhanced Conversions variable '{name}'...")
        variable = var_mgr.create_user_data_variable(
            account_id, container_id, name,
            auto_mode=not manual,
            folder_id=folder_id,
            email_var=email_var,
            phone_var=phone_var,
            first_name_var=first_name_var,
            last_name_var=last_name_var
        )

        mode = "MANUAL (GTM variable references)" if manual else "AUTO (auto-detect)"
        click.echo(f"Created variable: {variable['name']} (ID: {variable['variableId']})")
        click.echo(f"Mode: {mode}")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


# ============================================================================
# TRIGGER COMMANDS
# ============================================================================

@cli.command('list-triggers')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list_triggers_cmd(account_id, container_id, output_json):
    """List all triggers in container"""
    try:
        client = GTMClient()
        trigger_mgr = TriggerManager(client)

        triggers = trigger_mgr.list_triggers(account_id, container_id)

        if output_json:
            click.echo(json.dumps(triggers, indent=2))
        else:
            click.echo(f"\nFound {len(triggers)} triggers:\n")
            click.echo(f"{'ID':<10} {'Name':<40} {'Type':<20}")
            click.echo("-" * 75)
            for trigger in triggers:
                click.echo(f"{trigger['triggerId']:<10} {trigger['name']:<40} {trigger['type']:<20}")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('create-trigger')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--name', required=True, help='Trigger name')
@click.option('--event', required=True, help='Event name or regex pattern')
@click.option('--regex', is_flag=True, help='Use regex matching')
@click.option('--folder-id', help='Folder ID')
def create_trigger_cmd(account_id, container_id, name, event, regex, folder_id):
    """Create a custom event trigger"""
    try:
        client = GTMClient()
        trigger_mgr = TriggerManager(client)

        click.echo(f"Creating trigger '{name}'...")
        trigger = trigger_mgr.create_custom_event_trigger(
            account_id, container_id, name, event,
            use_regex=regex, folder_id=folder_id
        )

        click.echo(f"Created trigger: {trigger['name']} (ID: {trigger['triggerId']})")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


# ============================================================================
# AUTH COMMANDS
# ============================================================================

@cli.command('auth-setup')
@click.option('--show-url', is_flag=True, help='Only show authorization URL')
@click.option('--code', help='Authorization code from OAuth flow')
@click.option('--client-id', envvar='GTM_CLIENT_ID', help='OAuth Client ID (or set GTM_CLIENT_ID env var)')
@click.option('--client-secret', envvar='GTM_CLIENT_SECRET', help='OAuth Client Secret (or set GTM_CLIENT_SECRET env var)')
def auth_setup_cmd(show_url, code, client_id, client_secret):
    """Set up GTM OAuth credentials with edit scopes.

    Requires OAuth Client ID and Secret. Set via:
      - Command line: --client-id and --client-secret
      - Environment: GTM_CLIENT_ID and GTM_CLIENT_SECRET
      - Credentials file: ~/.xwander-google/oauth-clients.json

    To create OAuth credentials:
    1. Go to Google Cloud Console > APIs & Services > Credentials
    2. Create OAuth 2.0 Client ID (Desktop app)
    3. Enable Tag Manager API
    """
    import urllib.parse
    import urllib.request
    import os

    # OAuth2 configuration - load from args, env vars, or credentials file
    if not client_id or not client_secret:
        # Try loading from credentials file
        creds_file = os.path.expanduser("~/.xwander-google/oauth-clients.json")
        if os.path.exists(creds_file):
            try:
                import json
                with open(creds_file) as f:
                    oauth_creds = json.load(f)
                if 'gtm' in oauth_creds:
                    client_id = client_id or oauth_creds['gtm'].get('client_id')
                    client_secret = client_secret or oauth_creds['gtm'].get('client_secret')
            except Exception:
                pass

    if not client_id or not client_secret:
        click.echo("Error: OAuth credentials required.", err=True)
        click.echo("")
        click.echo("Provide credentials via:")
        click.echo("  1. Command line: --client-id 'xxx' --client-secret 'xxx'")
        click.echo("  2. Environment: export GTM_CLIENT_ID='xxx' GTM_CLIENT_SECRET='xxx'")
        click.echo("  3. Credentials file: ~/.xwander-google/oauth-clients.json")
        click.echo("")
        click.echo("To create OAuth credentials:")
        click.echo("  1. Go to Google Cloud Console > APIs & Services > Credentials")
        click.echo("  2. Create OAuth 2.0 Client ID (Desktop app)")
        click.echo("  3. Enable Tag Manager API")
        sys.exit(1)

    CLIENT_ID = client_id
    CLIENT_SECRET = client_secret
    REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    AUTH_URL = "https://accounts.google.com/o/oauth2/auth"

    # Required GTM scopes for workspace operations
    SCOPES = [
        "https://www.googleapis.com/auth/tagmanager.readonly",
        "https://www.googleapis.com/auth/tagmanager.edit.containers",
        "https://www.googleapis.com/auth/tagmanager.edit.containerversions",
        "https://www.googleapis.com/auth/tagmanager.publish"
    ]

    if code:
        # Exchange authorization code for tokens
        click.echo("Exchanging authorization code for tokens...")

        data = urllib.parse.urlencode({
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI
        }).encode()

        try:
            req = urllib.request.Request(TOKEN_URL, data=data)
            response = urllib.request.urlopen(req)
            tokens = json.loads(response.read().decode())

            if 'refresh_token' not in tokens:
                click.echo("Error: No refresh token received.", err=True)
                click.echo("Make sure you used the authorization URL with prompt=consent", err=True)
                sys.exit(1)

            # Update credentials file
            import os
            creds_path = os.path.expanduser("~/.xwander-google/credentials.json")

            if os.path.exists(creds_path):
                with open(creds_path, 'r') as f:
                    creds = json.load(f)
            else:
                os.makedirs(os.path.dirname(creds_path), exist_ok=True)
                creds = {"format_version": "1.0", "apis": {}}

            # Update GTM section
            creds['apis']['gtm'] = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'refresh_token': tokens['refresh_token'],
                'scopes': SCOPES
            }
            creds['updated_at'] = __import__('datetime').datetime.now().isoformat()

            with open(creds_path, 'w') as f:
                json.dump(creds, f, indent=2)
            os.chmod(creds_path, 0o600)

            click.echo("")
            click.echo("GTM credentials saved successfully!")
            click.echo(f"  Location: {creds_path}")
            click.echo("")
            click.echo("You can now use GTM commands like:")
            click.echo("  xw gtm workspace-status")
            click.echo("  xw gtm list-tags")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            click.echo(f"Error exchanging code: {error_body}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    else:
        # Generate authorization URL
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'scope': ' '.join(SCOPES),
            'redirect_uri': REDIRECT_URI,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        query_string = urllib.parse.urlencode(params)
        auth_url = f"{AUTH_URL}?{query_string}"

        click.echo("")
        click.echo("GTM OAuth Setup")
        click.echo("=" * 60)
        click.echo("")
        click.echo("Step 1: Visit this URL to authorize GTM access:")
        click.echo("")
        click.echo(auth_url)
        click.echo("")
        click.echo("Step 2: After granting access, copy the authorization code")
        click.echo("")
        click.echo("Step 3: Run this command with the code:")
        click.echo('  xw gtm auth-setup --code "YOUR_CODE_HERE"')
        click.echo("")
        click.echo("Required scopes:")
        for scope in SCOPES:
            click.echo(f"  - {scope.split('/')[-1]}")


@cli.command('auth-test')
def auth_test_cmd():
    """Test GTM authentication"""
    try:
        click.echo("Testing GTM authentication...")
        client = GTMClient()

        # List accounts to verify auth
        accounts = client.service.accounts().list().execute()
        account_list = accounts.get('account', [])

        click.echo("")
        click.echo("Authentication successful!")
        click.echo(f"Found {len(account_list)} GTM account(s):")
        for acc in account_list:
            click.echo(f"  - {acc.get('name', 'unnamed')} (ID: {acc['accountId']})")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)
    except Exception as e:
        click.echo(f"Authentication failed: {e}", err=True)
        sys.exit(1)


# ============================================================================
# WORKSPACE & VERSION COMMANDS
# ============================================================================

@cli.command('workspace-status')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--workspace-id', help='Workspace ID (auto-detected if not specified)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def workspace_status_cmd(account_id, container_id, workspace_id, output_json):
    """Show workspace status with pending changes"""
    try:
        client = GTMClient()

        # Get workspace ID if not specified
        if not workspace_id:
            workspace_id = client.get_workspace_id(account_id, container_id)

        workspace_path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"

        # Get workspace details
        workspace = client.service.accounts().containers().workspaces().get(
            path=workspace_path
        ).execute()

        # Get workspace status (pending changes)
        status = client.service.accounts().containers().workspaces().getStatus(
            path=workspace_path
        ).execute()

        # Parse changes
        workspace_changes = status.get('workspaceChange', [])
        merge_conflicts = status.get('mergeConflict', [])

        # Categorize changes
        added = []
        updated = []
        deleted = []

        for change in workspace_changes:
            change_status = change.get('changeStatus', 'unknown')
            # Determine entity type and name
            entity = None
            entity_type = None
            for key in ['tag', 'trigger', 'variable', 'folder', 'builtInVariable']:
                if key in change:
                    entity = change[key]
                    entity_type = key
                    break

            if entity:
                item = {
                    'type': entity_type,
                    'name': entity.get('name', 'unnamed'),
                    'id': entity.get(f'{entity_type}Id', 'N/A')
                }
                if change_status == 'added':
                    added.append(item)
                elif change_status == 'deleted':
                    deleted.append(item)
                else:  # updated, none, etc.
                    updated.append(item)

        if output_json:
            result = {
                'workspace': {
                    'id': workspace_id,
                    'name': workspace.get('name', 'Default Workspace'),
                    'description': workspace.get('description', '')
                },
                'changes': {
                    'total': len(workspace_changes),
                    'added': added,
                    'updated': updated,
                    'deleted': deleted
                },
                'conflicts': len(merge_conflicts)
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"\nWorkspace: {workspace.get('name', 'Default Workspace')}")
            click.echo(f"Workspace ID: {workspace_id}")
            click.echo(f"Account ID: {account_id}")
            click.echo(f"Container ID: {container_id}")
            click.echo("")

            total_changes = len(workspace_changes)
            if total_changes == 0:
                click.echo("Status: No pending changes")
            else:
                click.echo(f"Status: {total_changes} pending change(s)")
                click.echo("")

                if added:
                    click.echo(f"  Added ({len(added)}):")
                    for item in added:
                        click.echo(f"    + [{item['type']}] {item['name']} (ID: {item['id']})")

                if updated:
                    click.echo(f"  Modified ({len(updated)}):")
                    for item in updated:
                        click.echo(f"    ~ [{item['type']}] {item['name']} (ID: {item['id']})")

                if deleted:
                    click.echo(f"  Deleted ({len(deleted)}):")
                    for item in deleted:
                        click.echo(f"    - [{item['type']}] {item['name']} (ID: {item['id']})")

            if merge_conflicts:
                click.echo(f"\nWarning: {len(merge_conflicts)} merge conflict(s) detected")
                click.echo("  Run 'xw gtm sync-workspace' to resolve conflicts")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command('sync-workspace')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
def sync_workspace_cmd(account_id, container_id):
    """Sync workspace before version creation"""
    try:
        client = GTMClient()
        workspace_mgr = WorkspaceManager(client)

        click.echo("Syncing workspace...")
        result = workspace_mgr.sync(account_id, container_id)

        if result.get('mergeConflict'):
            click.echo(f"Resolved {len(result['mergeConflict'])} merge conflict(s)")

        click.echo("Workspace synced successfully")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('validate-workspace')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--workspace-id', help='Workspace ID (auto-detected if not specified)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def validate_workspace_cmd(account_id, container_id, workspace_id, output_json):
    """Validate workspace configuration before version creation.

    Checks for common issues that cause GTM compiler errors:
      - Variable type requirements (e.g., 'awec' needs 'mode' parameter)
      - Undefined variable references in tags/triggers
      - Invalid trigger references in tags
      - Missing required tag parameters

    Use this before create-version to catch issues early.
    """
    try:
        client = GTMClient()
        workspace_mgr = WorkspaceManager(client)

        click.echo("Validating workspace...")
        is_valid, issues = workspace_mgr.validate_workspace(account_id, container_id, workspace_id)

        if output_json:
            click.echo(json.dumps({
                'is_valid': is_valid,
                'issues': issues
            }, indent=2))
        else:
            errors = [i for i in issues if i['type'] == 'error']
            warnings = [i for i in issues if i['type'] == 'warning']

            if not issues:
                click.echo("Validation passed - no issues found")
            else:
                click.echo("")

                if errors:
                    click.echo(f"Errors ({len(errors)}):")
                    for e in errors:
                        click.echo(f"  [ERROR] {e['resource_type'].title()} {e['resource_id']} ({e['resource_name']})")
                        click.echo(f"          {e['message']}")

                if warnings:
                    click.echo(f"\nWarnings ({len(warnings)}):")
                    for w in warnings:
                        click.echo(f"  [WARN]  {w['resource_type'].title()} {w['resource_id']} ({w['resource_name']})")
                        click.echo(f"          {w['message']}")

                click.echo("")
                if is_valid:
                    click.echo("Validation passed with warnings")
                else:
                    click.echo("Validation failed - fix errors before creating version")
                    sys.exit(1)

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('create-version')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--name', required=True, help='Version name')
@click.option('--notes', default='', help='Version notes')
@click.option('--dry-run', is_flag=True, help='Preview changes without creating version')
@click.option('--skip-validation', is_flag=True, help='Skip workspace validation (not recommended)')
def create_version_cmd(account_id, container_id, name, notes, dry_run, skip_validation):
    """Create a container version from pending workspace changes.

    By default, validates workspace configuration before creating the version.
    This catches common issues like missing variable parameters or undefined
    variable references that would cause GTM compiler errors.

    Use --dry-run to preview pending changes without creating a version.
    """
    try:
        client = GTMClient()
        workspace_mgr = WorkspaceManager(client)

        if dry_run:
            # Get workspace status
            workspace_id = client.get_workspace_id(account_id, container_id)
            workspace_path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"

            status = client.service.accounts().containers().workspaces().getStatus(
                path=workspace_path
            ).execute()

            workspace_changes = status.get('workspaceChange', [])

            click.echo("")
            click.echo(f"Dry-run: Would create version '{name}'")
            click.echo("")

            if not workspace_changes:
                click.echo("No pending changes to include in version.")
                return

            # Categorize changes
            added = []
            updated = []
            deleted = []

            for change in workspace_changes:
                change_status = change.get('changeStatus', 'unknown')
                entity = None
                entity_type = None
                for key in ['tag', 'trigger', 'variable', 'folder', 'builtInVariable']:
                    if key in change:
                        entity = change[key]
                        entity_type = key
                        break

                if entity:
                    item = {
                        'type': entity_type,
                        'name': entity.get('name', 'unnamed'),
                        'id': entity.get(f'{entity_type}Id', 'N/A')
                    }
                    if change_status == 'added':
                        added.append(item)
                    elif change_status == 'deleted':
                        deleted.append(item)
                    else:
                        updated.append(item)

            click.echo(f"Changes to include ({len(workspace_changes)} total):")

            if added:
                click.echo(f"\n  Added ({len(added)}):")
                for item in added:
                    click.echo(f"    + [{item['type']}] {item['name']} (ID: {item['id']})")

            if updated:
                click.echo(f"\n  Modified ({len(updated)}):")
                for item in updated:
                    click.echo(f"    ~ [{item['type']}] {item['name']} (ID: {item['id']})")

            if deleted:
                click.echo(f"\n  Deleted ({len(deleted)}):")
                for item in deleted:
                    click.echo(f"    - [{item['type']}] {item['name']} (ID: {item['id']})")

            # Run validation
            click.echo("\nValidation preview:")
            is_valid, issues = workspace_mgr.validate_workspace(account_id, container_id)
            errors = [i for i in issues if i['type'] == 'error']
            warnings = [i for i in issues if i['type'] == 'warning']

            if errors:
                click.echo(f"  {len(errors)} error(s) - version creation would fail")
                for e in errors:
                    click.echo(f"    [ERROR] {e['resource_type']} {e['resource_id']}: {e['message']}")
            if warnings:
                click.echo(f"  {len(warnings)} warning(s)")
            if not issues:
                click.echo("  No issues found")

            click.echo("")
            if is_valid:
                click.echo("Run without --dry-run to create version.")
            else:
                click.echo("Fix errors before creating version.")
            return

        click.echo(f"Creating version '{name}'...")
        version = workspace_mgr.create_version(
            account_id, container_id, name, notes,
            validate=not skip_validation
        )

        click.echo(f"Version {version['containerVersionId']} created successfully")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('list-versions')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list_versions_cmd(account_id, container_id, output_json):
    """List container versions"""
    try:
        client = GTMClient()
        workspace_mgr = WorkspaceManager(client)

        versions = workspace_mgr.list_versions(account_id, container_id)

        if output_json:
            click.echo(json.dumps(versions, indent=2))
        else:
            click.echo(f"\nFound {len(versions)} versions:\n")
            click.echo(f"{'Version ID':<12} {'Name':<40} {'Deleted'}")
            click.echo("-" * 60)
            for v in sorted(versions, key=lambda x: int(x['containerVersionId']), reverse=True):
                deleted = "Yes" if v.get('deleted') else "No"
                click.echo(f"{v['containerVersionId']:<12} {v.get('name', 'unnamed'):<40} {deleted}")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


@cli.command('publish')
@click.option('--account-id', default=DEFAULT_ACCOUNT_ID, help='GTM account ID')
@click.option('--container-id', default=DEFAULT_CONTAINER_ID, help='GTM container ID')
@click.option('--version-id', help='Version ID to publish')
@click.option('--latest', is_flag=True, help='Publish latest version')
def publish_cmd(account_id, container_id, version_id, latest):
    """Publish a version to LIVE"""
    try:
        client = GTMClient()
        workspace_mgr = WorkspaceManager(client)
        publisher = Publisher(client)

        if latest:
            click.echo("Fetching latest version...")
            version = workspace_mgr.get_latest_version(account_id, container_id)
            version_id = version['containerVersionId']
            click.echo(f"Latest version: {version_id} - {version.get('name', 'unnamed')}")

        if not version_id:
            click.echo("Error: Provide --version-id or --latest", err=True)
            sys.exit(1)

        click.echo(f"Publishing version {version_id}...")
        result = publisher.publish(account_id, container_id, version_id)

        click.echo(f"Version {version_id} published successfully!")

    except GTMError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)


if __name__ == '__main__':
    cli()
