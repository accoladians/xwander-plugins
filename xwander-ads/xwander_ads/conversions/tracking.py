"""
Conversion Tracking Setup and Validation

Provides utilities for:
- Validating conversion tracking setup
- Checking GTM integration
- Diagnosing conversion issues
- Generating tracking recommendations
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import GoogleAdsError

logger = logging.getLogger(__name__)


class ConversionTracker:
    """Conversion tracking validation and diagnostics"""

    def __init__(self, client: GoogleAdsClient):
        """
        Initialize the conversion tracker.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client
        self._ga_service = client.get_service("GoogleAdsService")

    def check_conversion_health(
        self,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Check conversion tracking health for an account.

        Args:
            customer_id: Google Ads customer ID
            days: Days to analyze (default: 30)

        Returns:
            Dict with health assessment and issues

        Example:
            >>> tracker = ConversionTracker(client)
            >>> health = tracker.check_conversion_health("2425288235")
            >>> print(f"Health score: {health['score']}/100")
            >>> for issue in health['issues']:
            ...     print(f"- {issue['severity']}: {issue['message']}")
        """
        # Get all conversion actions
        query_actions = """
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.type,
                conversion_action.category,
                conversion_action.status,
                conversion_action.primary_for_goal
            FROM conversion_action
            WHERE conversion_action.status IN ('ENABLED', 'PAUSED')
        """

        try:
            actions_response = self._ga_service.search(customer_id=customer_id, query=query_actions)

            conversions = []
            for row in actions_response:
                conv = row.conversion_action
                conversions.append({
                    'id': conv.id,
                    'name': conv.name,
                    'type': conv.type_.name,
                    'category': conv.category.name,
                    'status': conv.status.name,
                    'primary': conv.primary_for_goal
                })

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            raise GoogleAdsError(f"Failed to fetch conversion actions: {error_msg}")

        # Get conversion performance
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query_performance = f"""
            SELECT
                conversion_action.id,
                conversion_action.name,
                metrics.conversions,
                metrics.all_conversions,
                metrics.conversions_value
            FROM conversion_action
            WHERE segments.date >= '{start_date.strftime('%Y-%m-%d')}'
              AND segments.date <= '{end_date.strftime('%Y-%m-%d')}'
              AND conversion_action.status IN ('ENABLED', 'PAUSED')
        """

        try:
            perf_response = self._ga_service.search(customer_id=customer_id, query=query_performance)

            # Aggregate conversions by action
            performance = {}
            for row in perf_response:
                conv_id = row.conversion_action.id
                if conv_id not in performance:
                    performance[conv_id] = {
                        'conversions': 0,
                        'all_conversions': 0,
                        'value': 0
                    }

                performance[conv_id]['conversions'] += row.metrics.conversions
                performance[conv_id]['all_conversions'] += row.metrics.all_conversions
                performance[conv_id]['value'] += row.metrics.conversions_value

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            logger.warning(f"Failed to fetch conversion performance: {error_msg}")
            performance = {}

        # Analyze health
        issues = []
        warnings = []

        total_conversions = len(conversions)
        enabled_conversions = [c for c in conversions if c['status'] == 'ENABLED']
        enabled_count = len(enabled_conversions)

        # Check if any conversions are configured
        if total_conversions == 0:
            issues.append({
                'severity': 'CRITICAL',
                'message': 'No conversion actions configured',
                'recommendation': 'Create conversion actions for key user actions'
            })

        # Check enabled conversions
        if enabled_count == 0 and total_conversions > 0:
            issues.append({
                'severity': 'CRITICAL',
                'message': 'All conversion actions are paused',
                'recommendation': 'Enable at least one conversion action'
            })

        # Check conversion activity
        active_conversions = 0
        inactive_conversions = []

        for conv in enabled_conversions:
            conv_id = conv['id']
            perf = performance.get(conv_id, {})

            if perf.get('conversions', 0) > 0:
                active_conversions += 1
            else:
                inactive_conversions.append(conv['name'])

        if enabled_count > 0:
            activity_rate = (active_conversions / enabled_count) * 100

            if activity_rate < 25:
                issues.append({
                    'severity': 'CRITICAL',
                    'message': f'Only {activity_rate:.0f}% of enabled conversions receiving data',
                    'inactive_count': len(inactive_conversions),
                    'inactive_conversions': inactive_conversions[:5],  # Show first 5
                    'recommendation': 'Debug conversion tracking setup (GTM, analytics)'
                })
            elif activity_rate < 50:
                warnings.append({
                    'severity': 'WARNING',
                    'message': f'{activity_rate:.0f}% of enabled conversions receiving data',
                    'inactive_count': len(inactive_conversions),
                    'recommendation': 'Review inactive conversion actions'
                })

        # Check primary for goal settings
        primary_count = sum(1 for c in enabled_conversions if c['primary'])
        if enabled_count > 0 and primary_count == 0:
            warnings.append({
                'severity': 'WARNING',
                'message': 'No conversions set as primary for goals',
                'recommendation': 'Set important conversions as primary for Smart Bidding'
            })

        # Calculate health score
        score = 100

        # Deduct for critical issues
        score -= len([i for i in issues if i['severity'] == 'CRITICAL']) * 30

        # Deduct for low activity rate
        if enabled_count > 0:
            score -= max(0, (50 - activity_rate))

        # Deduct for warnings
        score -= len(warnings) * 5

        score = max(0, min(100, score))

        return {
            'score': int(score),
            'status': self._get_health_status(score),
            'summary': {
                'total_conversions': total_conversions,
                'enabled_conversions': enabled_count,
                'active_conversions': active_conversions,
                'activity_rate': f"{activity_rate:.0f}%" if enabled_count > 0 else "N/A",
                'total_conversions_last_30d': sum(
                    p.get('conversions', 0) for p in performance.values()
                ),
                'total_value_last_30d': sum(
                    p.get('value', 0) for p in performance.values()
                )
            },
            'issues': issues,
            'warnings': warnings,
            'conversions': conversions,
            'performance': performance
        }

    def diagnose_conversion(
        self,
        customer_id: str,
        conversion_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Diagnose a specific conversion action.

        Args:
            customer_id: Google Ads customer ID
            conversion_id: Conversion action ID
            days: Days to analyze

        Returns:
            Dict with diagnostic information and recommendations
        """
        # Get conversion action details
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
            WHERE conversion_action.id = {conversion_id}
        """

        try:
            response = self._ga_service.search(customer_id=customer_id, query=query)
            conv_row = next(iter(response), None)

            if not conv_row:
                raise GoogleAdsError(f"Conversion action {conversion_id} not found")

            conv = conv_row.conversion_action

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            raise GoogleAdsError(f"Failed to fetch conversion action: {error_msg}")

        # Get performance
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query_perf = f"""
            SELECT
                segments.date,
                metrics.conversions,
                metrics.conversions_value,
                metrics.view_through_conversions
            FROM conversion_action
            WHERE conversion_action.id = {conversion_id}
              AND segments.date >= '{start_date.strftime('%Y-%m-%d')}'
              AND segments.date <= '{end_date.strftime('%Y-%m-%d')}'
            ORDER BY segments.date DESC
        """

        try:
            perf_response = self._ga_service.search(customer_id=customer_id, query=query_perf)

            daily_conversions = []
            total_conversions = 0
            total_value = 0

            for row in perf_response:
                daily_conversions.append({
                    'date': row.segments.date,
                    'conversions': row.metrics.conversions,
                    'value': row.metrics.conversions_value,
                    'view_through': row.metrics.view_through_conversions
                })
                total_conversions += row.metrics.conversions
                total_value += row.metrics.conversions_value

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            logger.warning(f"Failed to fetch conversion performance: {error_msg}")
            daily_conversions = []
            total_conversions = 0
            total_value = 0

        # Diagnose issues
        issues = []
        recommendations = []

        # Status check
        if conv.status.name != 'ENABLED':
            issues.append(f"Conversion is {conv.status.name}")
            recommendations.append("Enable the conversion action")

        # Activity check
        if conv.status.name == 'ENABLED' and total_conversions == 0:
            issues.append(f"No conversions in last {days} days")

            if conv.type_.name == 'WEBPAGE':
                recommendations.append(
                    "Check GTM tag configuration and firing triggers"
                )
                recommendations.append(
                    "Verify conversion tracking tag is on the correct pages"
                )
                recommendations.append(
                    "Test in GTM Preview mode to confirm tag fires"
                )
            elif conv.type_.name == 'UPLOAD_CLICKS':
                recommendations.append(
                    "Check offline conversion sync is running"
                )
                recommendations.append(
                    "Verify GCLID capture is working"
                )

        # Primary for goal check
        if conv.status.name == 'ENABLED' and not conv.primary_for_goal:
            recommendations.append(
                "Consider setting as primary for Smart Bidding optimization"
            )

        # Value check
        if conv.value_settings.default_value == 0:
            recommendations.append(
                "Set conversion value for better ROI tracking"
            )

        # Extract tag info for WEBPAGE conversions
        tag_info = {}
        if conv.type_.name == 'WEBPAGE' and conv.tag_snippets:
            for snippet in conv.tag_snippets:
                if snippet.event_snippet:
                    event = snippet.event_snippet
                    if "'send_to':" in event:
                        start = event.find("'send_to':") + 11
                        end = event.find("'", start + 1)
                        if start > 10 and end > start:
                            send_to = event[start:end]
                            if '/' in send_to:
                                parts = send_to.split('/')
                                tag_info = {
                                    'conversion_id': parts[0].replace('AW-', ''),
                                    'conversion_label': parts[1]
                                }

        return {
            'conversion': {
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
            },
            'performance': {
                'total_conversions': total_conversions,
                'total_value': total_value,
                'daily_breakdown': daily_conversions[:7]  # Last 7 days
            },
            'issues': issues,
            'recommendations': recommendations
        }

    def _get_health_status(self, score: int) -> str:
        """Get health status string from score."""
        if score >= 80:
            return "HEALTHY"
        elif score >= 60:
            return "NEEDS_ATTENTION"
        elif score >= 40:
            return "POOR"
        else:
            return "CRITICAL"
