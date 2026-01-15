"""Search campaign management.

This module handles CRUD operations for Search campaigns with advanced
targeting features including LOCATION_OF_PRESENCE geo-targeting for
Day Tours (tourists physically in Finland).

Key Features:
    - Create Search campaigns with geo-targeting options
    - LOCATION_OF_PRESENCE for in-destination targeting
    - Language targeting for tourist audiences
    - Network settings (Search + Partners, no Display)
    - Bidding strategies (Target CPA, Maximize Conversions)

API Version: v22 (google-ads-python 28.4.1)
"""

from typing import List, Dict, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import CampaignNotFoundError, APIError, QuotaExceededError, ValidationError


# Common geo target constants
GEO_TARGETS = {
    'FINLAND': 'geoTargetConstants/2246',
    'FRANCE': 'geoTargetConstants/2250',
    'SPAIN': 'geoTargetConstants/2724',
    'UNITED_KINGDOM': 'geoTargetConstants/2826',
    'GERMANY': 'geoTargetConstants/2276',
    'ITALY': 'geoTargetConstants/2380',
    'NETHERLANDS': 'geoTargetConstants/2528',
}

# Common language constants
LANGUAGE_CONSTANTS = {
    'ENGLISH': 1000,
    'GERMAN': 1001,
    'FRENCH': 1002,
    'SPANISH': 1003,
    'ITALIAN': 1004,
    'DUTCH': 1010,
    'FINNISH': 1011,
}

# Tourist languages commonly used for Day Tours
TOURIST_LANGUAGES = ['ENGLISH', 'FRENCH', 'SPANISH', 'GERMAN', 'ITALIAN']


