"""
GTM tag management operations.
"""

from typing import Dict, List, Optional
from .client import GTMClient
from .exceptions import ValidationError, DuplicateResourceError


class TagManager:
    """Manage GTM tags"""

    def __init__(self, client: GTMClient):
        """
        Initialize tag manager.

        Args:
            client: GTMClient instance
        """
        self.client = client

    def list_tags(self, account_id: str, container_id: str,
                 workspace_id: Optional[str] = None,
                 tag_type: Optional[str] = None) -> List[Dict]:
        """
        List all tags in a container.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)
            tag_type: Filter by tag type (e.g., 'awct', 'gaawe')

        Returns:
            List of tags

        Raises:
            GTMError: If API call fails
        """
        tags = self.client.list_resources('tags', account_id, container_id, workspace_id)

        if tag_type:
            tags = [t for t in tags if t.get('type') == tag_type]

        return tags

    def get_tag(self, account_id: str, container_id: str, tag_id: str,
               workspace_id: Optional[str] = None) -> Dict:
        """
        Get a specific tag.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            tag_id: Tag ID
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Tag object

        Raises:
            ResourceNotFoundError: If tag not found
            GTMError: If API call fails
        """
        return self.client.get_resource('tags', account_id, container_id, tag_id, workspace_id)

    def create_tag(self, account_id: str, container_id: str, name: str,
                  tag_type: str, parameters: List[Dict],
                  firing_trigger_ids: List[str],
                  workspace_id: Optional[str] = None,
                  folder_id: Optional[str] = None,
                  paused: bool = False) -> Dict:
        """
        Create a new tag.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            name: Tag name
            tag_type: Tag type (e.g., 'awct', 'gaawe', 'html')
            parameters: List of tag parameters
            firing_trigger_ids: List of trigger IDs that fire this tag
            workspace_id: Workspace ID (auto-detected if None)
            folder_id: Optional folder ID to organize tag
            paused: Whether tag is paused

        Returns:
            Created tag

        Raises:
            ValidationError: If required fields missing
            DuplicateResourceError: If tag name already exists
            GTMError: If API call fails
        """
        if not name or not tag_type:
            raise ValidationError(
                "Tag name and type are required",
                details={"name": name, "tag_type": tag_type}
            )

        tag_body = {
            'name': name,
            'type': tag_type,
            'parameter': parameters,
            'firingTriggerId': firing_trigger_ids,
            'paused': paused
        }

        if folder_id:
            tag_body['parentFolderId'] = folder_id

        try:
            return self.client.create_resource('tags', account_id, container_id, tag_body, workspace_id)
        except Exception as e:
            error_str = str(e).lower()
            if 'duplicate' in error_str or 'already exists' in error_str:
                raise DuplicateResourceError(
                    f"Tag '{name}' already exists",
                    details={"name": name}
                )
            raise

    def update_tag(self, account_id: str, container_id: str, tag_id: str,
                  updates: Dict, workspace_id: Optional[str] = None) -> Dict:
        """
        Update an existing tag.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            tag_id: Tag ID to update
            updates: Dictionary of fields to update
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Updated tag

        Raises:
            ResourceNotFoundError: If tag not found
            GTMError: If API call fails
        """
        # Get current tag
        tag = self.get_tag(account_id, container_id, tag_id, workspace_id)

        # Apply updates
        for key, value in updates.items():
            tag[key] = value

        # Update via API
        return self.client.update_resource('tags', account_id, container_id, tag_id, tag, workspace_id)

    def delete_tag(self, account_id: str, container_id: str, tag_id: str,
                  workspace_id: Optional[str] = None) -> None:
        """
        Delete a tag.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            tag_id: Tag ID to delete
            workspace_id: Workspace ID (auto-detected if None)

        Raises:
            ResourceNotFoundError: If tag not found
            GTMError: If API call fails
        """
        self.client.delete_resource('tags', account_id, container_id, tag_id, workspace_id)

    def list_conversion_tags(self, account_id: str, container_id: str,
                            workspace_id: Optional[str] = None,
                            include_ec_status: bool = True) -> List[Dict]:
        """
        List all Google Ads conversion tracking tags.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            workspace_id: Workspace ID (auto-detected if None)
            include_ec_status: Include Enhanced Conversions status

        Returns:
            List of conversion tags with metadata

        Raises:
            GTMError: If API call fails
        """
        tags = self.list_tags(account_id, container_id, workspace_id, tag_type='awct')

        conversion_tags = []
        for tag in tags:
            tag_info = {
                'tagId': tag['tagId'],
                'name': tag['name'],
                'type': tag['type'],
                'path': tag['path'],
                'fingerprint': tag.get('fingerprint'),
                'paused': tag.get('paused', False)
            }

            # Extract conversion parameters and EC status
            ec_enabled = False
            ec_variable = None

            for param in tag.get('parameter', []):
                key = param.get('key')
                if key == 'conversionId':
                    tag_info['conversionId'] = param.get('value')
                elif key == 'conversionLabel':
                    tag_info['conversionLabel'] = param.get('value')
                elif key == 'enableEnhancedConversion':
                    ec_enabled = param.get('value') == 'true' or param.get('value') is True
                elif key == 'cssProvidedEnhancedConversionValue':
                    ec_variable = param.get('value')

            if include_ec_status:
                tag_info['ecEnabled'] = ec_enabled
                tag_info['ecVariable'] = ec_variable

            conversion_tags.append(tag_info)

        return conversion_tags

    def update_conversion_tag(self, account_id: str, container_id: str,
                             tag_id: str, conversion_id: str, label: str,
                             workspace_id: Optional[str] = None,
                             unpause: bool = False) -> Dict:
        """
        Update a Google Ads conversion tag.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            tag_id: Tag ID to update
            conversion_id: New Google Ads conversion ID
            label: New conversion label
            workspace_id: Workspace ID (auto-detected if None)
            unpause: Set to True to unpause the tag

        Returns:
            Updated tag

        Raises:
            ValidationError: If tag is not a conversion tag
            ResourceNotFoundError: If tag not found
            GTMError: If API call fails
        """
        # Get current tag
        tag = self.get_tag(account_id, container_id, tag_id, workspace_id)

        if tag.get('type') != 'awct':
            raise ValidationError(
                f"Tag {tag_id} is not a conversion tag (type: {tag.get('type')})",
                details={"tag_id": tag_id, "type": tag.get('type')}
            )

        # Update conversion parameters
        updated = False
        for param in tag.get('parameter', []):
            if param.get('key') == 'conversionId':
                param['value'] = conversion_id
                updated = True
            elif param.get('key') == 'conversionLabel':
                param['value'] = label
                updated = True

        if not updated:
            raise ValidationError(
                f"Tag {tag_id} does not have conversion parameters",
                details={"tag_id": tag_id}
            )

        # Unpause if requested
        if unpause and tag.get('paused'):
            tag['paused'] = False

        # Update via API
        return self.client.update_resource('tags', account_id, container_id, tag_id, tag, workspace_id)

    def enable_enhanced_conversions(self, account_id: str, container_id: str,
                                   tag_id: str, user_data_variable: str,
                                   workspace_id: Optional[str] = None) -> Dict:
        """
        Enable Enhanced Conversions on a Google Ads conversion tag.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            tag_id: Tag ID to update
            user_data_variable: Name of User-Provided Data variable (e.g., "User-Provided Data")
            workspace_id: Workspace ID (auto-detected if None)

        Returns:
            Updated tag

        Raises:
            ValidationError: If tag is not a conversion tag
            ResourceNotFoundError: If tag not found
            GTMError: If API call fails
        """
        # Get current tag
        tag = self.get_tag(account_id, container_id, tag_id, workspace_id)

        if tag.get('type') != 'awct':
            raise ValidationError(
                f"Tag {tag_id} is not a Google Ads conversion tag (type: {tag.get('type')})",
                details={"tag_id": tag_id, "type": tag.get('type')}
            )

        # Check if Enhanced Conversions is already enabled
        params = tag.get('parameter', [])
        ec_enabled = False
        ec_var_set = False

        for param in params:
            if param.get('key') == 'enableEnhancedConversion':
                param['value'] = 'true'
                param['type'] = 'boolean'
                ec_enabled = True
            elif param.get('key') == 'cssProvidedEnhancedConversionValue':
                param['value'] = f"{{{{{user_data_variable}}}}}"
                param['type'] = 'template'
                ec_var_set = True

        # Add parameters if not present
        if not ec_enabled:
            params.append({
                'type': 'boolean',
                'key': 'enableEnhancedConversion',
                'value': 'true'
            })

        if not ec_var_set:
            # Reference the variable using GTM variable syntax: {{Variable Name}}
            params.append({
                'type': 'template',
                'key': 'cssProvidedEnhancedConversionValue',
                'value': f"{{{{{user_data_variable}}}}}"
            })

        tag['parameter'] = params

        # Update via API
        return self.client.update_resource('tags', account_id, container_id, tag_id, tag, workspace_id)
