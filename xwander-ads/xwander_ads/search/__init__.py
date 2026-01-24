"""Search campaigns module for xwander-ads plugin.

This module provides comprehensive management of Google Ads Search campaigns
with advanced targeting features for Day Tours and Multiday packages.

Key Features:
    - Search campaign creation with LOCATION_OF_PRESENCE targeting
    - Device bid adjustments (+50% mobile, -30% desktop)
    - Attribution window management (7 days Day Tours, 90 days Multiday)
    - Campaign conversion goal linking
    - Ad group management (create, list, get, bulk operations)

Use Cases:
    - Day Tours: Target tourists physically in Finland with mobile-optimized bids
    - Multiday: Target source markets (FR, ES, UK) with longer attribution

Example:
    >>> from xwander_ads import get_client
    >>> from xwander_ads.search import (
    ...     create_search_campaign,
    ...     set_device_bid_adjustments,
    ...     create_ad_group
    ... )
    >>>
    >>> client = get_client()
    >>>
    >>> # Create Day Tours campaign
    >>> campaign = create_search_campaign(
    ...     client,
    ...     "2425288235",
    ...     "Search | Day Tours | Ivalo",
    ...     daily_budget_eur=50.0,
    ...     target_cpa_eur=40.0,
    ...     geo_target_type="LOCATION_OF_PRESENCE",
    ...     geo_targets=["FINLAND"],
    ...     languages=["ENGLISH", "FRENCH", "GERMAN"]
    ... )
    >>>
    >>> # Set device bid adjustments
    >>> set_device_bid_adjustments(
    ...     client,
    ...     "2425288235",
    ...     campaign['campaign_id'],
    ...     mobile_modifier=1.5,   # +50%
    ...     desktop_modifier=0.7   # -30%
    ... )
    >>>
    >>> # Create ad group
    >>> ad_group = create_ad_group(
    ...     client,
    ...     "2425288235",
    ...     campaign['campaign_id'],
    ...     "Northern Lights | Ivalo",
    ...     cpc_bid_eur=1.50
    ... )
"""

from .campaigns import (
    create_search_campaign,
    get_search_campaign,
    list_search_campaigns,
    get_campaign_criteria,
    GEO_TARGETS,
    LANGUAGE_CONSTANTS,
    TOURIST_LANGUAGES,
)

from .adjustments import (
    set_device_bid_adjustments,
    update_conversion_attribution,
    link_conversion_actions,
    get_device_performance,
    bulk_update_attributions,
    DEVICE_TYPES,
    DAY_TOURS_DEVICE_MODIFIERS,
    MULTIDAY_DEVICE_MODIFIERS,
)

from .ad_groups import (
    create_ad_group,
    list_ad_groups,
    get_ad_group,
    bulk_create_ad_groups,
    AdGroupNotFoundError,
)

from .rsa import (
    create_rsa,
    list_rsas,
    get_rsa,
    bulk_create_rsas,
    validate_rsa_config,
    RSA_VALIDATION,
)

# Convenient alias for attribution updates
update_attribution_window = update_conversion_attribution

__all__ = [
    # Campaign operations
    'create_search_campaign',
    'get_search_campaign',
    'list_search_campaigns',
    'get_campaign_criteria',

    # Adjustment operations
    'set_device_bid_adjustments',
    'update_conversion_attribution',
    'update_attribution_window',  # alias for update_conversion_attribution
    'link_conversion_actions',
    'get_device_performance',
    'bulk_update_attributions',

    # Ad group operations
    'create_ad_group',
    'list_ad_groups',
    'get_ad_group',
    'bulk_create_ad_groups',
    'AdGroupNotFoundError',

    # RSA operations
    'create_rsa',
    'list_rsas',
    'get_rsa',
    'bulk_create_rsas',
    'validate_rsa_config',

    # Constants
    'GEO_TARGETS',
    'LANGUAGE_CONSTANTS',
    'TOURIST_LANGUAGES',
    'DEVICE_TYPES',
    'DAY_TOURS_DEVICE_MODIFIERS',
    'MULTIDAY_DEVICE_MODIFIERS',
    'RSA_VALIDATION',
]