def create_search_campaign(
    client: GoogleAdsClient,
    customer_id: str,
    name: str,
    daily_budget_eur: float,
    target_cpa_eur: Optional[float] = None,
    geo_target_type: str = "LOCATION_OF_PRESENCE",
    geo_targets: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
    status: str = "PAUSED"
) -> Dict:
    """Create a Search campaign with advanced geo-targeting.

    Creates a complete Search campaign including budget, geo targets,
    language targets, and network settings. Uses batch mutate for
    efficiency.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens, e.g., "2425288235")
        name: Campaign name (e.g., "Search | Day Tours | Ivalo")
        daily_budget_eur: Daily budget in EUR (e.g., 50.0)
        target_cpa_eur: Optional target CPA in EUR. If provided, uses
            Maximize Conversions with Target CPA. Otherwise uses
            Maximize Conversions without target.
        geo_target_type: Geo targeting type:
            - "LOCATION_OF_PRESENCE" (recommended for Day Tours - people IN location)
            - "AREA_OF_INTEREST" (people interested in location)
            - "PRESENCE_OR_INTEREST" (both - not recommended)
        geo_targets: List of geo target constants. Defaults to Finland.
            Use GEO_TARGETS dict keys or full resource names.
            Example: ["FINLAND"] or ["geoTargetConstants/2246"]
        languages: List of language names or IDs. Defaults to tourist languages.
            Use LANGUAGE_CONSTANTS dict keys or integer IDs.
            Example: ["ENGLISH", "FRENCH"] or [1000, 1002]
        status: Campaign status: "PAUSED" (default, safe) or "ENABLED"

    Returns:
        Dict with campaign details:
            - resource_name: Full resource name
            - campaign_id: Campaign ID
            - budget_id: Budget ID
            - name: Campaign name
            - url: Direct link to Google Ads UI

    Raises:
        ValidationError: If parameters are invalid
        APIError: For API errors
        QuotaExceededError: If API quota exceeded

    Example:
        >>> client = get_client()
        >>> result = create_search_campaign(
        ...     client,
        ...     "2425288235",
        ...     "Search | Day Tours | Ivalo",
        ...     daily_budget_eur=50.0,
        ...     target_cpa_eur=40.0,
        ...     geo_target_type="LOCATION_OF_PRESENCE",
        ...     geo_targets=["FINLAND"],
        ...     languages=["ENGLISH", "FRENCH", "GERMAN"],
        ...     status="PAUSED"
        ... )
        >>> print(f"Campaign created: {result['campaign_id']}")
        Campaign created: 12345678901
    """
    # Validate inputs
    if not name or not name.strip():
        raise ValidationError("Campaign name is required")
    if daily_budget_eur <= 0:
        raise ValidationError("Daily budget must be positive")
    if target_cpa_eur is not None and target_cpa_eur <= 0:
        raise ValidationError("Target CPA must be positive")

    # Resolve geo targets
    resolved_geo_targets = _resolve_geo_targets(geo_targets)

    # Resolve language targets
    resolved_languages = _resolve_languages(languages)

    # Validate geo target type
    valid_geo_types = {
        "LOCATION_OF_PRESENCE",
        "AREA_OF_INTEREST",
        "PRESENCE_OR_INTEREST",
    }
    if geo_target_type not in valid_geo_types:
        raise ValidationError(
            f"Invalid geo_target_type: {geo_target_type}. "
            f"Must be one of: {list(valid_geo_types)}"
        )

    try:
        mutate_service = client.get_service("GoogleAdsService")
        budget_service = client.get_service("CampaignBudgetService")
        campaign_service = client.get_service("CampaignService")
        bidding_strategy_service = client.get_service("BiddingStrategyService")

        # If Target CPA is specified, create portfolio bidding strategy FIRST
        # (must be done separately, cannot use temp IDs in batch)
        bidding_strategy_resource = None
        if target_cpa_eur is not None:
            bidding_strategy_operation = client.get_type("BiddingStrategyOperation")
            bidding_strategy = bidding_strategy_operation.create
            bidding_strategy.name = f"{name} - Target CPA €{int(target_cpa_eur)}"
            bidding_strategy.target_cpa.target_cpa_micros = int(target_cpa_eur * 1_000_000)

            bidding_response = bidding_strategy_service.mutate_bidding_strategies(
                customer_id=customer_id,
                operations=[bidding_strategy_operation]
            )
            bidding_strategy_resource = bidding_response.results[0].resource_name

        operations = []

        # Operation 1: Create Campaign Budget
        budget_op = client.get_type("MutateOperation")
        budget = budget_op.campaign_budget_operation.create
        budget.resource_name = budget_service.campaign_budget_path(customer_id, "-1")
        budget.name = f"{name} Budget"
        budget.amount_micros = int(daily_budget_eur * 1_000_000)
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget.explicitly_shared = False
        operations.append(budget_op)

        # Operation 2: Create Search Campaign
        # Pattern from working script: create_search_campaign_complete.py
        campaign_op = client.get_type("MutateOperation")
        campaign = campaign_op.campaign_operation.create
        campaign.resource_name = campaign_service.campaign_path(customer_id, "-2")
        campaign.name = name
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
        campaign.campaign_budget = budget_service.campaign_budget_path(customer_id, "-1")

        # Status
        if status.upper() == "ENABLED":
            campaign.status = client.enums.CampaignStatusEnum.ENABLED
        else:
            campaign.status = client.enums.CampaignStatusEnum.PAUSED

        # CRITICAL: Set geo targeting type using PositiveGeoTargetTypeEnum
        # (verified from working production campaigns)
        if geo_target_type == "LOCATION_OF_PRESENCE":
            campaign.geo_target_type_setting.positive_geo_target_type = (
                client.enums.PositiveGeoTargetTypeEnum.PRESENCE  # Value: 7
            )
        elif geo_target_type == "AREA_OF_INTEREST":
            campaign.geo_target_type_setting.positive_geo_target_type = (
                client.enums.PositiveGeoTargetTypeEnum.SEARCH_INTEREST  # Value: 6
            )
        else:  # PRESENCE_OR_INTEREST
            campaign.geo_target_type_setting.positive_geo_target_type = (
                client.enums.PositiveGeoTargetTypeEnum.PRESENCE_OR_INTEREST  # Value: 5
            )

        # Bidding Strategy: Manual CPC or Portfolio Target CPA
        # Target CPA requires a portfolio bidding strategy (created above)
        if bidding_strategy_resource is not None:
            # Use portfolio bidding strategy for Target CPA
            campaign.bidding_strategy = bidding_strategy_resource
        else:
            # Manual CPC with enhanced CPC (simple, works without conversion history)
            campaign.manual_cpc.enhanced_cpc_enabled = True

        # Network Settings (verified from working script)
        campaign.network_settings.target_google_search = True
        campaign.network_settings.target_search_network = True
        campaign.network_settings.target_content_network = False
        campaign.network_settings.target_partner_search_network = False

        # EU advertising compliance (required field for EU accounts) - MUST be enum!
        campaign.contains_eu_political_advertising = (
            client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
        )

        operations.append(campaign_op)

        # Operations 3+: Add Geo Targets
        for geo_target in resolved_geo_targets:
            geo_op = client.get_type("MutateOperation")
            criterion = geo_op.campaign_criterion_operation.create
            criterion.campaign = campaign_service.campaign_path(customer_id, "-2")
            criterion.location.geo_target_constant = geo_target
            criterion.negative = False
            operations.append(geo_op)

        # Operations N+: Add Languages
        for lang_id in resolved_languages:
            lang_op = client.get_type("MutateOperation")
            criterion = lang_op.campaign_criterion_operation.create
            criterion.campaign = campaign_service.campaign_path(customer_id, "-2")
            criterion.language.language_constant = f"languageConstants/{lang_id}"
            operations.append(lang_op)

        # Execute batch operation
        response = mutate_service.mutate(
            customer_id=customer_id,
            mutate_operations=operations
        )

        # Extract results
        budget_resource = response.mutate_operation_responses[0].campaign_budget_result.resource_name
        campaign_resource = response.mutate_operation_responses[1].campaign_result.resource_name

        budget_id = budget_resource.split("/")[-1]
        campaign_id = campaign_resource.split("/")[-1]

        result = {
            'resource_name': campaign_resource,
            'campaign_id': campaign_id,
            'budget_id': budget_id,
            'budget_resource': budget_resource,
            'name': name,
            'status': status.upper(),
            'daily_budget_eur': daily_budget_eur,
            'target_cpa_eur': target_cpa_eur,
            'geo_target_type': geo_target_type,
            'url': f"https://ads.google.com/aw/overview?campaignId={campaign_id}&__e={customer_id}"
        }

        # Include bidding strategy info if portfolio strategy was created
        if bidding_strategy_resource is not None:
            result['bidding_strategy_resource'] = bidding_strategy_resource
            result['bidding_strategy_id'] = bidding_strategy_resource.split("/")[-1]
            result['bidding_type'] = 'TARGET_CPA'
        else:
            result['bidding_type'] = 'MANUAL_CPC'

        return result

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "QUOTA_EXCEEDED" in str(error.error_code):
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to create campaign: {error.message if error else str(ex)}")


