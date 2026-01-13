"""Tests for reporting module (GAQL builder, templates, export)."""

import pytest
from xwander_ads.reporting import (
    GAQLBuilder,
    validate_query,
    format_query,
    QueryTemplates,
    CSVExporter,
    JSONExporter,
)


class TestGAQLBuilder:
    """Test GAQL query builder."""

    def test_basic_query(self):
        """Test building a basic query."""
        query = (
            GAQLBuilder()
            .select('campaign.id', 'campaign.name')
            .from_resource('campaign')
            .build()
        )

        assert 'SELECT campaign.id, campaign.name' in query
        assert 'FROM campaign' in query

    def test_query_with_where(self):
        """Test query with WHERE clause."""
        query = (
            GAQLBuilder()
            .select('campaign.name')
            .from_resource('campaign')
            .where('campaign.status = ENABLED')
            .build()
        )

        assert 'WHERE campaign.status = ENABLED' in query

    def test_query_with_date_range(self):
        """Test query with date range."""
        query = (
            GAQLBuilder()
            .select('campaign.name', 'metrics.clicks')
            .from_resource('campaign')
            .during('LAST_7_DAYS')
            .build()
        )

        assert 'WHERE segments.date DURING LAST_7_DAYS' in query

    def test_query_with_order_by(self):
        """Test query with ORDER BY."""
        query = (
            GAQLBuilder()
            .select('campaign.name', 'metrics.cost_micros')
            .from_resource('campaign')
            .order_by('metrics.cost_micros', desc=True)
            .build()
        )

        assert 'ORDER BY metrics.cost_micros DESC' in query

    def test_query_with_limit(self):
        """Test query with LIMIT."""
        query = (
            GAQLBuilder()
            .select('campaign.name')
            .from_resource('campaign')
            .limit(50)
            .build()
        )

        assert 'LIMIT 50' in query

    def test_complex_query(self):
        """Test complex query with all clauses."""
        query = (
            GAQLBuilder()
            .select('campaign.id', 'campaign.name', 'metrics.clicks')
            .from_resource('campaign')
            .where('campaign.status = ENABLED')
            .during('LAST_30_DAYS')
            .order_by('metrics.clicks', desc=True)
            .limit(100)
            .build()
        )

        assert 'SELECT campaign.id, campaign.name, metrics.clicks' in query
        assert 'FROM campaign' in query
        assert 'campaign.status = ENABLED' in query
        assert 'segments.date DURING LAST_30_DAYS' in query
        assert 'ORDER BY metrics.clicks DESC' in query
        assert 'LIMIT 100' in query

    def test_missing_select_raises_error(self):
        """Test that missing SELECT raises error."""
        with pytest.raises(ValueError, match='SELECT clause is required'):
            GAQLBuilder().from_resource('campaign').build()

    def test_missing_from_raises_error(self):
        """Test that missing FROM raises error."""
        with pytest.raises(ValueError, match='FROM clause is required'):
            GAQLBuilder().select('campaign.name').build()

    def test_date_between(self):
        """Test date range between two dates."""
        query = (
            GAQLBuilder()
            .select('campaign.name')
            .from_resource('campaign')
            .date_between('2025-01-01', '2025-01-31')
            .build()
        )

        assert "segments.date BETWEEN '2025-01-01' AND '2025-01-31'" in query


class TestQueryValidation:
    """Test query validation."""

    def test_valid_query(self):
        """Test validating a valid query."""
        query = "SELECT campaign.name FROM campaign"
        assert validate_query(query) is True

    def test_missing_select(self):
        """Test query without SELECT."""
        with pytest.raises(ValueError, match='must start with SELECT'):
            validate_query("FROM campaign")

    def test_missing_from(self):
        """Test query without FROM."""
        with pytest.raises(ValueError, match='must contain FROM'):
            validate_query("SELECT campaign.name")


class TestQueryFormatting:
    """Test query formatting."""

    def test_format_simple_query(self):
        """Test formatting a simple query."""
        query = "SELECT campaign.name FROM campaign WHERE campaign.status = ENABLED"
        formatted = format_query(query)

        assert 'SELECT' in formatted
        assert 'FROM campaign' in formatted
        assert 'WHERE' in formatted

    def test_format_preserves_query(self):
        """Test that formatting doesn't change query logic."""
        original = "SELECT campaign.name FROM campaign LIMIT 10"
        formatted = format_query(original)

        # Remove whitespace and compare
        assert original.replace(' ', '') in formatted.replace(' ', '').replace('\n', '')


class TestQueryTemplates:
    """Test pre-built query templates."""

    def test_campaign_performance_template(self):
        """Test campaign performance template."""
        query = QueryTemplates.campaign_performance(days=7, limit=50)

        assert 'SELECT' in query
        assert 'campaign.name' in query
        assert 'metrics.clicks' in query
        assert 'FROM campaign' in query
        assert 'LAST_7_DAYS' in query
        assert 'LIMIT 50' in query

    def test_conversion_actions_template(self):
        """Test conversion actions template."""
        query = QueryTemplates.conversion_actions(customer_id='123')

        assert 'conversion_action.id' in query
        assert 'conversion_action.name' in query
        assert 'FROM conversion_action' in query

    def test_search_terms_template(self):
        """Test search terms template."""
        query = QueryTemplates.search_terms(days=14, limit=100)

        assert 'search_term_view.search_term' in query
        assert 'FROM search_term_view' in query
        assert 'LAST_14_DAYS' in query

    def test_asset_group_performance_template(self):
        """Test asset group performance template."""
        query = QueryTemplates.asset_group_performance(campaign_id='123', days=30)

        assert 'asset_group.name' in query
        assert 'FROM asset_group' in query
        assert 'PERFORMANCE_MAX' in query
        assert 'campaign.id = 123' in query


class TestExport:
    """Test export functionality."""

    def test_csv_export_to_string(self):
        """Test CSV export to string."""
        data = [
            {'campaign.name': 'Campaign 1', 'metrics.clicks': 100},
            {'campaign.name': 'Campaign 2', 'metrics.clicks': 200},
        ]

        csv_string = CSVExporter.to_string(data)

        assert 'campaign.name,metrics.clicks' in csv_string
        assert 'Campaign 1,100' in csv_string
        assert 'Campaign 2,200' in csv_string

    def test_json_export_to_string(self):
        """Test JSON export to string."""
        data = [
            {'campaign.name': 'Campaign 1', 'metrics.clicks': 100},
        ]

        json_string = JSONExporter.to_string(data)

        assert '"campaign.name"' in json_string
        assert '"Campaign 1"' in json_string
        assert '"metrics.clicks"' in json_string
        assert '100' in json_string

    def test_csv_export_with_selected_columns(self):
        """Test CSV export with specific columns."""
        data = [
            {'campaign.name': 'Campaign 1', 'metrics.clicks': 100, 'extra': 'field'},
        ]

        csv_string = CSVExporter.to_string(data, columns=['campaign.name', 'metrics.clicks'])

        assert 'campaign.name,metrics.clicks' in csv_string
        assert 'extra' not in csv_string

    def test_empty_data_export(self):
        """Test exporting empty data."""
        assert CSVExporter.to_string([]) == "No data"
        assert JSONExporter.to_string([]) == "[]"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
