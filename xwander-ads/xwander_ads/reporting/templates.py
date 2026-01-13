"""Pre-built GAQL query templates for common reports.

Provides ready-to-use query templates for campaign performance,
conversions, search terms, and other common reporting needs.
"""

from typing import Optional
from .gaql import GAQLBuilder


class QueryTemplates:
    """Collection of pre-built GAQL query templates."""

    @staticmethod
    def campaign_performance(
        days: int = 7,
        enabled_only: bool = True,
        limit: int = 50
    ) -> str:
        """Campaign performance report.

        Args:
            days: Number of days to report (default: 7)
            enabled_only: Only include enabled campaigns (default: True)
            limit: Maximum rows to return (default: 50)

        Returns:
            GAQL query string
        """
        builder = (
            GAQLBuilder()
            .select(
                'campaign.id',
                'campaign.name',
                'campaign.status',
                'campaign.advertising_channel_type',
                'metrics.impressions',
                'metrics.clicks',
                'metrics.ctr',
                'metrics.cost_micros',
                'metrics.conversions',
                'metrics.conversions_value',
                'metrics.cost_per_conversion',
                'metrics.average_cpc'
            )
            .from_resource('campaign')
            .during(f'LAST_{days}_DAYS')
            .order_by('metrics.cost_micros', desc=True)
            .limit(limit)
        )

        if enabled_only:
            builder.where('campaign.status = ENABLED')
        else:
            builder.where('campaign.status != REMOVED')

        return builder.build()

    @staticmethod
    def conversion_actions(customer_id: str) -> str:
        """List all conversion actions.

        Args:
            customer_id: Customer ID (for reference, not used in query)

        Returns:
            GAQL query string
        """
        return (
            GAQLBuilder()
            .select(
                'conversion_action.id',
                'conversion_action.name',
                'conversion_action.type',
                'conversion_action.category',
                'conversion_action.status',
                'conversion_action.include_in_conversions_metric'
            )
            .from_resource('conversion_action')
            .where('conversion_action.status != REMOVED')
            .order_by('conversion_action.name')
            .build()
        )

    @staticmethod
    def conversion_performance(
        days: int = 30,
        limit: int = 50
    ) -> str:
        """Conversion action performance.

        Args:
            days: Number of days to report (default: 30)
            limit: Maximum rows to return (default: 50)

        Returns:
            GAQL query string
        """
        return (
            GAQLBuilder()
            .select(
                'conversion_action.id',
                'conversion_action.name',
                'conversion_action.type',
                'conversion_action.category',
                'metrics.conversions',
                'metrics.conversions_value',
                'metrics.all_conversions',
                'metrics.all_conversions_value'
            )
            .from_resource('conversion_action')
            .during(f'LAST_{days}_DAYS')
            .where('conversion_action.status = ENABLED')
            .order_by('metrics.conversions', desc=True)
            .limit(limit)
            .build()
        )

    @staticmethod
    def search_terms(
        days: int = 14,
        campaign_id: Optional[str] = None,
        limit: int = 100
    ) -> str:
        """Search term report.

        Args:
            days: Number of days to report (default: 14)
            campaign_id: Filter by campaign ID (optional)
            limit: Maximum rows to return (default: 100)

        Returns:
            GAQL query string
        """
        builder = (
            GAQLBuilder()
            .select(
                'campaign.id',
                'campaign.name',
                'ad_group.id',
                'ad_group.name',
                'segments.search_term_match_type',
                'search_term_view.search_term',
                'search_term_view.status',
                'metrics.impressions',
                'metrics.clicks',
                'metrics.ctr',
                'metrics.cost_micros',
                'metrics.conversions'
            )
            .from_resource('search_term_view')
            .during(f'LAST_{days}_DAYS')
            .order_by('metrics.clicks', desc=True)
            .limit(limit)
        )

        if campaign_id:
            builder.where(f'campaign.id = {campaign_id}')

        return builder.build()

    @staticmethod
    def asset_group_performance(
        campaign_id: Optional[str] = None,
        days: int = 30,
        limit: int = 50
    ) -> str:
        """Asset group performance (Performance Max).

        Args:
            campaign_id: Filter by campaign ID (optional)
            days: Number of days to report (default: 30)
            limit: Maximum rows to return (default: 50)

        Returns:
            GAQL query string
        """
        builder = (
            GAQLBuilder()
            .select(
                'campaign.id',
                'campaign.name',
                'asset_group.id',
                'asset_group.name',
                'asset_group.status',
                'metrics.impressions',
                'metrics.clicks',
                'metrics.ctr',
                'metrics.cost_micros',
                'metrics.conversions',
                'metrics.conversions_value'
            )
            .from_resource('asset_group')
            .during(f'LAST_{days}_DAYS')
            .where('campaign.advertising_channel_type = PERFORMANCE_MAX')
            .order_by('metrics.cost_micros', desc=True)
            .limit(limit)
        )

        if campaign_id:
            builder.where(f'campaign.id = {campaign_id}')

        return builder.build()

    @staticmethod
    def pmax_insights(
        campaign_id: str,
        days: int = 30
    ) -> str:
        """Performance Max insights by asset group.

        Args:
            campaign_id: Campaign ID
            days: Number of days to report (default: 30)

        Returns:
            GAQL query string
        """
        return (
            GAQLBuilder()
            .select(
                'asset_group.id',
                'asset_group.name',
                'asset_group.status',
                'asset_group.final_urls',
                'metrics.impressions',
                'metrics.clicks',
                'metrics.ctr',
                'metrics.cost_micros',
                'metrics.conversions',
                'metrics.conversions_value',
                'metrics.cost_per_conversion'
            )
            .from_resource('asset_group')
            .where(f'campaign.id = {campaign_id}')
            .where('campaign.advertising_channel_type = PERFORMANCE_MAX')
            .during(f'LAST_{days}_DAYS')
            .order_by('metrics.cost_micros', desc=True)
            .build()
        )

    @staticmethod
    def ad_group_performance(
        campaign_id: Optional[str] = None,
        days: int = 30,
        limit: int = 50
    ) -> str:
        """Ad group performance report.

        Args:
            campaign_id: Filter by campaign ID (optional)
            days: Number of days to report (default: 30)
            limit: Maximum rows to return (default: 50)

        Returns:
            GAQL query string
        """
        builder = (
            GAQLBuilder()
            .select(
                'campaign.id',
                'campaign.name',
                'ad_group.id',
                'ad_group.name',
                'ad_group.status',
                'metrics.impressions',
                'metrics.clicks',
                'metrics.ctr',
                'metrics.cost_micros',
                'metrics.conversions',
                'metrics.average_cpc'
            )
            .from_resource('ad_group')
            .during(f'LAST_{days}_DAYS')
            .where('ad_group.status != REMOVED')
            .order_by('metrics.cost_micros', desc=True)
            .limit(limit)
        )

        if campaign_id:
            builder.where(f'campaign.id = {campaign_id}')

        return builder.build()

    @staticmethod
    def keyword_performance(
        campaign_id: Optional[str] = None,
        ad_group_id: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> str:
        """Keyword performance report.

        Args:
            campaign_id: Filter by campaign ID (optional)
            ad_group_id: Filter by ad group ID (optional)
            days: Number of days to report (default: 30)
            limit: Maximum rows to return (default: 100)

        Returns:
            GAQL query string
        """
        builder = (
            GAQLBuilder()
            .select(
                'campaign.id',
                'campaign.name',
                'ad_group.id',
                'ad_group.name',
                'ad_group_criterion.keyword.text',
                'ad_group_criterion.keyword.match_type',
                'ad_group_criterion.status',
                'metrics.impressions',
                'metrics.clicks',
                'metrics.ctr',
                'metrics.cost_micros',
                'metrics.conversions',
                'metrics.average_cpc'
            )
            .from_resource('keyword_view')
            .during(f'LAST_{days}_DAYS')
            .where('ad_group_criterion.status != REMOVED')
            .order_by('metrics.clicks', desc=True)
            .limit(limit)
        )

        if campaign_id:
            builder.where(f'campaign.id = {campaign_id}')

        if ad_group_id:
            builder.where(f'ad_group.id = {ad_group_id}')

        return builder.build()

    @staticmethod
    def geographic_performance(
        days: int = 30,
        limit: int = 50
    ) -> str:
        """Geographic performance report.

        Args:
            days: Number of days to report (default: 30)
            limit: Maximum rows to return (default: 50)

        Returns:
            GAQL query string
        """
        return (
            GAQLBuilder()
            .select(
                'campaign.id',
                'campaign.name',
                'geographic_view.country_criterion_id',
                'geographic_view.location_type',
                'metrics.impressions',
                'metrics.clicks',
                'metrics.ctr',
                'metrics.cost_micros',
                'metrics.conversions'
            )
            .from_resource('geographic_view')
            .during(f'LAST_{days}_DAYS')
            .where('campaign.status = ENABLED')
            .order_by('metrics.clicks', desc=True)
            .limit(limit)
            .build()
        )

    @staticmethod
    def audience_performance(
        days: int = 30,
        limit: int = 50
    ) -> str:
        """Audience performance report.

        Args:
            days: Number of days to report (default: 30)
            limit: Maximum rows to return (default: 50)

        Returns:
            GAQL query string
        """
        return (
            GAQLBuilder()
            .select(
                'campaign.id',
                'campaign.name',
                'ad_group.id',
                'ad_group.name',
                'ad_group_criterion.user_list.name',
                'metrics.impressions',
                'metrics.clicks',
                'metrics.ctr',
                'metrics.cost_micros',
                'metrics.conversions'
            )
            .from_resource('user_list_view')
            .during(f'LAST_{days}_DAYS')
            .order_by('metrics.clicks', desc=True)
            .limit(limit)
            .build()
        )


# Convenience shortcuts
templates = QueryTemplates()
