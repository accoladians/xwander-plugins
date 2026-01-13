"""Performance Max campaign management.

This module handles CRUD operations for Performance Max campaigns.
"""

from typing import List, Dict, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import CampaignNotFoundError, APIError, QuotaExceededError


def list_campaigns(
    client: GoogleAdsClient,
    customer_id: str,
    enabled_only: bool = False
) -> List[Dict]:
    """List all Performance Max campaigns.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        enabled_only: If True, only return enabled campaigns

    Returns:
        List of dicts with campaign details

    Raises:
        APIError: For API errors
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        status_filter = ""
        if enabled_only:
            status_filter = "AND campaign.status = 'ENABLED'"

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_budget.amount_micros,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions
            FROM campaign
            WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
            {status_filter}
            ORDER BY campaign.name
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        campaigns = []
        for row in response:
            campaigns.append({
                'id': row.campaign.id,
                'name': row.campaign.name,
                'status': row.campaign.status.name,
                'budget_micros': row.campaign_budget.amount_micros if row.campaign_budget else 0,
                'cost_micros': row.metrics.cost_micros,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'conversions': row.metrics.conversions,
                'resource_name': f"customers/{customer_id}/campaigns/{row.campaign.id}"
            })

        return campaigns

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "QUOTA_EXCEEDED" in str(error.error_code):
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to list campaigns: {error.message if error else str(ex)}")


def get_campaign(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str
) -> Dict:
    """Get details for a specific campaign.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        campaign_id: Campaign ID

    Returns:
        Dict with campaign details

    Raises:
        CampaignNotFoundError: If campaign doesn't exist
        APIError: For other API errors
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_budget.id,
                campaign_budget.amount_micros,
                campaign.target_cpa.target_cpa_micros,
                campaign.target_roas.target_roas,
                campaign.maximize_conversions.target_cpa_micros,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            return {
                'id': row.campaign.id,
                'name': row.campaign.name,
                'status': row.campaign.status.name,
                'budget_id': row.campaign_budget.id if row.campaign_budget else None,
                'budget_micros': row.campaign_budget.amount_micros if row.campaign_budget else 0,
                'target_cpa_micros': row.campaign.target_cpa.target_cpa_micros if row.campaign.target_cpa else None,
                'target_roas': row.campaign.target_roas.target_roas if row.campaign.target_roas else None,
                'cost_micros': row.metrics.cost_micros,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'conversions': row.metrics.conversions,
                'conversions_value': row.metrics.conversions_value,
                'resource_name': f"customers/{customer_id}/campaigns/{row.campaign.id}"
            }

        raise CampaignNotFoundError(f"Campaign {campaign_id} not found for customer {customer_id}")

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "NOT_FOUND" in str(error.error_code):
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
        else:
            raise APIError(f"Failed to get campaign: {error.message if error else str(ex)}")


def list_asset_groups(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """List asset groups for Performance Max campaigns.

    Uses GAQL implicit joins - when querying asset_group, campaign fields
    are automatically accessible via the asset_group.campaign relationship.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        campaign_id: Optional campaign ID to filter by (must be numeric)
        limit: Maximum rows to return (default: 100, max: 10000)

    Returns:
        List of dicts with asset group details

    Raises:
        ValueError: If campaign_id is not numeric
        APIError: For API errors
    """
    # Input validation - prevent GAQL injection
    if campaign_id is not None:
        campaign_id = str(campaign_id).replace('-', '')
        if not campaign_id.isdigit():
            raise ValueError(f"Invalid campaign_id: must be numeric, got '{campaign_id}'")

    # Validate limit
    limit = min(max(1, limit), 10000)

    try:
        ga_service = client.get_service("GoogleAdsService")

        # GAQL doesn't support subqueries - use implicit join with direct field reference
        campaign_filter = ""
        if campaign_id:
            campaign_filter = f"AND campaign.id = {campaign_id}"

        query = f"""
            SELECT
                asset_group.id,
                asset_group.name,
                asset_group.campaign,
                asset_group.status,
                asset_group.resource_name,
                campaign.id,
                campaign.name
            FROM asset_group
            WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
            {campaign_filter}
            ORDER BY asset_group.name
            LIMIT {limit}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        asset_groups = []
        for row in response:
            ag = row.asset_group
            # Use campaign.id directly from implicit join (more efficient than string splitting)
            asset_groups.append({
                'id': ag.id,
                'name': ag.name,
                'campaign_id': str(row.campaign.id),
                'campaign_name': row.campaign.name,
                'status': ag.status.name,
                'resource_name': ag.resource_name
            })

        return asset_groups

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        raise APIError(f"Failed to list asset groups: {error.message if error else str(ex)}")


def get_campaign_stats(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    date_range: str = "LAST_30_DAYS"
) -> Dict:
    """Get detailed stats for a campaign.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        campaign_id: Campaign ID
        date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, etc.)

    Returns:
        Dict with detailed campaign statistics

    Raises:
        CampaignNotFoundError: If campaign doesn't exist
        APIError: For other API errors
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_value,
                metrics.average_cpc,
                metrics.ctr,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            return {
                'campaign_id': row.campaign.id,
                'campaign_name': row.campaign.name,
                'cost_micros': row.metrics.cost_micros,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'conversions': row.metrics.conversions,
                'conversions_value': row.metrics.conversions_value,
                'average_cpc': row.metrics.average_cpc,
                'ctr': row.metrics.ctr,
                'cost_per_conversion': row.metrics.cost_per_conversion,
                'date_range': date_range
            }

        raise CampaignNotFoundError(f"Campaign {campaign_id} not found")

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "NOT_FOUND" in str(error.error_code):
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
        else:
            raise APIError(f"Failed to get campaign stats: {error.message if error else str(ex)}")
