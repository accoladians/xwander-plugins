"""Performance Max module for xwander-ads plugin.

This module provides comprehensive management of Google Ads Performance Max campaigns,
including asset groups, signals, assets, and budgets.
"""

from .campaigns import (
    list_campaigns,
    get_campaign,
    list_asset_groups,
    get_campaign_stats
)

from .signals import (
    list_signals,
    add_search_theme,
    bulk_add_themes,
    remove_signal,
    get_signal_stats
)

__all__ = [
    # Campaigns
    'list_campaigns',
    'get_campaign',
    'list_asset_groups',
    'get_campaign_stats',
    # Signals
    'list_signals',
    'add_search_theme',
    'bulk_add_themes',
    'remove_signal',
    'get_signal_stats',
]
