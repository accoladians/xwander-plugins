"""
GTM workspace management operations.
"""

import re
from typing import Dict, List, Optional, Tuple
from googleapiclient.errors import HttpError

from .client import GTMClient
from .exceptions import WorkspaceConflictError, GTMError, ValidationError

# GTM built-in variables that don't need to be defined in workspace
GTM_BUILTIN_VARIABLES = {
    # Click variables
    'Click URL', 'Click Text', 'Click Element', 'Click ID', 'Click Classes', 'Click Target',
    # Page variables
    'Page URL', 'Page Path', 'Page Hostname', 'Referrer', 'Page Title',
    # Event variables
    'Event',
    # Form variables
    'Form ID', 'Form Classes', 'Form Target', 'Form Text', 'Form URL', 'Form Element',
    # Container/Environment variables
    'Container ID', 'Container Version', 'Environment Name', 'Debug Mode', 'Random Number',
    # Visibility/Scroll variables
    'Scroll Depth Threshold', 'Scroll Depth Units', 'Scroll Direction', 'Percent Visible',
    # Video variables
    'Video Status', 'Video Title', 'Video Percent', 'Video Current Time', 'Video Duration', 'Video URL', 'Video Provider',
    # History variables
    'New History Fragment', 'Old History Fragment', 'New History State', 'Old History State', 'History Source',
    # Error variables
    'Error Message', 'Error URL', 'Error Line',
    # Element visibility variables
    'Element ID', 'Element Classes', 'Element Target', 'Element URL',
}


