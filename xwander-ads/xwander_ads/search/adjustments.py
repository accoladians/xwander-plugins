"""Search campaign adjustments - device bids and attribution windows.

This module handles campaign-level adjustments for Search campaigns:
- Device bid modifiers (mobile/desktop/tablet)
- Conversion action attribution window updates
- Campaign conversion goal linking

Key Use Cases:
    - Day Tours: +50% mobile, -30% desktop (87% mobile traffic)
    - Attribution: 7 days for Day Tours, 90 days for Multiday

API Version: v22 (google-ads-python 28.4.1)
"""

from typing import Dict, List, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import (
    CampaignNotFoundError,
    APIError,
    QuotaExceededError,
    ValidationError,
    InvalidResourceError
)


# Device enum values for reference
DEVICE_TYPES = {
    'MOBILE': 4,       # Smartphones
    'DESKTOP': 2,      # Desktop and laptop computers
    'TABLET': 3,       # Tablets
    'CONNECTED_TV': 6, # Smart TVs
}

# Recommended bid modifiers for Day Tours
DAY_TOURS_DEVICE_MODIFIERS = {
    'MOBILE': 1.5,    # +50% (tourists searching on phones)
    'DESKTOP': 0.7,   # -30% (mostly Finnish locals)
    'TABLET': 1.0,    # baseline
}


def set_device_bid_adjustments(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    mobile_modifier: float = 1.0,
    desktop_modifier: float = 1.0,
    tablet_modifier: float = 1.0
) -> Dict:
    """Set device bid modifiers for a campaign.

    Device bid adjustments control how much more or less to bid for
    different device types. For Day Tours, mobile gets +50% because
    87% of in-destination searches are on smartphones.

    Modifier Values:
        - 1.0 = No adjustment (baseline)
        - 1.5 = +50% bid increase
        - 0.7 = -30% bid decrease
        - 0.0 = -100% (completely exclude device - use with caution)
        - Range: 0.1 (-90%) to 10.0 (+900%)

    IMPORTANT: This must be called AFTER campaign creation.
    Device criteria cannot be set during campaign creation.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens, e.g., "2425288235")
        campaign_id: Campaign ID (e.g., "12345678901")
        mobile_modifier: Mobile bid modifier (default: 1.0)
        desktop_modifier: Desktop bid modifier (default: 1.0)
        tablet_modifier: Tablet bid modifier (default: 1.0)

    Returns:
        Dict with results:
            - campaign_id: Campaign ID
            - device_adjustments: Dict of device -> modifier set
            - results: List of created resource names

    Raises:
        ValidationError: If modifiers are out of range
        CampaignNotFoundError: If campaign doesn't exist
        APIError: For other API errors

    Example:
        >>> # Day Tours: favor mobile, reduce desktop
        >>> result = set_device_bid_adjustments(
        ...     client,
        ...     "2425288235",
        ...     "12345678901",
        ...     mobile_modifier=1.5,   # +50%
        ...     desktop_modifier=0.7,  # -30%
        ...     tablet_modifier=1.0    # baseline
        ... )
        >>> print(f"Set {len(result['results'])} device adjustments")
        Set 3 device adjustments
    """
    # Validate modifiers
    for name, value in [('mobile', mobile_modifier), ('desktop', desktop_modifier), ('tablet', tablet_modifier)]:
        if value < 0.0 or value > 10.0:
            raise ValidationError(
                f"Invalid {name}_modifier: {value}. Must be between 0.0 and 10.0"
            )

    try:
        campaign_criterion_service = client.get_service("CampaignCriterionService")
        campaign_service = client.get_service("CampaignService")

        campaign_resource = campaign_service.campaign_path(customer_id, campaign_id)

        operations = []

        # Mobile bid adjustment
        if mobile_modifier != 1.0 or True:  # Always set for explicit control
            mobile_op = client.get_type("CampaignCriterionOperation")
            mobile_criterion = mobile_op.create
            mobile_criterion.campaign = campaign_resource
            mobile_criterion.device.type_ = client.enums.DeviceEnum.MOBILE
            mobile_criterion.bid_modifier = mobile_modifier
            mobile_criterion.negative = False
            operations.append(mobile_op)

        # Desktop bid adjustment
        if desktop_modifier != 1.0 or True:
            desktop_op = client.get_type("CampaignCriterionOperation")
            desktop_criterion = desktop_op.create
            desktop_criterion.campaign = campaign_resource
            desktop_criterion.device.type_ = client.enums.DeviceEnum.DESKTOP
            desktop_criterion.bid_modifier = desktop_modifier
            desktop_criterion.negative = False
            operations.append(desktop_op)

        # Tablet bid adjustment
        if tablet_modifier != 1.0 or True:
            tablet_op = client.get_type("CampaignCriterionOperation")
            tablet_criterion = tablet_op.create
            tablet_criterion.campaign = campaign_resource
            tablet_criterion.device.type_ = client.enums.DeviceEnum.TABLET
            tablet_criterion.bid_modifier = tablet_modifier
            tablet_criterion.negative = False
            operations.append(tablet_op)

        # Execute operations
        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )

        results = [result.resource_name for result in response.results]

        return {
            'campaign_id': campaign_id,
            'device_adjustments': {
                'MOBILE': mobile_modifier,
                'DESKTOP': desktop_modifier,
                'TABLET': tablet_modifier,
            },
            'results': results
        }

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        error_str = str(error.error_code) if error else ""

        if "NOT_FOUND" in error_str:
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
        elif "QUOTA_EXCEEDED" in error_str:
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to set device adjustments: {error.message if error else str(ex)}")


