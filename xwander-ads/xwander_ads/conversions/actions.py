"""
Google Ads Conversion Action Manager

Create, list, update, and manage conversion actions programmatically.
Get conversion labels (tag_snippets) for GTM integration.
"""

import logging
from typing import Dict, List, Optional, Any
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import GoogleAdsError

logger = logging.getLogger(__name__)


class ConversionActionManager:
    """Manage Google Ads conversion actions via API"""

    def __init__(self, client: GoogleAdsClient):
        """
        Initialize the conversion action manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client
        self._ga_service = client.get_service("GoogleAdsService")
        self._conversion_service = client.get_service("ConversionActionService")

    def list_conversions(
        self,
        customer_id: str,
        include_removed: bool = False,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all conversion actions in an account.

        Args:
            customer_id: Google Ads customer ID
            include_removed: Include removed conversion actions
            status_filter: Filter by status (ENABLED, PAUSED, REMOVED)

        Returns:
            List of dicts with conversion details including tag snippets

        Raises:
            GoogleAdsError: If API request fails
        """
        where_clauses = []

        if not include_removed:
            where_clauses.append("conversion_action.status != 'REMOVED'")

        if status_filter:
            where_clauses.append(f"conversion_action.status = '{status_filter}'")

        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.type,
                conversion_action.category,
                conversion_action.status,
                conversion_action.primary_for_goal,
                conversion_action.counting_type,
                conversion_action.click_through_lookback_window_days,
                conversion_action.view_through_lookback_window_days,
                conversion_action.value_settings.default_value,
                conversion_action.value_settings.always_use_default_value,
                conversion_action.tag_snippets
            FROM conversion_action
            {where_clause}
            ORDER BY conversion_action.name
        """

        results = []
        try:
            response = self._ga_service.search(customer_id=customer_id, query=query)

            for row in response:
                conv = row.conversion_action

                # Extract tag snippet info (contains conversion label)
                tag_info = self._extract_tag_info(conv)

                results.append({
                    'id': conv.id,
                    'name': conv.name,
                    'type': conv.type_.name,
                    'category': conv.category.name,
                    'status': conv.status.name,
                    'primary_for_goal': conv.primary_for_goal,
                    'counting_type': conv.counting_type.name,
                    'click_through_days': conv.click_through_lookback_window_days,
                    'view_through_days': conv.view_through_lookback_window_days,
                    'default_value': conv.value_settings.default_value,
                    'always_use_default_value': conv.value_settings.always_use_default_value,
                    'tag_info': tag_info
                })

            logger.info(f"Retrieved {len(results)} conversion actions for customer {customer_id}")
            return results

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            raise GoogleAdsError(f"Failed to list conversions: {error_msg}")

    def get_conversion(
        self,
        customer_id: str,
        conversion_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific conversion action by ID.

        Args:
            customer_id: Google Ads customer ID
            conversion_id: Conversion action ID

        Returns:
            Dict with conversion details or None if not found
        """
        conversions = self.list_conversions(customer_id, include_removed=True)
        return next((c for c in conversions if str(c['id']) == str(conversion_id)), None)

    def get_conversion_labels(
        self,
        customer_id: str,
        webpage_only: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get conversion labels for GTM integration.

        Args:
            customer_id: Google Ads customer ID
            webpage_only: Only return WEBPAGE type conversions (default: True)

        Returns:
            Dict mapping conversion_name -> {id, label, conversion_id, category}
        """
        conversions = self.list_conversions(customer_id)

        labels = {}
        for conv in conversions:
            # Filter by type if requested
            if webpage_only and conv['type'] != 'WEBPAGE':
                continue

            # Only include enabled conversions
            if conv['status'] != 'ENABLED':
                continue

            tag_info = conv.get('tag_info', {})
            labels[conv['name']] = {
                'action_id': conv['id'],
                'conversion_id': tag_info.get('conversion_id', customer_id),
                'conversion_label': tag_info.get('conversion_label', 'UNKNOWN'),
                'category': conv['category']
            }

        logger.info(f"Retrieved {len(labels)} conversion labels for customer {customer_id}")
        return labels

    def create_conversion(
        self,
        customer_id: str,
        name: str,
        category: str = "SUBMIT_LEAD_FORM",
        conversion_type: str = "WEBPAGE",
        value: float = 0,
        count_type: str = "ONE_PER_CLICK",
        click_through_days: int = 90,
        view_through_days: int = 1,
        include_in_goals: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new conversion action.

        Args:
            customer_id: Google Ads customer ID
            name: Unique name for the conversion
            category: PURCHASE, SUBMIT_LEAD_FORM, SIGNUP, CONTACT, PHONE_CALL_LEAD, etc.
            conversion_type: WEBPAGE, UPLOAD_CLICKS, etc.
            value: Default conversion value
            count_type: ONE_PER_CLICK or MANY_PER_CLICK
            click_through_days: Click attribution window (default: 90)
            view_through_days: View-through attribution window (default: 1)
            include_in_goals: Include in conversions column

        Returns:
            Dict with created conversion details including label

        Raises:
            GoogleAdsError: If creation fails
        """
        # Create the conversion action operation
        conversion_action_operation = self.client.get_type("ConversionActionOperation")
        conversion_action = conversion_action_operation.create

        # Set basic properties
        conversion_action.name = name
        conversion_action.type_ = self.client.enums.ConversionActionTypeEnum[conversion_type]
        conversion_action.category = self.client.enums.ConversionActionCategoryEnum[category]
        conversion_action.status = self.client.enums.ConversionActionStatusEnum.ENABLED

        # Set counting
        conversion_action.counting_type = self.client.enums.ConversionActionCountingTypeEnum[count_type]

        # Set attribution windows
        conversion_action.click_through_lookback_window_days = click_through_days
        conversion_action.view_through_lookback_window_days = view_through_days

        # Set value settings
        conversion_action.value_settings.default_value = value
        conversion_action.value_settings.always_use_default_value = (value > 0)

        # Set primary for goal
        conversion_action.primary_for_goal = include_in_goals

        try:
            response = self._conversion_service.mutate_conversion_actions(
                customer_id=customer_id,
                operations=[conversion_action_operation]
            )

            # Get the created resource name
            resource_name = response.results[0].resource_name
            conv_id = resource_name.split('/')[-1]

            # Query to get the tag snippets (labels are auto-generated)
            query = f"""
                SELECT
                    conversion_action.id,
                    conversion_action.name,
                    conversion_action.tag_snippets
                FROM conversion_action
                WHERE conversion_action.resource_name = '{resource_name}'
            """

            label_response = self._ga_service.search(customer_id=customer_id, query=query)

            tag_info = {}
            for row in label_response:
                conv = row.conversion_action
                tag_info = self._extract_tag_info(conv)

            logger.info(f"Created conversion action: {name} (ID: {conv_id})")

            return {
                'success': True,
                'resource_name': resource_name,
                'action_id': conv_id,
                'name': name,
                'conversion_id': tag_info.get('conversion_id', customer_id),
                'conversion_label': tag_info.get('conversion_label', 'PENDING'),
                'message': f"Created conversion action: {name}"
            }

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            raise GoogleAdsError(f"Failed to create conversion: {error_msg}")

    def update_conversion(
        self,
        customer_id: str,
        conversion_id: str,
        **updates
    ) -> Dict[str, Any]:
        """
        Update an existing conversion action.

        Args:
            customer_id: Google Ads customer ID
            conversion_id: Conversion action ID
            **updates: Fields to update (status, name, value, etc.)

        Returns:
            Dict with success status and message

        Raises:
            GoogleAdsError: If update fails
        """
        conversion_action_operation = self.client.get_type("ConversionActionOperation")
        conversion_action = conversion_action_operation.update

        conversion_action.resource_name = (
            f"customers/{customer_id}/conversionActions/{conversion_id}"
        )

        # Track which fields are being updated
        update_mask_paths = []

        # Status update
        if 'status' in updates:
            status_value = updates['status']
            conversion_action.status = self.client.enums.ConversionActionStatusEnum[status_value]
            update_mask_paths.append("status")

        # Name update
        if 'name' in updates:
            conversion_action.name = updates['name']
            update_mask_paths.append("name")

        # Value settings update
        if 'value' in updates:
            conversion_action.value_settings.default_value = updates['value']
            update_mask_paths.append("value_settings.default_value")

        if 'always_use_default_value' in updates:
            conversion_action.value_settings.always_use_default_value = updates['always_use_default_value']
            update_mask_paths.append("value_settings.always_use_default_value")

        # Primary for goal update
        if 'primary_for_goal' in updates:
            conversion_action.primary_for_goal = updates['primary_for_goal']
            update_mask_paths.append("primary_for_goal")

        # Attribution windows
        if 'click_through_days' in updates:
            conversion_action.click_through_lookback_window_days = updates['click_through_days']
            update_mask_paths.append("click_through_lookback_window_days")

        if 'view_through_days' in updates:
            conversion_action.view_through_lookback_window_days = updates['view_through_days']
            update_mask_paths.append("view_through_lookback_window_days")

        # Set the update mask
        self.client.copy_from(
            conversion_action_operation.update_mask,
            self.client.get_type("FieldMask")(paths=update_mask_paths)
        )

        try:
            response = self._conversion_service.mutate_conversion_actions(
                customer_id=customer_id,
                operations=[conversion_action_operation]
            )

            logger.info(f"Updated conversion action {conversion_id}: {', '.join(update_mask_paths)}")

            return {
                'success': True,
                'message': f"Updated conversion {conversion_id}",
                'updated_fields': update_mask_paths
            }

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            raise GoogleAdsError(f"Failed to update conversion: {error_msg}")

    def remove_conversion(self, customer_id: str, conversion_id: str) -> Dict[str, Any]:
        """
        Remove (disable) a conversion action.

        Args:
            customer_id: Google Ads customer ID
            conversion_id: Conversion action ID

        Returns:
            Dict with success status and message

        Raises:
            GoogleAdsError: If removal fails
        """
        return self.update_conversion(
            customer_id=customer_id,
            conversion_id=conversion_id,
            status='REMOVED'
        )

    def _extract_tag_info(self, conversion_action) -> Dict[str, str]:
        """
        Extract conversion ID and label from tag snippets.

        Args:
            conversion_action: ConversionAction protobuf object

        Returns:
            Dict with conversion_id and conversion_label
        """
        tag_info = {}

        if not conversion_action.tag_snippets:
            return tag_info

        for snippet in conversion_action.tag_snippets:
            tag_info['type'] = snippet.type_.name

            # The event_snippet contains the conversion label
            if snippet.event_snippet:
                event = snippet.event_snippet

                # Parse AW-xxx/label format from gtag send_to parameter
                if "'send_to':" in event:
                    start = event.find("'send_to':") + 11
                    end = event.find("'", start + 1)

                    if start > 10 and end > start:
                        send_to = event[start:end]

                        if '/' in send_to:
                            parts = send_to.split('/')
                            tag_info['conversion_id'] = parts[0].replace('AW-', '')
                            tag_info['conversion_label'] = parts[1]

        return tag_info
