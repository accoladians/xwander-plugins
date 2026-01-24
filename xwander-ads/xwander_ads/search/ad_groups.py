"""Ad group management for Search campaigns.

This module handles CRUD operations for ad groups within Search campaigns,
enabling full campaign structure management via API.

Key Features:
    - Create ad groups with CPC bidding
    - List ad groups with metrics
    - Get individual ad group details
    - Bulk ad group creation

API Version: v22 (google-ads-python 28.4.1)
"""

from typing import List, Dict, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import (
    CampaignNotFoundError,
    APIError,
    QuotaExceededError,
    ValidationError,
    AdsError
)


class AdGroupNotFoundError(AdsError):
    """Ad group not found."""
    exit_code = 4


def create_ad_group(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    name: str,
    cpc_bid_eur: Optional[float] = None,
    status: str = "PAUSED"
) -> Dict:
    """Create an ad group within a Search campaign.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (e.g., "2425288235")
        campaign_id: Parent campaign ID (e.g., "23458341084")
        name: Ad group name (e.g., "Northern Lights Tours")
        cpc_bid_eur: Default CPC bid in EUR (optional)
        status: Initial status (PAUSED recommended, or ENABLED)

    Returns:
        Dict with:
            - ad_group_id: Created ad group ID
            - resource_name: Full resource name
            - name: Ad group name
            - url: Link to Google Ads UI

    Raises:
        ValidationError: Invalid parameters
        CampaignNotFoundError: Campaign doesn't exist
        APIError: API failures

    Example:
        >>> result = create_ad_group(
        ...     client, "2425288235", "23458341084",
        ...     "Northern Lights | Ivalo",
        ...     cpc_bid_eur=1.50
        ... )
        >>> print(f"Created: {result['ad_group_id']}")
    """
    # Validate inputs
    if not name or not name.strip():
        raise ValidationError("Ad group name is required")
    if not campaign_id or not str(campaign_id).isdigit():
        raise ValidationError("Valid campaign_id is required")
    if cpc_bid_eur is not None and cpc_bid_eur <= 0:
        raise ValidationError("CPC bid must be positive")

    # Validate status
    valid_statuses = {"ENABLED", "PAUSED"}
    status_upper = status.upper()
    if status_upper not in valid_statuses:
        raise ValidationError(f"Status must be one of: {list(valid_statuses)}")

    try:
        ad_group_service = client.get_service("AdGroupService")
        campaign_service = client.get_service("CampaignService")

        # Create ad group operation
        operation = client.get_type("AdGroupOperation")
        ad_group = operation.create
        ad_group.name = name
        ad_group.campaign = campaign_service.campaign_path(customer_id, campaign_id)

        # Set status
        if status_upper == "ENABLED":
            ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
        else:
            ad_group.status = client.enums.AdGroupStatusEnum.PAUSED

        # Set CPC bid if provided
        if cpc_bid_eur is not None:
            ad_group.cpc_bid_micros = int(cpc_bid_eur * 1_000_000)

        # Ad group type: SEARCH_STANDARD (default for Search campaigns)
        ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD

        # Execute operation
        response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[operation]
        )

        resource_name = response.results[0].resource_name
        ad_group_id = resource_name.split("/")[-1]

        return {
            'ad_group_id': ad_group_id,
            'resource_name': resource_name,
            'name': name,
            'status': status_upper,
            'cpc_bid_eur': cpc_bid_eur,
            'campaign_id': campaign_id,
            'url': f"https://ads.google.com/aw/adgroups?campaignId={campaign_id}&__e={customer_id}"
        }

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error:
            error_msg = error.message
            if "QUOTA_EXCEEDED" in str(error.error_code):
                raise QuotaExceededError("API quota exceeded - try again later")
            elif "NOT_FOUND" in str(error.error_code) or "campaign" in error_msg.lower():
                raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
            else:
                raise APIError(f"Failed to create ad group: {error_msg}")
        else:
            raise APIError(f"Failed to create ad group: {str(ex)}")


