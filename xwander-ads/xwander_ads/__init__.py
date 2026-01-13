"""xwander-ads: Google Ads API integration plugin.

This plugin provides comprehensive Google Ads management functionality
including Performance Max campaigns, audiences, conversions, and reporting.

Modules:
    - auth: Authentication and client management
    - pmax: Performance Max campaign operations
    - conversions: Conversion tracking management
    - audiences: Audience management
    - reporting: GAQL queries and reporting

Usage:
    from xwander_ads import get_client, pmax

    client = get_client()
    campaigns = pmax.list_campaigns(client, "2425288235")
"""

__version__ = "1.1.0"
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
