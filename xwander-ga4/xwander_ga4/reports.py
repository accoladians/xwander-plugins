"""GA4 Report builders and formatters"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from .client import GA4DataClient
from .exceptions import GA4ValidationError


class ReportBuilder:
    """Build and run GA4 reports"""

    def __init__(self, client: GA4DataClient):
        self.client = client

    def last_n_days(
        self,
        days: int,
        dimensions: List[str],
        metrics: List[str],
        limit: int = 100,
        order_bys: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Get report for last N days

        Args:
            days: Number of days (1-730)
            dimensions: List of dimension names
            metrics: List of metric names
            limit: Max rows
            order_bys: Optional sort order

        Returns:
            Report with rows and quota
        """
        if days < 1 or days > 730:
            raise GA4ValidationError("Days must be between 1 and 730")

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        return self.client.run_report(
            date_ranges=[
                {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                }
            ],
            dimensions=dimensions,
            metrics=metrics,
            limit=limit,
            order_bys=order_bys,
        )

    def date_range(
        self,
        start_date: str,
        end_date: str,
        dimensions: List[str],
        metrics: List[str],
        limit: int = 100,
        order_bys: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Get report for specific date range

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            dimensions: List of dimension names
            metrics: List of metric names
            limit: Max rows
            order_bys: Optional sort order

        Returns:
            Report with rows and quota
        """
        return self.client.run_report(
            date_ranges=[{"start_date": start_date, "end_date": end_date}],
            dimensions=dimensions,
            metrics=metrics,
            limit=limit,
            order_bys=order_bys,
        )

    def traffic_sources(self, days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """Traffic by source/medium"""
        return self.last_n_days(
            days=days,
            dimensions=["source", "medium"],
            metrics=["sessions", "activeUsers", "bounceRate"],
            limit=limit,
            order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        )

    def top_pages(self, days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """Top pages by sessions"""
        return self.last_n_days(
            days=days,
            dimensions=["pagePath"],
            metrics=["sessions", "activeUsers", "averageSessionDuration"],
            limit=limit,
            order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        )

    def conversions(self, days: int = 30, limit: int = 100) -> Dict[str, Any]:
        """Conversion actions and counts"""
        return self.last_n_days(
            days=days,
            dimensions=["eventName"],
            metrics=["eventCount", "eventValue"],
            limit=limit,
            order_bys=[{"metric": {"metric_name": "eventCount"}, "desc": True}],
        )

    def daily_summary(self, days: int = 30) -> Dict[str, Any]:
        """Daily metrics summary"""
        return self.last_n_days(
            days=days,
            dimensions=["date"],
            metrics=["sessions", "activeUsers", "eventCount"],
            limit=days + 1,
        )

    def realtime_summary(self) -> Dict[str, Any]:
        """Realtime active users by country"""
        return self.client.run_realtime_report(
            dimensions=["country"],
            metrics=["activeUsers"],
            limit=20,
        )


class ReportFormatter:
    """
    Format GA4 reports for display

    Provides multiple output formats for GA4 report data:
    - table(): ASCII table format for terminal display
    - json(): JSON format for programmatic use
    - summary(): Human-readable text summary with key metrics

    All methods accept the report data dict returned by GA4DataClient.run_report()
    """

    @staticmethod
    def table(data: Dict[str, Any], columns: Optional[List[str]] = None) -> str:
        """Format report as ASCII table"""
        if not data.get("rows"):
            return "No data"

        rows = data["rows"]
        if columns:
            rows = [{k: v for k, v in row.items() if k in columns} for row in rows]

        if not rows:
            return "No data"

        # Get column widths
        keys = list(rows[0].keys())
        widths = {k: len(k) for k in keys}
        for row in rows:
            for k, v in row.items():
                widths[k] = max(widths[k], len(str(v)))

        # Build table
        header = " | ".join(f"{k:{widths[k]}}" for k in keys)
        separator = "-+-".join("-" * widths[k] for k in keys)

        lines = [header, separator]
        for row in rows:
            lines.append(" | ".join(f"{str(row[k]):{widths[k]}}" for k in keys))

        return "\n".join(lines)

    @staticmethod
    def json(data: Dict[str, Any]) -> str:
        """Format report as JSON"""
        import json

        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def summary(data: Dict[str, Any]) -> str:
        """Format report as summary text"""
        lines = [f"Rows: {data.get('row_count', len(data.get('rows', [])))}"]

        if data.get("rows"):
            lines.append("\nData:")
            for row in data["rows"][:5]:
                items = [f"{k}: {v}" for k, v in row.items()]
                lines.append("  - " + ", ".join(items))
            if len(data["rows"]) > 5:
                lines.append(f"  ... and {len(data['rows']) - 5} more rows")

        if data.get("property_quota"):
            quota = data["property_quota"]
            lines.append(
                f"\nQuota: {quota.get('tokens_used', 0)} / "
                f"{quota.get('tokens_per_day', 0)} tokens"
            )

        return "\n".join(lines)