def update_conversion_attribution(
    client: GoogleAdsClient,
    customer_id: str,
    conversion_action_id: str,
    click_lookback_days: int,
    view_lookback_days: int = 1
) -> Dict:
    """Update conversion action attribution windows.

    Attribution windows control how long after a click a conversion
    is attributed to the ad. Different products need different windows:
    - Day Tours: 7 days (78% book within 48 hours)
    - Multiday: 90 days (4-5 month booking lead time)

    IMPORTANT: Attribution changes affect ALL campaigns using this
    conversion action. Create product-specific conversion actions
    for different attribution needs.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens, e.g., "2425288235")
        conversion_action_id: Conversion action ID (e.g., "7452944340")
        click_lookback_days: Click-through attribution window (1-90 days)
        view_lookback_days: View-through attribution window (1-30 days, default: 1)

    Returns:
        Dict with results:
            - conversion_action_id: Updated action ID
            - click_lookback_days: New click window
            - view_lookback_days: New view window
            - resource_name: Conversion action resource

    Raises:
        ValidationError: If windows are out of range
        InvalidResourceError: If conversion action doesn't exist
        APIError: For other API errors

    Example:
        >>> # Update Day Tours to 7-day window
        >>> result = update_conversion_attribution(
        ...     client,
        ...     "2425288235",
        ...     "7452944340",
        ...     click_lookback_days=7,
        ...     view_lookback_days=1
        ... )
        >>> print(f"Updated: {result['click_lookback_days']} day window")
        Updated: 7 day window

        >>> # Update Multiday to 90-day window
        >>> result = update_conversion_attribution(
        ...     client,
        ...     "2425288235",
        ...     "7452944343",
        ...     click_lookback_days=90,
        ...     view_lookback_days=30
        ... )
    """
    # Validate windows
    if click_lookback_days < 1 or click_lookback_days > 90:
        raise ValidationError(
            f"click_lookback_days must be 1-90, got {click_lookback_days}"
        )
    if view_lookback_days < 1 or view_lookback_days > 30:
        raise ValidationError(
            f"view_lookback_days must be 1-30, got {view_lookback_days}"
        )

    try:
        ca_service = client.get_service("ConversionActionService")

        # Build resource name
        conversion_action_resource = ca_service.conversion_action_path(
            customer_id,
            str(conversion_action_id)
        )

        # Create update operation
        op = client.get_type("ConversionActionOperation")
        op.update_mask.paths.extend([
            "click_through_lookback_window_days",
            "view_through_lookback_window_days"
        ])

        ca = op.update
        ca.resource_name = conversion_action_resource
        ca.click_through_lookback_window_days = click_lookback_days
        ca.view_through_lookback_window_days = view_lookback_days

        # Execute update
        response = ca_service.mutate_conversion_actions(
            customer_id=customer_id,
            operations=[op]
        )

        return {
            'conversion_action_id': conversion_action_id,
            'click_lookback_days': click_lookback_days,
            'view_lookback_days': view_lookback_days,
            'resource_name': response.results[0].resource_name
        }

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        error_str = str(error.error_code) if error else ""

        if "NOT_FOUND" in error_str:
            raise InvalidResourceError(f"Conversion action {conversion_action_id} not found")
        elif "QUOTA_EXCEEDED" in error_str:
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to update attribution: {error.message if error else str(ex)}")