class WorkspaceManager:
    """Manage GTM workspaces"""

    def __init__(self, client: GTMClient):
        """
        Initialize workspace manager.

        Args:
            client: GTMClient instance
        """
        self.client = client

    def sync(self, account_id: str, container_id: str,
            workspace_id: Optional[str] = None) -> Dict:
        """
        Sync workspace before version creation.

        This is CRITICAL for proper version persistence. Without syncing,
        versions may appear to be created but are not actually persisted.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Sync response with potential mergeConflict field

        Raises:
            WorkspaceConflictError: If sync has unresolvable conflicts
            GTMError: If sync fails
        """
        if not workspace_id:
            workspace_id = self.client.get_workspace_id(account_id, container_id)

        workspace_path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"

        try:
            sync_response = self.client.service.accounts().containers().workspaces().sync(
                path=workspace_path
            ).execute()

            # Handle merge conflicts by keeping workspace version
            if sync_response.get('mergeConflict'):
                conflicts = sync_response['mergeConflict']
                print(f"  Resolving {len(conflicts)} merge conflict(s)...")

                for conflict in conflicts:
                    entity = conflict.get('entityInWorkspace', {})

                    # Resolve by keeping workspace version
                    if entity.get('tag'):
                        self.client.service.accounts().containers().workspaces().resolve_conflict(
                            path=workspace_path,
                            body={'tag': entity.get('tag')},
                            fingerprint=entity.get('fingerprint')
                        ).execute()
                    elif entity.get('trigger'):
                        self.client.service.accounts().containers().workspaces().resolve_conflict(
                            path=workspace_path,
                            body={'trigger': entity.get('trigger')},
                            fingerprint=entity.get('fingerprint')
                        ).execute()
                    elif entity.get('variable'):
                        self.client.service.accounts().containers().workspaces().resolve_conflict(
                            path=workspace_path,
                            body={'variable': entity.get('variable')},
                            fingerprint=entity.get('fingerprint')
                        ).execute()

            return sync_response

        except HttpError as e:
            raise self.client.handle_http_error(e, "sync workspace")

    def validate_workspace(self, account_id: str, container_id: str,
                          workspace_id: Optional[str] = None,
                          strict: bool = False) -> Tuple[bool, List[Dict]]:
        """
        Validate workspace configuration before version creation.

        Checks for common issues that cause GTM compiler errors:
        1. Variable type requirements (e.g., 'awec' needs 'mode' parameter)
        2. Undefined variable references in tags/triggers
        3. Invalid trigger references in tags
        4. Missing required tag parameters

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)
            strict: If True, raise ValidationError on any issue; otherwise return issues

        Returns:
            Tuple of (is_valid, list of issues)
            Each issue is a dict with: type, resource_type, resource_id, resource_name, message

        Raises:
            ValidationError: If strict=True and validation fails
            GTMError: If API calls fail
        """
        if not workspace_id:
            workspace_id = self.client.get_workspace_id(account_id, container_id)

        issues = []

        # Load all resources
        variables = self.client.list_resources('variables', account_id, container_id, workspace_id)
        triggers = self.client.list_resources('triggers', account_id, container_id, workspace_id)
        tags = self.client.list_resources('tags', account_id, container_id, workspace_id)

        # Build lookup tables
        variable_names = {v['name']: v for v in variables}
        variable_ids = {v['variableId']: v for v in variables}
        trigger_ids = {t['triggerId']: t for t in triggers}

        # === Validate Variables ===
        for var in variables:
            var_id = var.get('variableId')
            var_name = var.get('name', 'Unknown')
            var_type = var.get('type')
            params = var.get('parameter', [])
            # Create a set of parameter keys for quick lookup (e.g., 'mode', 'email', 'phone')
            param_keys = {p.get('key') for p in params}

            # Check awec (Enhanced Conversions) variable requirements
            # awec = Google Ads Web Enhanced Conversions variable type
            # MUST have 'mode' parameter set to either 'AUTO' or 'MANUAL'
            if var_type == 'awec':
                if 'mode' not in param_keys:
                    issues.append({
                        'type': 'error',
                        'resource_type': 'variable',
                        'resource_id': var_id,
                        'resource_name': var_name,
                        'message': f"User-Provided Data variable missing required 'mode' parameter (AUTO or MANUAL)"
                    })

            # Check gtes type - this is usually wrong for EC
            # gtes = Google Tag Services (deprecated for EC, causes compiler errors)
            # Common mistake: using 'gtes' instead of 'awec' for Enhanced Conversions
            if var_type == 'gtes':
                issues.append({
                    'type': 'warning',
                    'resource_type': 'variable',
                    'resource_id': var_id,
                    'resource_name': var_name,
                    'message': f"Variable uses type 'gtes' - for Enhanced Conversions use type 'awec' instead"
                })

        # === Validate Triggers ===
        for trigger in triggers:
            trig_id = trigger.get('triggerId')
            trig_name = trigger.get('name', 'Unknown')

            # Check variable references in trigger conditions
            # Triggers can reference variables in their filter conditions (e.g., {{Page URL}} equals "...")
            # We need to verify all {{Variable Name}} references resolve to actual variables
            for condition in trigger.get('filter', []) + trigger.get('customEventFilter', []):
                for param in condition.get('parameter', []):
                    # arg0 is typically the variable reference in condition comparisons
                    if param.get('key') == 'arg0':
                        value = param.get('value', '')
                        # Extract all {{Variable Name}} patterns using regex
                        var_refs = re.findall(r'\{\{([^}]+)\}\}', value)
                        for ref in var_refs:
                            # Skip built-in variables (prefixed with _) and check if variable exists
                            if ref not in variable_names and not ref.startswith('_'):
                                issues.append({
                                    'type': 'error',
                                    'resource_type': 'trigger',
                                    'resource_id': trig_id,
                                    'resource_name': trig_name,
                                    'message': f"References undefined variable '{{{{{ref}}}}}'"
                                })

        # === Validate Tags ===
        for tag in tags:
            tag_id = tag.get('tagId')
            tag_name = tag.get('name', 'Unknown')
            tag_type = tag.get('type')
            params = tag.get('parameter', [])

            # Check trigger references
            for firing_trigger_id in tag.get('firingTriggerId', []):
                if firing_trigger_id not in trigger_ids:
                    issues.append({
                        'type': 'error',
                        'resource_type': 'tag',
                        'resource_id': tag_id,
                        'resource_name': tag_name,
                        'message': f"References undefined trigger ID {firing_trigger_id}"
                    })

            # Check variable references in parameters
            # Tags often reference variables in their config (e.g., conversionValue: {{Order Total}})
            for param in params:
                value = str(param.get('value', ''))
                # Extract all {{Variable Name}} patterns
                var_refs = re.findall(r'\{\{([^}]+)\}\}', value)
                for ref in var_refs:
                    # Skip built-in variables (prefixed with _ like {{_event}} or in GTM_BUILTIN_VARIABLES list)
                    if ref.startswith('_') or ref in GTM_BUILTIN_VARIABLES:
                        continue
                    if ref not in variable_names:
                        issues.append({
                            'type': 'error',
                            'resource_type': 'tag',
                            'resource_id': tag_id,
                            'resource_name': tag_name,
                            'message': f"References undefined variable '{{{{{ref}}}}}'"
                        })

            # Check awct (conversion) tag requirements
            if tag_type == 'awct':
                param_keys = {p.get('key') for p in params}
                if 'conversionId' not in param_keys:
                    issues.append({
                        'type': 'error',
                        'resource_type': 'tag',
                        'resource_id': tag_id,
                        'resource_name': tag_name,
                        'message': "Conversion tag missing required 'conversionId' parameter"
                    })
                if 'conversionLabel' not in param_keys:
                    issues.append({
                        'type': 'error',
                        'resource_type': 'tag',
                        'resource_id': tag_id,
                        'resource_name': tag_name,
                        'message': "Conversion tag missing required 'conversionLabel' parameter"
                    })

        # Summarize results
        is_valid = not any(i['type'] == 'error' for i in issues)

        if strict and not is_valid:
            error_messages = [f"  - {i['resource_type'].title()} {i['resource_id']} ({i['resource_name']}): {i['message']}"
                           for i in issues if i['type'] == 'error']
            raise ValidationError(
                f"Workspace validation failed with {len(error_messages)} error(s):\n" + "\n".join(error_messages),
                details={"issues": issues}
            )

        return is_valid, issues

    def create_version(self, account_id: str, container_id: str,
                      version_name: str, notes: str = "",
                      workspace_id: Optional[str] = None,
                      auto_sync: bool = True,
                      validate: bool = True) -> Dict:
        """
        Create a version from workspace changes.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            version_name: Version name
            notes: Version notes
            workspace_id: Workspace ID (auto-detected if None)
            auto_sync: Auto-sync before creating version (recommended)
            validate: Validate workspace before version creation (recommended)

        Returns:
            containerVersion object

        Raises:
            ValidationError: If validation fails (when validate=True)
            GTMError: If version creation fails
            WorkspaceConflictError: If workspace has conflicts
        """
        if not workspace_id:
            workspace_id = self.client.get_workspace_id(account_id, container_id)

        workspace_path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
        container_path = f"accounts/{account_id}/containers/{container_id}"

        # Step 0: Validate workspace if validation enabled
        if validate:
            print(f"  Validating workspace {workspace_id}...")
            is_valid, issues = self.validate_workspace(account_id, container_id, workspace_id)

            # Show warnings
            warnings = [i for i in issues if i['type'] == 'warning']
            for w in warnings:
                print(f"  Warning: {w['resource_type'].title()} {w['resource_id']} ({w['resource_name']}): {w['message']}")

            # Fail on errors
            errors = [i for i in issues if i['type'] == 'error']
            if errors:
                error_messages = [f"  - {e['resource_type'].title()} {e['resource_id']} ({e['resource_name']}): {e['message']}"
                                for e in errors]
                raise ValidationError(
                    f"Version creation blocked - {len(errors)} validation error(s) found:\n" + "\n".join(error_messages),
                    details={"issues": issues}
                )
            print(f"  Validation passed")

        # Step 1: Sync workspace if auto_sync enabled
        if auto_sync:
            print(f"  Syncing workspace {workspace_id}...")
            self.sync(account_id, container_id, workspace_id)

        # Step 2: Create version
        print(f"  Creating version '{version_name}'...")
        try:
            result = self.client.service.accounts().containers().workspaces().create_version(
                path=workspace_path,
                body={
                    'name': version_name,
                    'notes': notes
                }
            ).execute()
        except HttpError as e:
            raise self.client.handle_http_error(e, "create version")

        # Step 3: Check for compiler errors
        if result.get('compilerError'):
            errors = result.get('compilerError', {})
            raise GTMError(
                f"Version creation failed with compiler error: {errors}",
                details={"compiler_error": errors}
            )

        if result.get('syncStatus', {}).get('syncError'):
            error = result['syncStatus']['syncError']
            raise GTMError(
                f"Sync error during version creation: {error}",
                details={"sync_error": error}
            )

        # Step 4: Verify version was actually persisted
        version = result.get('containerVersion')
        if not version:
            raise GTMError("No containerVersion in response")

        created_id = int(version['containerVersionId'])

        # Query all version headers to confirm persistence
        try:
            headers = self.client.service.accounts().containers().version_headers().list(
                parent=container_path
            ).execute()

            version_ids = [
                int(v['containerVersionId'])
                for v in headers.get('containerVersionHeader', [])
            ]

            if created_id not in version_ids:
                raise GTMError(
                    f"Version {created_id} not persisted! "
                    f"Latest version: {max(version_ids) if version_ids else 'none'}",
                    details={
                        "created_id": created_id,
                        "persisted_ids": version_ids
                    }
                )

            print(f"  Version {created_id} created and verified")

        except HttpError as e:
            print(f"  Warning: Could not verify version persistence: {e}")
            # Don't fail if verification fails, but log it

        return version

    def list_versions(self, account_id: str, container_id: str,
                     include_deleted: bool = False) -> list:
        """
        List container versions.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            include_deleted: Include deleted versions

        Returns:
            List of version headers

        Raises:
            GTMError: If API call fails
        """
        try:
            parent = f"accounts/{account_id}/containers/{container_id}"
            response = self.client.service.accounts().containers().version_headers().list(
                parent=parent,
                includeDeleted=include_deleted
            ).execute()

            return response.get('containerVersionHeader', [])

        except HttpError as e:
            raise self.client.handle_http_error(e, "list versions")

    def get_version(self, account_id: str, container_id: str,
                   version_id: str) -> Dict:
        """
        Get a specific version.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            version_id: Version ID

        Returns:
            containerVersion object

        Raises:
            GTMError: If API call fails
        """
        try:
            path = f"accounts/{account_id}/containers/{container_id}/versions/{version_id}"
            return self.client.service.accounts().containers().versions().get(
                path=path
            ).execute()

        except HttpError as e:
            raise self.client.handle_http_error(e, f"get version {version_id}")

    def get_latest_version(self, account_id: str, container_id: str) -> Dict:
        """
        Get the latest container version.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID

        Returns:
            Latest containerVersion object

        Raises:
            GTMError: If no versions found or API call fails
        """
        versions = self.list_versions(account_id, container_id)

        if not versions:
            raise GTMError(
                f"No versions found for container {container_id}",
                details={"account_id": account_id, "container_id": container_id}
            )

        # Sort by version ID (descending) and return the latest
        latest = sorted(versions, key=lambda v: int(v['containerVersionId']), reverse=True)[0]

        # Get full version details
        return self.get_version(account_id, container_id, latest['containerVersionId'])
