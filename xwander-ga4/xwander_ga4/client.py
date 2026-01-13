"""GA4 Data API and Admin API clients"""

import os
from typing import Any, Dict, List, Optional
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    RunRealtimeReportRequest,
)
from google.analytics.admin_v1beta.types import (
    CustomDimension,
)
from google.api_core.gapic_v1 import client_info

from .exceptions import GA4ConfigError, GA4APIError, GA4ValidationError


class GA4DataClient:
    """Google Analytics 4 Data API client"""

    def __init__(self, property_id: str, credentials_path: Optional[str] = None):
        """
        Initialize GA4 Data API client

        Args:
            property_id: GA4 property ID (e.g., '358203796')
            credentials_path: Path to service account JSON (default: GOOGLE_APPLICATION_CREDENTIALS)
        """
        self.property_id = property_id
        self.property_resource = f"properties/{property_id}"

        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        try:
            self.client = BetaAnalyticsDataClient()
        except Exception as e:
            raise GA4ConfigError(f"Failed to initialize GA4 Data API: {e}")

    def run_report(
        self,
        date_ranges: List[Dict[str, str]],
        dimensions: List[str],
        metrics: List[str],
        limit: int = 10,
        offset: int = 0,
        order_bys: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Run a GA4 report

        Args:
            date_ranges: List of {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
            dimensions: List of dimension names (e.g., ['date', 'source'])
            metrics: List of metric names (e.g., ['sessions', 'users'])
            limit: Max rows to return (default 10)
            offset: Row offset (default 0)
            order_bys: Optional sort order

        Returns:
            Dict with rows, row_count, property_quota
        """
        if not date_ranges or not dimensions or not metrics:
            raise GA4ValidationError("date_ranges, dimensions, and metrics are required")

        # Build request
        request = RunReportRequest(
            property=self.property_resource,
            date_ranges=[
                DateRange(start_date=dr["start_date"], end_date=dr["end_date"])
                for dr in date_ranges
            ],
            dimensions=[Dimension(name=dim) for dim in dimensions],
            metrics=[Metric(name=met) for met in metrics],
            limit=limit,
            offset=offset,
        )

        if order_bys:
            request.order_bys = order_bys

        try:
            response = self.client.run_report(request)
            return self._format_report_response(response)
        except Exception as e:
            raise GA4APIError(f"Failed to run report: {e}")

    def run_realtime_report(
        self,
        dimensions: List[str],
        metrics: List[str],
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Run a realtime GA4 report

        Args:
            dimensions: List of dimension names (e.g., ['country', 'source'])
            metrics: List of metric names (e.g., ['activeUsers', 'eventCount'])
            limit: Max rows to return

        Returns:
            Dict with rows, total_users
        """
        if not dimensions or not metrics:
            raise GA4ValidationError("dimensions and metrics are required")

        request = RunRealtimeReportRequest(
            property=self.property_resource,
            dimensions=[Dimension(name=dim) for dim in dimensions],
            metrics=[Metric(name=met) for met in metrics],
            limit=limit,
        )

        try:
            response = self.client.run_realtime_report(request)
            return self._format_realtime_response(response)
        except Exception as e:
            raise GA4APIError(f"Failed to run realtime report: {e}")

    @staticmethod
    def _format_report_response(response) -> Dict[str, Any]:
        """Format GA4 report response"""
        rows = []
        for row in response.rows:
            row_dict = {}
            for i, dim_value in enumerate(row.dimension_values):
                if i < len(response.dimension_headers):
                    row_dict[response.dimension_headers[i].name] = dim_value.value
            for i, metric_value in enumerate(row.metric_values):
                if i < len(response.metric_headers):
                    row_dict[response.metric_headers[i].name] = metric_value.value
            rows.append(row_dict)

        # Build quota dict with safe attribute access (API fields may vary)
        quota = response.property_quota
        quota_dict = {}
        for field in [
            "tokens_per_day", "tokens_per_hour", "concurrent_requests",
            "tokens_used", "tokens_remaining", "concurrent_requests_used",
            "concurrent_requests_remaining"
        ]:
            if hasattr(quota, field):
                quota_dict[field] = getattr(quota, field)

        return {
            "rows": rows,
            "row_count": response.row_count,
            "property_quota": quota_dict,
        }

    @staticmethod
    def _format_realtime_response(response) -> Dict[str, Any]:
        """Format GA4 realtime report response"""
        rows = []
        for row in response.rows:
            row_dict = {}
            for i, dim_value in enumerate(row.dimension_values):
                if i < len(response.dimension_headers):
                    row_dict[response.dimension_headers[i].name] = dim_value.value
            for i, metric_value in enumerate(row.metric_values):
                if i < len(response.metric_headers):
                    row_dict[response.metric_headers[i].name] = metric_value.value
            rows.append(row_dict)

        return {
            "rows": rows,
            "total_users": response.totals_row.metric_values[0].value
            if response.totals_row and response.totals_row.metric_values
            else 0,
        }


class GA4AdminClient:
    """Google Analytics 4 Admin API client"""

    def __init__(self, property_id: str, credentials_path: Optional[str] = None):
        """
        Initialize GA4 Admin API client

        Args:
            property_id: GA4 property ID (e.g., '358203796')
            credentials_path: Path to service account JSON
        """
        self.property_id = property_id
        self.property_resource = f"properties/{property_id}"
        self.account_id = None  # Will be extracted from property

        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        try:
            self.client = AnalyticsAdminServiceClient()
        except Exception as e:
            raise GA4ConfigError(f"Failed to initialize GA4 Admin API: {e}")

    def get_property(self) -> Dict[str, Any]:
        """Get property details"""
        try:
            property_obj = self.client.get_property(name=self.property_resource)
            self.account_id = property_obj.account.split("/")[-1]
            return {
                "name": property_obj.display_name,
                "property_id": property_obj.name.split("/")[-1],
                "account_id": self.account_id,
                "timezone": property_obj.time_zone,
                "currency_code": property_obj.currency_code,
                "industry_category": property_obj.industry_category,
            }
        except Exception as e:
            raise GA4APIError(f"Failed to get property: {e}")

    def create_custom_dimension(
        self,
        display_name: str,
        parameter_name: str,
        scope: str = "EVENT",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a custom dimension

        Args:
            display_name: Display name (e.g., 'Product Type')
            parameter_name: Parameter name (e.g., 'product_type')
            scope: Dimension scope: 'EVENT', 'USER', or 'ITEM' (default: 'EVENT')
            description: Optional description

        Returns:
            Dict with custom_dimension details
        """
        if scope not in ["EVENT", "USER", "ITEM"]:
            raise GA4ValidationError(f"Invalid scope: {scope}")

        custom_dimension = CustomDimension(
            display_name=display_name,
            parameter_name=parameter_name,
            scope=CustomDimension.DimensionScope[scope],
            description=description,
        )

        # Use client method directly instead of request object
        try:

            response = self.client.create_custom_dimension(
                parent=self.property_resource,
                custom_dimension=custom_dimension
            )
            return {
                "api_name": response.api_name,
                "display_name": response.display_name,
                "parameter_name": response.parameter_name,
                "scope": response.scope.name,
                "description": response.description,
            }
        except Exception as e:
            raise GA4APIError(f"Failed to create custom dimension: {e}")

    def list_custom_dimensions(self) -> List[Dict[str, Any]]:
        """
        List all custom dimensions

        Returns:
            List of custom dimensions
        """
        try:
            response = self.client.list_custom_dimensions(parent=self.property_resource)
            dimensions = []
            for dim in response.custom_dimensions:
                dimensions.append(
                    {
                        "api_name": dim.api_name,
                        "display_name": dim.display_name,
                        "parameter_name": dim.parameter_name,
                        "scope": dim.scope.name,
                        "description": dim.description,
                    }
                )
            return dimensions
        except Exception as e:
            raise GA4APIError(f"Failed to list custom dimensions: {e}")

    def list_audiences(self) -> List[Dict[str, Any]]:
        """
        List all audiences

        Returns:
            List of audiences
        """
        try:
            response = self.client.list_audiences(parent=self.property_resource)
            audiences = []
            for audience in response.audiences:
                audiences.append(
                    {
                        "name": audience.display_name,
                        "audience_id": audience.name.split("/")[-1],
                        "description": audience.description,
                        "member_count": audience.member_count_approximate or 0,
                    }
                )
            return audiences
        except Exception as e:
            raise GA4APIError(f"Failed to list audiences: {e}")