def get_search_campaign(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str
) -> Dict:
    """Get details for a specific Search campaign.

    Retrieves comprehensive campaign information including budget,
    bidding strategy, geo targeting settings, and performance metrics.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        campaign_id: Campaign ID

    Returns:
        Dict with campaign details:
            - id: Campaign ID
            - name: Campaign name
            - status: ENABLED, PAUSED, or REMOVED
            - budget_micros: Daily budget in micros
            - target_cpa_micros: Target CPA (if set)
            - geo_target_type: Geo targeting type setting
            - cost_micros: Total cost
            - impressions: Total impressions
            - clicks: Total clicks
            - conversions: Total conversions
            - resource_name: Full resource name

    Raises:
        CampaignNotFoundError: If campaign doesn't exist
        APIError: For other API errors

    Example:
        >>> campaign = get_search_campaign(client, "2425288235", "12345678901")
        >>> print(f"{campaign['name']}: {campaign['status']}")
        Search | Day Tours: ENABLED
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
                campaign.maximize_conversions.target_cpa_micros,
                campaign.geo_target_type_setting.positive_geo_target_type,
                campaign.network_settings.target_google_search,
                campaign.network_settings.target_search_network,
                campaign.network_settings.target_content_network,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND campaign.advertising_channel_type = 'SEARCH'
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            return {
                'id': row.campaign.id,
                'name': row.campaign.name,
                'status': row.campaign.status.name,
                'channel_type': row.campaign.advertising_channel_type.name,
                'budget_id': row.campaign_budget.id if row.campaign_budget else None,
                'budget_micros': row.campaign_budget.amount_micros if row.campaign_budget else 0,
                'target_cpa_micros': row.campaign.maximize_conversions.target_cpa_micros,
                'geo_target_type': row.campaign.geo_target_type_setting.positive_geo_target_type.name,
                'target_google_search': row.campaign.network_settings.target_google_search,
                'target_search_network': row.campaign.network_settings.target_search_network,
                'target_content_network': row.campaign.network_settings.target_content_network,
                'cost_micros': row.metrics.cost_micros,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'conversions': row.metrics.conversions,
                'conversions_value': row.metrics.conversions_value,
                'resource_name': f"customers/{customer_id}/campaigns/{row.campaign.id}"
            }

        raise CampaignNotFoundError(f"Search campaign {campaign_id} not found for customer {customer_id}")

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "NOT_FOUND" in str(error.error_code):
            raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
        else:
            raise APIError(f"Failed to get campaign: {error.message if error else str(ex)}")


def list_search_campaigns(
    client: GoogleAdsClient,
    customer_id: str,
    enabled_only: bool = False,
    limit: int = 50
) -> List[Dict]:
    """List all Search campaigns.

    Retrieves Search campaigns with performance metrics and settings.
    Useful for auditing and reporting.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        enabled_only: If True, only return enabled campaigns
        limit: Maximum campaigns to return (default: 50, max: 10000)

    Returns:
        List of dicts with campaign details including:
            - id: Campaign ID
            - name: Campaign name
            - status: Campaign status
            - budget_micros: Daily budget
            - geo_target_type: Geo targeting type
            - cost_micros: Total spend
            - impressions, clicks, conversions: Metrics

    Raises:
        APIError: For API errors

    Example:
        >>> campaigns = list_search_campaigns(client, "2425288235")
        >>> for c in campaigns:
        ...     print(f"{c['name']}: {c['status']}")
        Search | Day Tours: ENABLED
        Search | Other: PAUSED
    """
    # Validate limit
    limit = min(max(1, limit), 10000)

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
                campaign.maximize_conversions.target_cpa_micros,
                campaign.geo_target_type_setting.positive_geo_target_type,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE campaign.advertising_channel_type = 'SEARCH'
            {status_filter}
            ORDER BY campaign.name
            LIMIT {limit}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        campaigns = []
        for row in response:
            campaigns.append({
                'id': row.campaign.id,
                'name': row.campaign.name,
                'status': row.campaign.status.name,
                'budget_micros': row.campaign_budget.amount_micros if row.campaign_budget else 0,
                'target_cpa_micros': row.campaign.maximize_conversions.target_cpa_micros,
                'geo_target_type': row.campaign.geo_target_type_setting.positive_geo_target_type.name,
                'cost_micros': row.metrics.cost_micros,
                'impressions': row.metrics.impressions,
                'clicks': row.metrics.clicks,
                'conversions': row.metrics.conversions,
                'conversions_value': row.metrics.conversions_value,
                'resource_name': f"customers/{customer_id}/campaigns/{row.campaign.id}"
            })

        return campaigns

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "QUOTA_EXCEEDED" in str(error.error_code):
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to list campaigns: {error.message if error else str(ex)}")


def get_campaign_criteria(
    client: GoogleAdsClient,
    customer_id: str,
    campaign_id: str
) -> Dict:
    """Get campaign targeting criteria (geo, language, device).

    Retrieves all targeting criteria for a campaign including
    geo targets, language targets, and device bid modifiers.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        campaign_id: Campaign ID

    Returns:
        Dict with targeting details:
            - geo_targets: List of geo target locations
            - languages: List of language targets
            - device_modifiers: Dict of device bid modifiers

    Raises:
        CampaignNotFoundError: If campaign doesn't exist
        APIError: For other API errors
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign_criterion.campaign,
                campaign_criterion.criterion_id,
                campaign_criterion.type,
                campaign_criterion.location.geo_target_constant,
                campaign_criterion.language.language_constant,
                campaign_criterion.device.type,
                campaign_criterion.bid_modifier,
                campaign_criterion.negative
            FROM campaign_criterion
            WHERE campaign.id = {campaign_id}
            LIMIT 100
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        geo_targets = []
        languages = []
        device_modifiers = {}

        for row in response:
            criterion = row.campaign_criterion
            criterion_type = criterion.type_.name

            if criterion_type == "LOCATION":
                geo_targets.append({
                    'id': criterion.criterion_id,
                    'geo_constant': criterion.location.geo_target_constant,
                    'negative': criterion.negative
                })
            elif criterion_type == "LANGUAGE":
                languages.append({
                    'id': criterion.criterion_id,
                    'language_constant': criterion.language.language_constant
                })
            elif criterion_type == "DEVICE":
                device_type = criterion.device.type_.name
                device_modifiers[device_type] = {
                    'id': criterion.criterion_id,
                    'bid_modifier': criterion.bid_modifier
                }

        return {
            'campaign_id': campaign_id,
            'geo_targets': geo_targets,
            'languages': languages,
            'device_modifiers': device_modifiers
        }

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        raise APIError(f"Failed to get campaign criteria: {error.message if error else str(ex)}")