def list_ad_groups(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: Optional[str] = None,
    enabled_only: bool = False,
    limit: int = 100
) -> List[Dict]:
    """List ad groups with optional campaign filter.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID
        campaign_id: Optional campaign filter
        enabled_only: If True, only return enabled ad groups
        limit: Maximum ad groups to return (default: 100, max: 10000)

    Returns:
        List of dicts:
            - id: Ad group ID
            - name: Ad group name
            - campaign_id: Parent campaign ID
            - campaign_name: Parent campaign name
            - status: ENABLED/PAUSED/REMOVED
            - cpc_bid_micros: Default CPC bid
            - impressions, clicks, conversions: Metrics

    Raises:
        APIError: For API errors

    Example:
        >>> ad_groups = list_ad_groups(client, "2425288235", campaign_id="23458341084")
        >>> for ag in ad_groups:
        ...     print(f"{ag['name']}: {ag['status']}")
    """
    # Validate limit
    limit = min(max(1, limit), 10000)

    try:
        ga_service = client.get_service("GoogleAdsService")

        # Build filters
        filters = []
        if campaign_id:
            if not str(campaign_id).isdigit():
                raise ValidationError("campaign_id must be numeric")
            filters.append(f"campaign.id = {campaign_id}")
        if enabled_only:
            filters.append("ad_group.status = 'ENABLED'")
        else:
            filters.append("ad_group.status != 'REMOVED'")

        where_clause = " AND ".join(filters) if filters else "ad_group.status != 'REMOVED'"

        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                ad_group.cpc_bid_micros,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM ad_group
            WHERE {where_clause}
            ORDER BY ad_group.name
            LIMIT {limit}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        ad_groups = []
        for row in response:
            ad_groups.append({
                'id': row.ad_group.id,
                'name': row.ad_group.name,
                'status': row.ad_group.status.name,
                'type': row.ad_group.type_.name,
                'cpc_bid_micros': row.ad_group.cpc_bid_micros,
                'cpc_bid_eur': row.ad_group.cpc_bid_micros / 1_000_000 if row.ad_group.cpc_bid_micros else None,
                'campaign_id': row.campaign.id,
                'campaign_name': row.campaign.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'cost_micros': row.metrics.cost_micros,
                'cost_eur': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions,
                'resource_name': f"customers/{customer_id}/adGroups/{row.ad_group.id}"
            })

        return ad_groups

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "QUOTA_EXCEEDED" in str(error.error_code):
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to list ad groups: {error.message if error else str(ex)}")


def get_ad_group(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: str
) -> Dict:
    """Get detailed ad group information.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID
        ad_group_id: Ad group ID

    Returns:
        Dict with ad group details:
            - id: Ad group ID
            - name: Ad group name
            - status: ENABLED/PAUSED/REMOVED
            - campaign_id: Parent campaign ID
            - campaign_name: Parent campaign name
            - cpc_bid_micros: Default CPC bid
            - type: Ad group type
            - metrics: Performance metrics

    Raises:
        AdGroupNotFoundError: If ad group doesn't exist
        APIError: For other API errors

    Example:
        >>> ad_group = get_ad_group(client, "2425288235", "12345678901")
        >>> print(f"{ad_group['name']}: {ad_group['status']}")
    """
    if not ad_group_id or not str(ad_group_id).isdigit():
        raise ValidationError("Valid ad_group_id is required")

    try:
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                ad_group.cpc_bid_micros,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM ad_group
            WHERE ad_group.id = {ad_group_id}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            return {
                'id': row.ad_group.id,
                'name': row.ad_group.name,
                'status': row.ad_group.status.name,
                'type': row.ad_group.type_.name,
                'cpc_bid_micros': row.ad_group.cpc_bid_micros,
                'cpc_bid_eur': row.ad_group.cpc_bid_micros / 1_000_000 if row.ad_group.cpc_bid_micros else None,
                'campaign_id': row.campaign.id,
                'campaign_name': row.campaign.name,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'cost_micros': row.metrics.cost_micros,
                'cost_eur': row.metrics.cost_micros / 1_000_000,
                'conversions': row.metrics.conversions,
                'conversions_value': row.metrics.conversions_value,
                'resource_name': f"customers/{customer_id}/adGroups/{row.ad_group.id}"
            }

        raise AdGroupNotFoundError(f"Ad group {ad_group_id} not found for customer {customer_id}")

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "NOT_FOUND" in str(error.error_code):
            raise AdGroupNotFoundError(f"Ad group {ad_group_id} not found")
        else:
            raise APIError(f"Failed to get ad group: {error.message if error else str(ex)}")


