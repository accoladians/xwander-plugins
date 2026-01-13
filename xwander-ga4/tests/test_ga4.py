"""Tests for GA4 plugin"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from xwander_ga4 import (
    GA4DataClient,
    GA4AdminClient,
    ReportBuilder,
    ReportFormatter,
    DimensionManager,
    AudienceManager,
    GA4ValidationError,
    GA4ConfigError,
)


class TestGA4DataClient(unittest.TestCase):
    """Test GA4 Data API client"""

    def setUp(self):
        self.property_id = "358203796"

    @patch("xwander_ga4.client.BetaAnalyticsDataClient")
    def test_init_success(self, mock_client):
        """Test successful client initialization"""
        client = GA4DataClient(self.property_id)
        assert client.property_id == self.property_id
        assert client.property_resource == f"properties/{self.property_id}"

    @patch("xwander_ga4.client.BetaAnalyticsDataClient")
    def test_init_failure(self, mock_client):
        """Test failed client initialization"""
        mock_client.side_effect = Exception("Auth failed")
        with self.assertRaises(GA4ConfigError):
            GA4DataClient(self.property_id)

    @patch("xwander_ga4.client.BetaAnalyticsDataClient")
    def test_run_report_missing_params(self, mock_client):
        """Test run_report with missing parameters"""
        client = GA4DataClient(self.property_id)
        with self.assertRaises(GA4ValidationError):
            client.run_report([], [], [])

    @patch("xwander_ga4.client.BetaAnalyticsDataClient")
    def test_run_report_success(self, mock_client):
        """Test successful report run"""
        # Mock response
        mock_response = MagicMock()
        mock_response.rows = []
        mock_response.row_count = 0
        mock_response.dimension_headers = []
        mock_response.metric_headers = []
        mock_response.property_quota = MagicMock(
            tokens_per_day=1000,
            tokens_per_hour=100,
            concurrent_requests=10,
            server_errors_per_day=5,
            tokens_used=50,
            tokens_remaining=950,
            reset_window_reset_delay_days=1,
            concurrent_requests_used=1,
            concurrent_requests_remaining=9,
        )

        client = GA4DataClient(self.property_id)
        client.client.run_report = MagicMock(return_value=mock_response)

        result = client.run_report(
            date_ranges=[{"start_date": "2026-01-01", "end_date": "2026-01-07"}],
            dimensions=["date"],
            metrics=["sessions"],
        )

        assert "rows" in result
        assert "property_quota" in result
        assert result["row_count"] == 0

    @patch("xwander_ga4.client.BetaAnalyticsDataClient")
    def test_run_realtime_report(self, mock_client):
        """Test realtime report"""
        mock_response = MagicMock()
        mock_response.rows = []
        mock_response.dimension_headers = []
        mock_response.metric_headers = []
        mock_response.totals_row = MagicMock(metric_values=[])

        client = GA4DataClient(self.property_id)
        client.client.run_realtime_report = MagicMock(return_value=mock_response)

        result = client.run_realtime_report(
            dimensions=["country"],
            metrics=["activeUsers"],
        )

        assert "rows" in result
        assert "total_users" in result


class TestGA4AdminClient(unittest.TestCase):
    """Test GA4 Admin API client"""

    def setUp(self):
        self.property_id = "358203796"

    @patch("xwander_ga4.client.AnalyticsAdminServiceClient")
    def test_init_success(self, mock_client):
        """Test successful admin client initialization"""
        client = GA4AdminClient(self.property_id)
        assert client.property_id == self.property_id
        assert client.property_resource == f"properties/{self.property_id}"

    @patch("xwander_ga4.client.AnalyticsAdminServiceClient")
    def test_create_dimension_invalid_scope(self, mock_client):
        """Test dimension creation with invalid scope"""
        client = GA4AdminClient(self.property_id)
        with self.assertRaises(GA4ValidationError):
            client.create_custom_dimension(
                display_name="Test",
                parameter_name="test",
                scope="INVALID",
            )


class TestReportBuilder(unittest.TestCase):
    """Test report builder"""

    def setUp(self):
        self.mock_client = MagicMock(spec=GA4DataClient)

    def test_last_n_days_invalid_days(self):
        """Test last_n_days with invalid days"""
        builder = ReportBuilder(self.mock_client)
        with self.assertRaises(GA4ValidationError):
            builder.last_n_days(days=0, dimensions=["date"], metrics=["sessions"])

        with self.assertRaises(GA4ValidationError):
            builder.last_n_days(days=731, dimensions=["date"], metrics=["sessions"])

    def test_last_n_days_success(self):
        """Test successful last_n_days report"""
        self.mock_client.run_report = MagicMock(
            return_value={"rows": [], "row_count": 0, "property_quota": {}}
        )
        builder = ReportBuilder(self.mock_client)
        result = builder.last_n_days(days=7, dimensions=["date"], metrics=["sessions"])
        assert result is not None
        self.mock_client.run_report.assert_called_once()

    def test_traffic_sources(self):
        """Test traffic_sources report"""
        self.mock_client.run_report = MagicMock(
            return_value={"rows": [], "row_count": 0, "property_quota": {}}
        )
        builder = ReportBuilder(self.mock_client)
        result = builder.traffic_sources(days=30)
        assert result is not None
        self.mock_client.run_report.assert_called_once()


class TestReportFormatter(unittest.TestCase):
    """Test report formatter"""

    def test_table_format(self):
        """Test table formatting"""
        data = {
            "rows": [
                {"date": "2026-01-01", "sessions": "100"},
                {"date": "2026-01-02", "sessions": "150"},
            ]
        }
        formatter = ReportFormatter()
        result = formatter.table(data)
        assert "date" in result
        assert "sessions" in result
        assert "2026-01-01" in result

    def test_table_empty_data(self):
        """Test table formatting with empty data"""
        data = {"rows": []}
        formatter = ReportFormatter()
        result = formatter.table(data)
        assert result == "No data"

    def test_json_format(self):
        """Test JSON formatting"""
        data = {"rows": [{"date": "2026-01-01"}]}
        formatter = ReportFormatter()
        result = formatter.json(data)
        assert "2026-01-01" in result

    def test_summary_format(self):
        """Test summary formatting"""
        data = {
            "rows": [
                {"date": "2026-01-01", "sessions": "100"},
                {"date": "2026-01-02", "sessions": "150"},
            ]
        }
        formatter = ReportFormatter()
        result = formatter.summary(data)
        assert "Rows:" in result
        assert "date" in result


class TestDimensionManager(unittest.TestCase):
    """Test dimension manager"""

    def setUp(self):
        self.mock_admin = MagicMock(spec=GA4AdminClient)

    def test_validate_parameter_name(self):
        """Test parameter name validation"""
        # Valid names
        DimensionManager.validate_parameter_name("product_type")
        DimensionManager.validate_parameter_name("day_tour")

        # Invalid names
        with self.assertRaises(GA4ValidationError):
            DimensionManager.validate_parameter_name("")

        with self.assertRaises(GA4ValidationError):
            DimensionManager.validate_parameter_name("a" * 41)

        with self.assertRaises(GA4ValidationError):
            DimensionManager.validate_parameter_name("123invalid")

    def test_validate_display_name(self):
        """Test display name validation"""
        # Valid names
        DimensionManager.validate_display_name("Product Type")
        DimensionManager.validate_display_name("Day Tour")

        # Invalid names
        with self.assertRaises(GA4ValidationError):
            DimensionManager.validate_display_name("")

        with self.assertRaises(GA4ValidationError):
            DimensionManager.validate_display_name("a" * 101)

    def test_create_dimension(self):
        """Test dimension creation"""
        self.mock_admin.create_custom_dimension = MagicMock(
            return_value={"api_name": "customEvent:test"}
        )
        manager = DimensionManager(self.mock_admin)
        result = manager.create(
            display_name="Test", parameter_name="test", scope="EVENT"
        )
        assert result["api_name"] == "customEvent:test"


if __name__ == "__main__":
    unittest.main()