def _resolve_geo_targets(geo_targets: Optional[List[str]]) -> List[str]:
    """Resolve geo target names to resource names.

    Args:
        geo_targets: List of geo target names or resource names

    Returns:
        List of geo target resource names
    """
    if geo_targets is None:
        return [GEO_TARGETS['FINLAND']]

    resolved = []
    for target in geo_targets:
        if target.upper() in GEO_TARGETS:
            resolved.append(GEO_TARGETS[target.upper()])
        elif target.startswith('geoTargetConstants/'):
            resolved.append(target)
        else:
            # Assume it's a numeric ID
            resolved.append(f"geoTargetConstants/{target}")

    return resolved


def _resolve_languages(languages: Optional[List]) -> List[int]:
    """Resolve language names to IDs.

    Args:
        languages: List of language names or IDs

    Returns:
        List of language IDs
    """
    if languages is None:
        return [LANGUAGE_CONSTANTS[lang] for lang in TOURIST_LANGUAGES]

    resolved = []
    for lang in languages:
        if isinstance(lang, int):
            resolved.append(lang)
        elif isinstance(lang, str):
            if lang.upper() in LANGUAGE_CONSTANTS:
                resolved.append(LANGUAGE_CONSTANTS[lang.upper()])
            elif lang.isdigit():
                resolved.append(int(lang))
            else:
                raise ValidationError(f"Unknown language: {lang}")

    return resolved
