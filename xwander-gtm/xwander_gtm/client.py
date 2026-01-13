"""
GTM API client for xwander-gtm plugin.
Handles authentication and low-level API operations.
"""

import os
import yaml
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .exceptions import (
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    GTMError
)


class GTMClient:
    """Google Tag Manager API client"""

    def __init__(self, credentials_path: str = None):
        """
        Initialize GTM API client.

        Args:
            credentials_path: Path to GTM credentials YAML file (legacy).
                             If None, uses unified xwander-google-auth (recommended).

        Raises:
            AuthenticationError: If credentials are missing or invalid
        """
        if credentials_path:
            # Legacy path for backward compatibility
            self.credentials = self._load_credentials(credentials_path)
            self.service = build('tagmanager', 'v2', credentials=self.credentials)
        else:
            # Use unified xwander-google-auth (recommended)
            try:
                from xwander_google_auth import get_client
                self.service = get_client('gtm')
            except ImportError:
                # Fallback to legacy if xwander-google-auth not installed
                self.credentials = self._load_credentials("~/.gtm-credentials.yaml")
                self.service = build('tagmanager', 'v2', credentials=self.credentials)
            except Exception as e:
                # If unified auth fails, try legacy
                try:
                    self.credentials = self._load_credentials("~/.gtm-credentials.yaml")
                    self.service = build('tagmanager', 'v2', credentials=self.credentials)
                except:
                    raise AuthenticationError(
                        f"Failed to authenticate via unified auth or legacy credentials: {e}",
                        details={"error": str(e)}
                    )

    def _load_credentials(self, creds_path: str) -> Credentials:
        """
        Load OAuth credentials from YAML file.

        Args:
            creds_path: Path to credentials file

        Returns:
            Google OAuth2 credentials

        Raises:
            AuthenticationError: If credentials are missing or invalid
        """
        full_path = os.path.expanduser(creds_path)

        if not os.path.exists(full_path):
            raise AuthenticationError(
                f"Credentials file not found: {full_path}",
                details={"path": full_path}
            )

        try:
            with open(full_path, 'r') as f:
                creds_data = yaml.safe_load(f)
        except Exception as e:
            raise AuthenticationError(
                f"Failed to read credentials file: {e}",
                details={"path": full_path, "error": str(e)}
            )

        # Validate required fields
        required_fields = ['refresh_token', 'token_uri', 'client_id', 'client_secret']
        missing = [f for f in required_fields if f not in creds_data]
        if missing:
            raise AuthenticationError(
                f"Missing required credential fields: {', '.join(missing)}",
                details={"missing_fields": missing}
            )

        # Use all scopes from credentials file
        scopes = creds_data.get('scopes', [
            'https://www.googleapis.com/auth/tagmanager.readonly',
            'https://www.googleapis.com/auth/tagmanager.edit.containers',
            'https://www.googleapis.com/auth/tagmanager.edit.containerversions',
            'https://www.googleapis.com/auth/tagmanager.publish'
        ])

        credentials = Credentials(
            token=creds_data.get('access_token'),  # Will be refreshed if expired
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=scopes
        )

        return credentials

    def handle_http_error(self, error: HttpError, operation: str) -> GTMError:
        """
        Convert HttpError to appropriate GTMError.

        Args:
            error: The HttpError from Google API
            operation: Description of the operation that failed

        Returns:
            Appropriate GTMError subclass
        """
        status = error.resp.status
        error_message = str(error)

        if status == 401 or status == 403:
            if 'quota' in error_message.lower() or 'rate' in error_message.lower():
                return RateLimitError(
                    f"Rate limit exceeded during {operation}",
                    details={"status": status, "error": error_message}
                )
            return AuthenticationError(
                f"Authentication failed during {operation}",
                details={"status": status, "error": error_message}
            )
        elif status == 404:
            return ResourceNotFoundError(
                f"Resource not found during {operation}",
                details={"status": status, "error": error_message}
            )
        elif status == 429:
            return RateLimitError(
                f"Rate limit exceeded during {operation}",
                details={"status": status, "error": error_message}
            )
        else:
            return GTMError(
                f"API error during {operation}: {error_message}",
                details={"status": status, "error": error_message}
            )

    def get_workspace_id(self, account_id: str, container_id: str,
                        workspace_name: str = "Default Workspace") -> str:
        """
        Get workspace ID by name.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_name: Name of workspace (default: "Default Workspace")

        Returns:
            Workspace ID

        Raises:
            ResourceNotFoundError: If workspace not found
            GTMError: If API call fails
        """
        try:
            parent = f"accounts/{account_id}/containers/{container_id}"
            response = self.service.accounts().containers().workspaces().list(
                parent=parent
            ).execute()

            # Find workspace by name
            for ws in response.get('workspace', []):
                if ws.get('name') == workspace_name:
                    return ws['workspaceId']

            # If named workspace not found, return first workspace
            if response.get('workspace'):
                return response['workspace'][0]['workspaceId']

            raise ResourceNotFoundError(
                f"No workspaces found in container {container_id}",
                details={"account_id": account_id, "container_id": container_id}
            )

        except HttpError as e:
            raise self.handle_http_error(e, "get workspace")

    def list_resources(self, resource_type: str, account_id: str,
                      container_id: str, workspace_id: Optional[str] = None) -> list:
        """
        List GTM resources (tags, triggers, variables, folders).

        Args:
            resource_type: Type of resource ('tags', 'triggers', 'variables', 'folders')
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            List of resources

        Raises:
            GTMError: If API call fails
        """
        if not workspace_id:
            workspace_id = self.get_workspace_id(account_id, container_id)

        try:
            parent = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"

            # Get the appropriate service method
            service_map = {
                'tags': self.service.accounts().containers().workspaces().tags(),
                'triggers': self.service.accounts().containers().workspaces().triggers(),
                'variables': self.service.accounts().containers().workspaces().variables(),
                'folders': self.service.accounts().containers().workspaces().folders()
            }

            if resource_type not in service_map:
                raise GTMError(
                    f"Invalid resource type: {resource_type}",
                    details={"valid_types": list(service_map.keys())}
                )

            response = service_map[resource_type].list(parent=parent).execute()

            # API returns resource_type as the key (e.g., 'tag', 'trigger')
            singular = resource_type.rstrip('s')  # Simple singularization
            return response.get(singular, [])

        except HttpError as e:
            raise self.handle_http_error(e, f"list {resource_type}")

    def get_resource(self, resource_type: str, account_id: str, container_id: str,
                    resource_id: str, workspace_id: Optional[str] = None) -> Dict:
        """
        Get a specific GTM resource.

        Args:
            resource_type: Type of resource ('tags', 'triggers', 'variables', 'folders')
            account_id: GTM account ID
            container_id: GTM container ID
            resource_id: Resource ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Resource object

        Raises:
            ResourceNotFoundError: If resource not found
            GTMError: If API call fails
        """
        if not workspace_id:
            workspace_id = self.get_workspace_id(account_id, container_id)

        try:
            path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/{resource_type}/{resource_id}"

            service_map = {
                'tags': self.service.accounts().containers().workspaces().tags(),
                'triggers': self.service.accounts().containers().workspaces().triggers(),
                'variables': self.service.accounts().containers().workspaces().variables(),
                'folders': self.service.accounts().containers().workspaces().folders()
            }

            if resource_type not in service_map:
                raise GTMError(
                    f"Invalid resource type: {resource_type}",
                    details={"valid_types": list(service_map.keys())}
                )

            return service_map[resource_type].get(path=path).execute()

        except HttpError as e:
            raise self.handle_http_error(e, f"get {resource_type[:-1]} {resource_id}")

    def create_resource(self, resource_type: str, account_id: str, container_id: str,
                       body: Dict, workspace_id: Optional[str] = None) -> Dict:
        """
        Create a GTM resource.

        Args:
            resource_type: Type of resource ('tags', 'triggers', 'variables', 'folders')
            account_id: GTM account ID
            container_id: GTM container ID
            body: Resource configuration
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Created resource

        Raises:
            GTMError: If API call fails
        """
        if not workspace_id:
            workspace_id = self.get_workspace_id(account_id, container_id)

        try:
            parent = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"

            service_map = {
                'tags': self.service.accounts().containers().workspaces().tags(),
                'triggers': self.service.accounts().containers().workspaces().triggers(),
                'variables': self.service.accounts().containers().workspaces().variables(),
                'folders': self.service.accounts().containers().workspaces().folders()
            }

            if resource_type not in service_map:
                raise GTMError(
                    f"Invalid resource type: {resource_type}",
                    details={"valid_types": list(service_map.keys())}
                )

            return service_map[resource_type].create(parent=parent, body=body).execute()

        except HttpError as e:
            raise self.handle_http_error(e, f"create {resource_type[:-1]}")

    def update_resource(self, resource_type: str, account_id: str, container_id: str,
                       resource_id: str, body: Dict, workspace_id: Optional[str] = None) -> Dict:
        """
        Update a GTM resource.

        Args:
            resource_type: Type of resource ('tags', 'triggers', 'variables', 'folders')
            account_id: GTM account ID
            container_id: GTM container ID
            resource_id: Resource ID
            body: Updated resource configuration
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Updated resource

        Raises:
            GTMError: If API call fails
        """
        if not workspace_id:
            workspace_id = self.get_workspace_id(account_id, container_id)

        try:
            path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/{resource_type}/{resource_id}"
            fingerprint = body.get('fingerprint')

            service_map = {
                'tags': self.service.accounts().containers().workspaces().tags(),
                'triggers': self.service.accounts().containers().workspaces().triggers(),
                'variables': self.service.accounts().containers().workspaces().variables(),
                'folders': self.service.accounts().containers().workspaces().folders()
            }

            if resource_type not in service_map:
                raise GTMError(
                    f"Invalid resource type: {resource_type}",
                    details={"valid_types": list(service_map.keys())}
                )

            return service_map[resource_type].update(
                path=path,
                fingerprint=fingerprint,
                body=body
            ).execute()

        except HttpError as e:
            raise self.handle_http_error(e, f"update {resource_type[:-1]} {resource_id}")

    def delete_resource(self, resource_type: str, account_id: str, container_id: str,
                       resource_id: str, workspace_id: Optional[str] = None) -> None:
        """
        Delete a GTM resource.

        Args:
            resource_type: Type of resource ('tags', 'triggers', 'variables', 'folders')
            account_id: GTM account ID
            container_id: GTM container ID
            resource_id: Resource ID
            workspace_id: Workspace ID (auto-detected if None)

        Raises:
            GTMError: If API call fails
        """
        if not workspace_id:
            workspace_id = self.get_workspace_id(account_id, container_id)

        try:
            path = f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/{resource_type}/{resource_id}"

            service_map = {
                'tags': self.service.accounts().containers().workspaces().tags(),
                'triggers': self.service.accounts().containers().workspaces().triggers(),
                'variables': self.service.accounts().containers().workspaces().variables(),
                'folders': self.service.accounts().containers().workspaces().folders()
            }

            if resource_type not in service_map:
                raise GTMError(
                    f"Invalid resource type: {resource_type}",
                    details={"valid_types": list(service_map.keys())}
                )

            service_map[resource_type].delete(path=path).execute()

        except HttpError as e:
            raise self.handle_http_error(e, f"delete {resource_type[:-1]} {resource_id}")

    # Convenience methods for common operations
    def list_tags(self, account_id: str, container_id: str,
                  workspace_id: Optional[str] = None) -> list:
        """
        List all tags in a container.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            List of tags
        """
        return self.list_resources('tags', account_id, container_id, workspace_id)

    def list_triggers(self, account_id: str, container_id: str,
                      workspace_id: Optional[str] = None) -> list:
        """
        List all triggers in a container.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            List of triggers
        """
        return self.list_resources('triggers', account_id, container_id, workspace_id)

    def list_variables(self, account_id: str, container_id: str,
                       workspace_id: Optional[str] = None) -> list:
        """
        List all variables in a container.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            List of variables
        """
        return self.list_resources('variables', account_id, container_id, workspace_id)
