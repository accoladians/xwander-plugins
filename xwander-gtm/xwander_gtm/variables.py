"""
GTM variable management operations.
"""

from typing import Dict, List, Optional
from .client import GTMClient
from .exceptions import ValidationError, DuplicateResourceError


class VariableManager:
    """Manage GTM variables"""

    def __init__(self, client: GTMClient):
        """
        Initialize variable manager.

        Args:
            client: GTMClient instance
        """
        self.client = client

    def list_variables(self, account_id: str, container_id: str,
                      workspace_id: Optional[str] = None) -> List[Dict]:
        """
        List all variables in a container.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            List of variables

        Raises:
            GTMError: If API call fails
        """
        return self.client.list_resources('variables', account_id, container_id, workspace_id)

    def get_variable(self, account_id: str, container_id: str, variable_id: str,
                    workspace_id: Optional[str] = None) -> Dict:
        """
        Get a specific variable.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            variable_id: Variable ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Variable object

        Raises:
            ResourceNotFoundError: If variable not found
            GTMError: If API call fails
        """
        return self.client.get_resource('variables', account_id, container_id, variable_id, workspace_id)

    def create_data_layer_variable(self, account_id: str, container_id: str,
                                   name: str, data_layer_name: str,
                                   workspace_id: Optional[str] = None,
                                   folder_id: Optional[str] = None,
                                   default_value: Optional[str] = None) -> Dict:
        """
        Create a Data Layer Variable.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            name: Variable name
            data_layer_name: Data layer variable name (e.g., 'ecommerce.value')
            workspace_id: Workspace ID (auto-detected if None)
            folder_id: Optional folder ID
            default_value: Optional default value

        Returns:
            Created variable

        Raises:
            DuplicateResourceError: If variable name already exists
            GTMError: If API call fails
        """
        variable_body = {
            'name': name,
            'type': 'v',  # Data Layer Variable
            'parameter': [
                {
                    'type': 'INTEGER',
                    'key': 'dataLayerVersion',
                    'value': '2'
                },
                {
                    'type': 'TEMPLATE',
                    'key': 'name',
                    'value': data_layer_name
                }
            ]
        }

        if default_value is not None:
            variable_body['parameter'].extend([
                {
                    'type': 'BOOLEAN',
                    'key': 'setDefaultValue',
                    'value': 'true'
                },
                {
                    'type': 'TEMPLATE',
                    'key': 'defaultValue',
                    'value': default_value
                }
            ])
        else:
            variable_body['parameter'].append({
                'type': 'BOOLEAN',
                'key': 'setDefaultValue',
                'value': 'false'
            })

        if folder_id:
            variable_body['parentFolderId'] = folder_id

        try:
            return self.client.create_resource('variables', account_id, container_id, variable_body, workspace_id)
        except Exception as e:
            error_str = str(e).lower()
            if 'duplicate' in error_str or 'already exists' in error_str:
                raise DuplicateResourceError(
                    f"Variable '{name}' already exists",
                    details={"name": name}
                )
            raise

    def create_user_data_variable(self, account_id: str, container_id: str,
                                  name: str = "EC - User Data",
                                  workspace_id: Optional[str] = None,
                                  auto_mode: bool = True,
                                  folder_id: Optional[str] = None,
                                  email_var: Optional[str] = None,
                                  phone_var: Optional[str] = None,
                                  first_name_var: Optional[str] = None,
                                  last_name_var: Optional[str] = None) -> Dict:
        """
        Create a User-Provided Data variable for Enhanced Conversions.

        This creates a variable of type 'awec' (Google Ads Web Enhanced Conversions)
        that can be used with Google Ads conversion tags to pass user data for
        better attribution matching.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            name: Variable name (default: "EC - User Data")
            workspace_id: Workspace ID (auto-detected if None)
            auto_mode: If True, uses automatic detection (recommended for standard forms);
                      if False, uses manual GTM variable references
            folder_id: Optional folder ID
            email_var: For manual mode - GTM variable name for email (e.g., "{{DLV - email}}")
            phone_var: For manual mode - GTM variable name for phone
            first_name_var: For manual mode - GTM variable name for first name
            last_name_var: For manual mode - GTM variable name for last name

        Returns:
            Created variable with structure matching GTM's expected format

        Raises:
            DuplicateResourceError: If variable name already exists
            ValidationError: If manual mode without variable mappings
            GTMError: If API call fails

        Example (AUTO mode - recommended):
            >>> var_mgr.create_user_data_variable(account_id, container_id, "User-Provided Data")

        Example (MANUAL mode):
            >>> var_mgr.create_user_data_variable(
            ...     account_id, container_id, "EC - Custom Data",
            ...     auto_mode=False,
            ...     email_var="{{DLV - enhanced_conversion_data.email}}",
            ...     phone_var="{{DLV - enhanced_conversion_data.phone_number}}"
            ... )
        """
        # Validate MANUAL mode has at least one field mapping
        if not auto_mode and not any([email_var, phone_var, first_name_var, last_name_var]):
            raise ValidationError(
                "MANUAL mode requires at least one field mapping (email, phone, first_name, or last_name)",
                details={"mode": "MANUAL", "name": name}
            )

        # Type 'awec' = Google Ads Web Enhanced Conversions (User-Provided Data)
        # This is the correct type - NOT 'gtes' which is Google Tag Enhanced Settings
        variable_body = {
            'name': name,
            'type': 'awec',
            'parameter': []
        }

        if auto_mode:
            # AUTO mode - Google automatically detects form fields
            # This is the recommended approach for standard HTML forms
            variable_body['parameter'].extend([
                {'type': 'template', 'key': 'mode', 'value': 'AUTO'},
                {'type': 'boolean', 'key': 'autoPhoneEnabled', 'value': 'true'},
                {'type': 'boolean', 'key': 'autoAddressEnabled', 'value': 'true'},
                {'type': 'boolean', 'key': 'autoEmailEnabled', 'value': 'true'},
                {'type': 'boolean', 'key': 'enableElementBlocking', 'value': 'false'}
            ])
        else:
            # MANUAL mode - specify GTM variable references for each field
            # Use this when data comes from dataLayer or custom sources
            variable_body['parameter'].append({
                'type': 'template',
                'key': 'mode',
                'value': 'MANUAL'
            })

            # Add field mappings using GTM variable syntax {{Variable Name}}
            if email_var:
                variable_body['parameter'].append({
                    'type': 'template',
                    'key': 'email',
                    'value': email_var
                })
            if phone_var:
                variable_body['parameter'].append({
                    'type': 'template',
                    'key': 'phoneNumber',
                    'value': phone_var
                })
            if first_name_var:
                variable_body['parameter'].append({
                    'type': 'template',
                    'key': 'firstName',
                    'value': first_name_var
                })
            if last_name_var:
                variable_body['parameter'].append({
                    'type': 'template',
                    'key': 'lastName',
                    'value': last_name_var
                })

        if folder_id:
            variable_body['parentFolderId'] = folder_id

        try:
            return self.client.create_resource('variables', account_id, container_id, variable_body, workspace_id)
        except Exception as e:
            error_str = str(e).lower()
            if 'duplicate' in error_str or 'already exists' in error_str:
                raise DuplicateResourceError(
                    f"Variable '{name}' already exists",
                    details={"name": name}
                )
            raise

    def update_variable(self, account_id: str, container_id: str, variable_id: str,
                       updates: Dict, workspace_id: Optional[str] = None) -> Dict:
        """
        Update an existing variable.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            variable_id: Variable ID to update
            updates: Dictionary of fields to update
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Updated variable

        Raises:
            ResourceNotFoundError: If variable not found
            GTMError: If API call fails
        """
        # Get current variable
        variable = self.get_variable(account_id, container_id, variable_id, workspace_id)

        # Apply updates
        for key, value in updates.items():
            variable[key] = value

        # Update via API
        return self.client.update_resource('variables', account_id, container_id, variable_id, variable, workspace_id)

    def delete_variable(self, account_id: str, container_id: str, variable_id: str,
                       workspace_id: Optional[str] = None) -> None:
        """
        Delete a variable.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            variable_id: Variable ID to delete
            workspace_id: Workspace ID (auto-detected if None)

        Raises:
            ResourceNotFoundError: If variable not found
            GTMError: If API call fails
        """
        self.client.delete_resource('variables', account_id, container_id, variable_id, workspace_id)
