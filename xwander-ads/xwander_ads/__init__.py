"""xwander-ads: Google Ads API integration plugin.

This plugin provides comprehensive Google Ads management functionality
including Performance Max campaigns, audiences, conversions, recommendations,
and reporting.

Modules:
    - auth: Authentication and client management
    - pmax: Performance Max campaign operations
    - conversions: Conversion tracking management
    - audiences: Audience management
    - recommendations: Recommendation analysis and tracking
    - reporting: GAQL queries and reporting

Usage:
    from xwander_ads import get_client, pmax, recommendations

    client = get_client()
    campaigns = pmax.list_campaigns(client, "2425288235")
    recs = recommendations.fetch_recommendations(client, "2425288235")
"""

__version__ = "1.2.0"
__author__ = "Xwander Platform"

from .auth import get_client, test_auth
from .exceptions import (
    AdsError,
    AuthenticationError,
    AssetGroupNotFoundError,
    CampaignNotFoundError,
    DuplicateSignalError,
    QuotaExceededError,
    InvalidResourceError,
    BudgetError,
    ValidationError,
    APIError
)

__all__ = [
    # Version
    '__version__',
    '__author__',
    # Auth
    'get_client',
    'test_auth',
    # Exceptions
    'AdsError',
    'AuthenticationError',
    'AssetGroupNotFoundError',
    'CampaignNotFoundError',
    'DuplicateSignalError',
    'QuotaExceededError',
    'InvalidResourceError',
    'BudgetError',
    'ValidationError',
    'APIError',
]
