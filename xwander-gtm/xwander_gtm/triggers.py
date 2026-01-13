"""
GTM trigger management operations.
"""

from typing import Dict, List, Optional
from .client import GTMClient
from .exceptions import ValidationError, DuplicateResourceError


class TriggerManager:
    """Manage GTM triggers"""

    def __init__(self, client: GTMClient):
        """
        Initialize trigger manager.

        Args:
            client: GTMClient instance
        """
        self.client = client

    def list_triggers(self, account_id: str, container_id: str,
                     workspace_id: Optional[str] = None) -> List[Dict]:
        """
        List all triggers in a container.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            List of triggers

        Raises:
            GTMError: If API call fails
        """
        return self.client.list_resources('triggers', account_id, container_id, workspace_id)

    def get_trigger(self, account_id: str, container_id: str, trigger_id: str,
                   workspace_id: Optional[str] = None) -> Dict:
        """
        Get a specific trigger.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            trigger_id: Trigger ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Trigger object

        Raises:
            ResourceNotFoundError: If trigger not found
            GTMError: If API call fails
        """
        return self.client.get_resource('triggers', account_id, container_id, trigger_id, workspace_id)

    def create_custom_event_trigger(self, account_id: str, container_id: str,
                                    name: str, event_pattern: str,
                                    workspace_id: Optional[str] = None,
                                    folder_id: Optional[str] = None,
                                    use_regex: bool = True) -> Dict:
        """
        Create a custom event trigger.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            name: Trigger name
            event_pattern: Event name or regex pattern
            workspace_id: Workspace ID (auto-detected if None)
            folder_id: Optional folder ID
            use_regex: Use regex matching (default: True)

        Returns:
            Created trigger

        Raises:
            DuplicateResourceError: If trigger name already exists
            GTMError: If API call fails
        """
        trigger_body = {
            'name': name,
            'type': 'customEvent',
            'customEventFilter': [
                {
                    'type': 'MATCH_REGEX' if use_regex else 'EQUALS',
                    'parameter': [
                        {
                            'type': 'TEMPLATE',
                            'key': 'arg0',
                            'value': '{{_event}}'
                        },
                        {
                            'type': 'TEMPLATE',
                            'key': 'arg1',
                            'value': event_pattern
                        }
                    ]
                }
            ]
        }

        if folder_id:
            trigger_body['parentFolderId'] = folder_id

        try:
            return self.client.create_resource('triggers', account_id, container_id, trigger_body, workspace_id)
        except Exception as e:
            error_str = str(e).lower()
            if 'duplicate' in error_str or 'already exists' in error_str:
                raise DuplicateResourceError(
                    f"Trigger '{name}' already exists",
                    details={"name": name}
                )
            raise

    def create_page_view_trigger(self, account_id: str, container_id: str,
                                 name: str, url_pattern: Optional[str] = None,
                                 workspace_id: Optional[str] = None,
                                 folder_id: Optional[str] = None) -> Dict:
        """
        Create a page view trigger.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            name: Trigger name
            url_pattern: Optional URL pattern to match
            workspace_id: Workspace ID (auto-detected if None)
            folder_id: Optional folder ID

        Returns:
            Created trigger

        Raises:
            DuplicateResourceError: If trigger name already exists
            GTMError: If API call fails
        """
        trigger_body = {
            'name': name,
            'type': 'pageview'
        }

        # Add URL filter if provided
        if url_pattern:
            trigger_body['filter'] = [
                {
                    'type': 'MATCH_REGEX',
                    'parameter': [
                        {
                            'type': 'TEMPLATE',
                            'key': 'arg0',
                            'value': '{{Page URL}}'
                        },
                        {
                            'type': 'TEMPLATE',
                            'key': 'arg1',
                            'value': url_pattern
                        }
                    ]
                }
            ]

        if folder_id:
            trigger_body['parentFolderId'] = folder_id

        try:
            return self.client.create_resource('triggers', account_id, container_id, trigger_body, workspace_id)
        except Exception as e:
            error_str = str(e).lower()
            if 'duplicate' in error_str or 'already exists' in error_str:
                raise DuplicateResourceError(
                    f"Trigger '{name}' already exists",
                    details={"name": name}
                )
            raise

    def update_trigger(self, account_id: str, container_id: str, trigger_id: str,
                      updates: Dict, workspace_id: Optional[str] = None) -> Dict:
        """
        Update an existing trigger.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            trigger_id: Trigger ID to update
            updates: Dictionary of fields to update
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Updated trigger

        Raises:
            ResourceNotFoundError: If trigger not found
            GTMError: If API call fails
        """
        # Get current trigger
        trigger = self.get_trigger(account_id, container_id, trigger_id, workspace_id)

        # Apply updates
        for key, value in updates.items():
            trigger[key] = value

        # Update via API
        return self.client.update_resource('triggers', account_id, container_id, trigger_id, trigger, workspace_id)

    def delete_trigger(self, account_id: str, container_id: str, trigger_id: str,
                      workspace_id: Optional[str] = None) -> None:
        """
        Delete a trigger.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            trigger_id: Trigger ID to delete
            workspace_id: Workspace ID (auto-detected if None)

        Raises:
            ResourceNotFoundError: If trigger not found
            GTMError: If API call fails
        """
        self.client.delete_resource('triggers', account_id, container_id, trigger_id, workspace_id)