def bulk_create_ad_groups(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    ad_groups_list: List[Dict]
) -> List[Dict]:
    """Create multiple ad groups in batch.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID
        campaign_id: Parent campaign ID
        ad_groups_list: List of dicts with keys:
            - name: Ad group name (required)
            - cpc_bid_eur: Optional default bid
            - status: Optional status (defaults to PAUSED)

    Returns:
        List of results (one per ad group):
            - status: 'success' or 'error'
            - ad_group_id: Created ad group ID (if success)
            - name: Ad group name
            - error: Error message (if error)

    Raises:
        ValidationError: If input is invalid
        APIError: For API errors

    Example:
        >>> ad_groups = [
        ...     {"name": "Northern Lights", "cpc_bid_eur": 1.50},
        ...     {"name": "Husky Safari", "cpc_bid_eur": 1.20},
        ...     {"name": "Reindeer Farm", "cpc_bid_eur": 0.90},
        ... ]
        >>> results = bulk_create_ad_groups(client, "2425288235", "23458341084", ad_groups)
    """
    if not ad_groups_list:
        raise ValidationError("ad_groups_list cannot be empty")
    if not campaign_id or not str(campaign_id).isdigit():
        raise ValidationError("Valid campaign_id is required")

    try:
        ad_group_service = client.get_service("AdGroupService")
        campaign_service = client.get_service("CampaignService")

        operations = []
        for ag_config in ad_groups_list:
            # Validate required fields
            if 'name' not in ag_config or not ag_config['name']:
                raise ValidationError(f"Each ad group must have a 'name': {ag_config}")

            operation = client.get_type("AdGroupOperation")
            ad_group = operation.create
            ad_group.name = ag_config['name']
            ad_group.campaign = campaign_service.campaign_path(customer_id, campaign_id)

            # Set status (default to PAUSED for safety)
            status = ag_config.get('status', 'PAUSED').upper()
            if status == "ENABLED":
                ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
            else:
                ad_group.status = client.enums.AdGroupStatusEnum.PAUSED

            # Set CPC bid if provided
            if 'cpc_bid_eur' in ag_config and ag_config['cpc_bid_eur'] is not None:
                ad_group.cpc_bid_micros = int(ag_config['cpc_bid_eur'] * 1_000_000)

            # Ad group type
            ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD

            operations.append(operation)

        # Execute batch with partial failure support
        response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=operations,
            partial_failure=True
        )

        # Process results
        results = []
        for i, result in enumerate(response.results):
            if result.resource_name:
                ad_group_id = result.resource_name.split("/")[-1]
                results.append({
                    'status': 'success',
                    'ad_group_id': ad_group_id,
                    'resource_name': result.resource_name,
                    'name': ad_groups_list[i]['name']
                })
            else:
                # Check partial failure errors
                error_msg = "Failed to create"
                if response.partial_failure_error:
                    # Extract error for this specific operation
                    error_msg = f"Failed: {response.partial_failure_error.message}"

                results.append({
                    'status': 'error',
                    'name': ad_groups_list[i]['name'],
                    'error': error_msg
                })

        return results

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error:
            error_msg = error.message
            if "QUOTA_EXCEEDED" in str(error.error_code):
                raise QuotaExceededError("API quota exceeded - try again later")
            elif "NOT_FOUND" in str(error.error_code) or "campaign" in error_msg.lower():
                raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
            else:
                raise APIError(f"Failed to create ad groups: {error_msg}")
        else:
            raise APIError(f"Failed to create ad groups: {str(ex)}")