def link_conversion_actions(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    conversion_action_ids: List[str]
) -> Dict:
    """Link specific conversion actions to a campaign.

    By default, campaigns use ALL conversion actions in the account.
    Use this to limit a campaign to specific actions only.

    For campaign separation:
    - Day Tours campaign -> Day Tours conversion actions only
    - Multiday campaign -> Multiday conversion actions only

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        campaign_id: Campaign ID to link conversions to
        conversion_action_ids: List of conversion action IDs to link

    Returns:
        Dict with results:
            - campaign_id: Campaign ID
            - linked_actions: Number of actions linked
            - results: List of created goal resource names

    Raises:
        CampaignNotFoundError: If campaign doesn't exist
        APIError: For other API errors

    Example:
        >>> day_tour_conversions = ["7452944340", "7459612447", "7459612456"]
        >>> result = link_conversion_actions(
        ...     client,
        ...     "2425288235",
        ...     "12345678901",
        ...     day_tour_conversions
        ... )
        >>> print(f"Linked {result['linked_actions']} conversion actions")
        Linked 3 conversion actions
    """
    if not conversion_action_ids:
        raise ValidationError("At least one conversion_action_id is required")

    try:
        ccg_service = client.get_service("CampaignConversionGoalService")
        campaign_service = client.get_service("CampaignService")
        ca_service = client.get_service("ConversionActionService")

        campaign_resource = campaign_service.campaign_path(customer_id, str(campaign_id))

        operations = []

        for conv_id in conversion_action_ids:
            conv_resource = ca_service.conversion_action_path(customer_id, str(conv_id))

            op = client.get_type("CampaignConversionGoalOperation")
            goal = op.update

            # Resource name format: customers/{customer_id}/campaignConversionGoals/{campaign_id}~{conversion_action_id}
            goal.resource_name = f"customers/{customer_id}/campaignConversionGoals/{campaign_id}~{conv_id}"
            goal.biddable = True

            # Set update mask
            op.update_mask.paths.append("biddable")

            operations.append(op)

        # Execute operations
        response = ccg_service.mutate_campaign_conversion_goals(
            customer_id=customer_id,
            operations=operations
        )

        results = [result.resource_name for result in response.results]

        return {
            'campaign_id': campaign_id,
            'linked_actions': len(results),
            'results': results
        }

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        error_str = str(error.error_code) if error else ""

        if "NOT_FOUND" in error_str:
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
        elif "QUOTA_EXCEEDED" in error_str:
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to link conversion actions: {error.message if error else str(ex)}")


def get_device_performance(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str,
    date_range: str = "LAST_30_DAYS"
) -> List[Dict]:
    """Get performance metrics by device type.

    Useful for validating device bid adjustments are working correctly.
    For Day Tours, mobile should get 70%+ impressions after adjustments.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        campaign_id: Campaign ID
        date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, etc.)

    Returns:
        List of dicts with device performance:
            - device: Device type (MOBILE, DESKTOP, TABLET)
            - impressions: Impressions on this device
            - clicks: Clicks on this device
            - cost_micros: Cost on this device
            - conversions: Conversions on this device
            - impression_share: Percentage of total impressions

    Example:
        >>> perf = get_device_performance(client, "2425288235", "12345678901")
        >>> for p in perf:
        ...     print(f"{p['device']}: {p['impression_share']:.1f}% impressions")
        MOBILE: 72.5% impressions
        DESKTOP: 18.2% impressions
        TABLET: 9.3% impressions
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                segments.device,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        results = []
        total_impressions = 0

        # First pass: collect data and total impressions
        raw_results = []
        for row in response:
            device = row.segments.device.name
            impressions = row.metrics.impressions
            raw_results.append({
                'device': device,
                'impressions': impressions,
                'clicks': row.metrics.clicks,
                'cost_micros': row.metrics.cost_micros,
                'conversions': row.metrics.conversions,
            })
            total_impressions += impressions

        # Second pass: calculate shares
        for r in raw_results:
            r['impression_share'] = (r['impressions'] / total_impressions * 100) if total_impressions > 0 else 0
            results.append(r)

        return results

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        raise APIError(f"Failed to get device performance: {error.message if error else str(ex)}")


def bulk_update_attributions(
    client: GoogleAdsClient,
    customer_id: str,
    updates: List[Dict]
) -> List[Dict]:
    """Update attribution windows for multiple conversion actions.

    Efficient batch operation for updating many conversion actions at once.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        updates: List of dicts with:
            - conversion_action_id: Action ID to update
            - click_lookback_days: New click window (1-90)
            - view_lookback_days: New view window (1-30, optional)

    Returns:
        List of result dicts for each update

    Example:
        >>> updates = [
        ...     {"conversion_action_id": "7452944340", "click_lookback_days": 7},
        ...     {"conversion_action_id": "7452944343", "click_lookback_days": 90, "view_lookback_days": 30},
        ... ]
        >>> results = bulk_update_attributions(client, "2425288235", updates)
        >>> print(f"Updated {len(results)} conversion actions")
    """
    results = []

    for update in updates:
        conv_id = update['conversion_action_id']
        click_days = update['click_lookback_days']
        view_days = update.get('view_lookback_days', 1)

        try:
            result = update_conversion_attribution(
                client,
                customer_id,
                conv_id,
                click_lookback_days=click_days,
                view_lookback_days=view_days
            )
            result['status'] = 'success'
            results.append(result)
        except Exception as e:
            results.append({
                'conversion_action_id': conv_id,
                'status': 'error',
                'error': str(e)
            })

    return results
