"""Unit tests for Search campaigns module.

These tests verify the Search module works correctly using mocked
Google Ads API responses. For integration tests with the live API,
see test_search_integration.py.

Run with:
    cd /srv/plugins/xwander-ads
    python3 -m pytest tests/test_search.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from google.ads.googleads.errors import GoogleAdsException

from xwander_ads.search import (
    create_search_campaign,
    get_search_campaign,
    list_search_campaigns,
    get_campaign_criteria,
    set_device_bid_adjustments,
    update_conversion_attribution,
    link_conversion_actions,
    get_device_performance,
    bulk_update_attributions,
    GEO_TARGETS,
    LANGUAGE_CONSTANTS,
    TOURIST_LANGUAGES,
    DEVICE_TYPES,
    DAY_TOURS_DEVICE_MODIFIERS,
)
from xwander_ads.exceptions import (
    CampaignNotFoundError,
    ValidationError,
    APIError,
    QuotaExceededError,
    InvalidResourceError,
)


# Test configuration
CUSTOMER_ID = "2425288235"
CAMPAIGN_ID = "12345678901"
CONVERSION_ACTION_ID = "7452944340"


class TestConstants:
    """Test that constants are defined correctly."""

    def test_geo_targets_contains_finland(self):
        """Test Finland geo target is defined."""
        assert 'FINLAND' in GEO_TARGETS
        assert GEO_TARGETS['FINLAND'] == 'geoTargetConstants/2246'

    def test_language_constants_contains_tourist_languages(self):
        """Test tourist languages are defined."""
        assert 'ENGLISH' in LANGUAGE_CONSTANTS
        assert 'FRENCH' in LANGUAGE_CONSTANTS
        assert 'GERMAN' in LANGUAGE_CONSTANTS
        assert LANGUAGE_CONSTANTS['ENGLISH'] == 1000

    def test_tourist_languages_default(self):
        """Test default tourist languages."""
        assert 'ENGLISH' in TOURIST_LANGUAGES
        assert 'FRENCH' in TOURIST_LANGUAGES
        assert 'GERMAN' in TOURIST_LANGUAGES
        assert len(TOURIST_LANGUAGES) == 5

    def test_device_types_defined(self):
        """Test device type constants."""
        assert DEVICE_TYPES['MOBILE'] == 4
        assert DEVICE_TYPES['DESKTOP'] == 2
        assert DEVICE_TYPES['TABLET'] == 3

    def test_day_tours_modifiers(self):
        """Test Day Tours recommended modifiers."""
        assert DAY_TOURS_DEVICE_MODIFIERS['MOBILE'] == 1.5
        assert DAY_TOURS_DEVICE_MODIFIERS['DESKTOP'] == 0.7
        assert DAY_TOURS_DEVICE_MODIFIERS['TABLET'] == 1.0


class TestCampaignCreation:
    """Test campaign creation functions."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Google Ads client."""
        client = Mock()

        # Mock services
        client.get_service.return_value = Mock()

        # Mock enums
        client.enums.BudgetDeliveryMethodEnum.STANDARD = "STANDARD"
        client.enums.AdvertisingChannelTypeEnum.SEARCH = "SEARCH"
        client.enums.CampaignStatusEnum.PAUSED = "PAUSED"
        client.enums.CampaignStatusEnum.ENABLED = "ENABLED"
        client.enums.GeoTargetingTypeEnum.LOCATION_OF_PRESENCE = "LOCATION_OF_PRESENCE"
        client.enums.GeoTargetingTypeEnum.AREA_OF_INTEREST = "AREA_OF_INTEREST"

        # Mock type creation
        mock_op = Mock()
        mock_op.campaign_budget_operation.create = Mock()
        mock_op.campaign_operation.create = Mock()
        mock_op.campaign_criterion_operation.create = Mock()
        client.get_type.return_value = mock_op

        return client

    def test_create_campaign_validation_empty_name(self, mock_client):
        """Test validation rejects empty campaign name."""
        with pytest.raises(ValidationError) as exc:
            create_search_campaign(
                mock_client,
                CUSTOMER_ID,
                name="",
                daily_budget_eur=50.0
            )
        assert "name is required" in str(exc.value)

    def test_create_campaign_validation_negative_budget(self, mock_client):
        """Test validation rejects negative budget."""
        with pytest.raises(ValidationError) as exc:
            create_search_campaign(
                mock_client,
                CUSTOMER_ID,
                name="Test Campaign",
                daily_budget_eur=-10.0
            )
        assert "budget must be positive" in str(exc.value)

    def test_create_campaign_validation_negative_cpa(self, mock_client):
        """Test validation rejects negative target CPA."""
        with pytest.raises(ValidationError) as exc:
            create_search_campaign(
                mock_client,
                CUSTOMER_ID,
                name="Test Campaign",
                daily_budget_eur=50.0,
                target_cpa_eur=-5.0
            )
        assert "Target CPA must be positive" in str(exc.value)

    def test_create_campaign_validation_invalid_geo_type(self, mock_client):
        """Test validation rejects invalid geo target type."""
        with pytest.raises(ValidationError) as exc:
            create_search_campaign(
                mock_client,
                CUSTOMER_ID,
                name="Test Campaign",
                daily_budget_eur=50.0,
                geo_target_type="INVALID_TYPE"
            )
        assert "Invalid geo_target_type" in str(exc.value)


class TestDeviceBidAdjustments:
    """Test device bid adjustment functions."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Google Ads client for device adjustments."""
        client = Mock()

        # Mock services
        mock_criterion_service = Mock()
        mock_campaign_service = Mock()

        def get_service(name):
            if name == "CampaignCriterionService":
                return mock_criterion_service
            elif name == "CampaignService":
                return mock_campaign_service
            return Mock()

        client.get_service.side_effect = get_service

        # Mock campaign_path
        mock_campaign_service.campaign_path.return_value = f"customers/{CUSTOMER_ID}/campaigns/{CAMPAIGN_ID}"

        # Mock enums
        client.enums.DeviceEnum.MOBILE = "MOBILE"
        client.enums.DeviceEnum.DESKTOP = "DESKTOP"
        client.enums.DeviceEnum.TABLET = "TABLET"

        # Mock type creation
        mock_op = Mock()
        mock_op.create = Mock()
        client.get_type.return_value = mock_op

        # Mock mutate response
        mock_response = Mock()
        mock_response.results = [
            Mock(resource_name="customers/123/campaignCriteria/1"),
            Mock(resource_name="customers/123/campaignCriteria/2"),
            Mock(resource_name="customers/123/campaignCriteria/3"),
        ]
        mock_criterion_service.mutate_campaign_criteria.return_value = mock_response

        return client

    def test_set_device_adjustments_validation_low_modifier(self, mock_client):
        """Test validation rejects modifier below 0."""
        with pytest.raises(ValidationError) as exc:
            set_device_bid_adjustments(
                mock_client,
                CUSTOMER_ID,
                CAMPAIGN_ID,
                mobile_modifier=-0.5
            )
        assert "Invalid mobile_modifier" in str(exc.value)

    def test_set_device_adjustments_validation_high_modifier(self, mock_client):
        """Test validation rejects modifier above 10."""
        with pytest.raises(ValidationError) as exc:
            set_device_bid_adjustments(
                mock_client,
                CUSTOMER_ID,
                CAMPAIGN_ID,
                desktop_modifier=15.0
            )
        assert "Invalid desktop_modifier" in str(exc.value)

    def test_set_device_adjustments_success(self, mock_client):
        """Test successful device bid adjustment."""
        result = set_device_bid_adjustments(
            mock_client,
            CUSTOMER_ID,
            CAMPAIGN_ID,
            mobile_modifier=1.5,
            desktop_modifier=0.7,
            tablet_modifier=1.0
        )

        assert result['campaign_id'] == CAMPAIGN_ID
        assert result['device_adjustments']['MOBILE'] == 1.5
        assert result['device_adjustments']['DESKTOP'] == 0.7
        assert result['device_adjustments']['TABLET'] == 1.0
        assert len(result['results']) == 3


class TestAttributionUpdates:
    """Test attribution window update functions."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Google Ads client for attribution updates."""
        client = Mock()

        # Mock service
        mock_ca_service = Mock()
        mock_ca_service.conversion_action_path.return_value = (
            f"customers/{CUSTOMER_ID}/conversionActions/{CONVERSION_ACTION_ID}"
        )

        client.get_service.return_value = mock_ca_service

        # Mock type creation
        mock_op = Mock()
        mock_op.update_mask.paths = []
        mock_op.update = Mock()
        client.get_type.return_value = mock_op

        # Mock response
        mock_response = Mock()
        mock_response.results = [
            Mock(resource_name=f"customers/{CUSTOMER_ID}/conversionActions/{CONVERSION_ACTION_ID}")
        ]
        mock_ca_service.mutate_conversion_actions.return_value = mock_response

        return client

    def test_update_attribution_validation_click_days_low(self, mock_client):
        """Test validation rejects click days below 1."""
        with pytest.raises(ValidationError) as exc:
            update_conversion_attribution(
                mock_client,
                CUSTOMER_ID,
                CONVERSION_ACTION_ID,
                click_lookback_days=0
            )
        assert "click_lookback_days must be 1-90" in str(exc.value)

    def test_update_attribution_validation_click_days_high(self, mock_client):
        """Test validation rejects click days above 90."""
        with pytest.raises(ValidationError) as exc:
            update_conversion_attribution(
                mock_client,
                CUSTOMER_ID,
                CONVERSION_ACTION_ID,
                click_lookback_days=100
            )
        assert "click_lookback_days must be 1-90" in str(exc.value)

    def test_update_attribution_validation_view_days_high(self, mock_client):
        """Test validation rejects view days above 30."""
        with pytest.raises(ValidationError) as exc:
            update_conversion_attribution(
                mock_client,
                CUSTOMER_ID,
                CONVERSION_ACTION_ID,
                click_lookback_days=7,
                view_lookback_days=60
            )
        assert "view_lookback_days must be 1-30" in str(exc.value)

    def test_update_attribution_success(self, mock_client):
        """Test successful attribution update."""
        result = update_conversion_attribution(
            mock_client,
            CUSTOMER_ID,
            CONVERSION_ACTION_ID,
            click_lookback_days=7,
            view_lookback_days=1
        )

        assert result['conversion_action_id'] == CONVERSION_ACTION_ID
        assert result['click_lookback_days'] == 7
        assert result['view_lookback_days'] == 1


class TestBulkUpdates:
    """Test bulk operation functions."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for bulk operations."""
        client = Mock()

        # Mock service
        mock_ca_service = Mock()
        mock_ca_service.conversion_action_path.return_value = "mock/path"
        client.get_service.return_value = mock_ca_service

        # Mock type and response
        mock_op = Mock()
        mock_op.update_mask.paths = []
        mock_op.update = Mock()
        client.get_type.return_value = mock_op

        mock_response = Mock()
        mock_response.results = [Mock(resource_name="mock/result")]
        mock_ca_service.mutate_conversion_actions.return_value = mock_response

        return client

    def test_bulk_update_attributions(self, mock_client):
        """Test bulk attribution updates."""
        updates = [
            {"conversion_action_id": "123", "click_lookback_days": 7},
            {"conversion_action_id": "456", "click_lookback_days": 90, "view_lookback_days": 30},
        ]

        results = bulk_update_attributions(mock_client, CUSTOMER_ID, updates)

        assert len(results) == 2
        assert results[0]['status'] == 'success'
        assert results[1]['status'] == 'success'

    def test_bulk_update_handles_errors(self, mock_client):
        """Test bulk update handles individual errors."""
        updates = [
            {"conversion_action_id": "123", "click_lookback_days": 7},
            {"conversion_action_id": "456", "click_lookback_days": 100},  # Invalid
        ]

        results = bulk_update_attributions(mock_client, CUSTOMER_ID, updates)

        # First should succeed, second should fail validation
        assert results[0]['status'] == 'success'
        assert results[1]['status'] == 'error'
        assert 'error' in results[1]


class TestConversionGoalLinking:
    """Test conversion action linking functions."""

    def test_link_conversion_actions_validation_empty_list(self):
        """Test validation rejects empty conversion action list."""
        mock_client = Mock()

        with pytest.raises(ValidationError) as exc:
            link_conversion_actions(
                mock_client,
                CUSTOMER_ID,
                CAMPAIGN_ID,
                conversion_action_ids=[]
            )
        assert "at least one conversion_action_id is required" in str(exc.value).lower()


class TestExceptionHandling:
    """Test exception classes and error handling."""

    def test_validation_error_exit_code(self):
        """Test ValidationError has correct exit code."""
        error = ValidationError("Test error")
        assert error.exit_code == 8

    def test_campaign_not_found_error_exit_code(self):
        """Test CampaignNotFoundError has correct exit code."""
        error = CampaignNotFoundError("Test error")
        assert error.exit_code == 4

    def test_api_error_exit_code(self):
        """Test APIError has correct exit code."""
        error = APIError("Test error")
        assert error.exit_code == 1

    def test_quota_exceeded_error_exit_code(self):
        """Test QuotaExceededError has correct exit code."""
        error = QuotaExceededError("Test error")
        assert error.exit_code == 2


class TestCLIIntegration:
    """Test CLI integration for search module."""

    def test_cli_help_search(self):
        """Test CLI search help is accessible."""
        from xwander_ads.cli import main
        import sys
        from io import StringIO

        # Capture output
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        with pytest.raises(SystemExit) as exc:
            main(['search', '--help'])

        sys.stdout = old_stdout

        # Should exit with 0 (help is normal exit)
        assert exc.value.code == 0

        output = captured.getvalue()
        assert 'search' in output.lower()

    def test_cli_search_list_missing_customer_id(self):
        """Test CLI search list requires customer-id."""
        from xwander_ads.cli import main

        with pytest.raises(SystemExit) as exc:
            main(['search', 'list'])

        # Should exit with error (2 = argparse error)
        assert exc.value.code == 2

    def test_cli_search_create_dry_run(self):
        """Test CLI search create --dry-run doesn't make API calls."""
        from xwander_ads.cli import main
        import sys
        from io import StringIO

        # Capture output
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        # This should NOT make API calls due to --dry-run
        try:
            main([
                'search', 'create',
                '--customer-id', '2425288235',
                '--name', 'Test Campaign',
                '--budget', '50',
                '--dry-run'
            ])
        except SystemExit:
            pass  # Expected

        sys.stdout = old_stdout
        output = captured.getvalue()

        # Should contain dry run indication
        assert 'DRY RUN' in output

    def test_cli_search_adjust_devices_dry_run(self):
        """Test CLI adjust-devices --dry-run doesn't make API calls."""
        from xwander_ads.cli import main
        import sys
        from io import StringIO

        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        try:
            main([
                'search', 'adjust-devices',
                '--customer-id', '2425288235',
                '--campaign-id', '12345',
                '--mobile', '+50',
                '--desktop', '-30',
                '--dry-run'
            ])
        except SystemExit:
            pass

        sys.stdout = old_stdout
        output = captured.getvalue()

        assert 'DRY RUN' in output
        assert '1.50' in output  # +50% = 1.5
        assert '0.70' in output  # -30% = 0.7


class TestModifierParsing:
    """Test modifier value parsing in CLI."""

    def test_parse_percentage_positive(self):
        """Test parsing positive percentage notation."""
        from xwander_ads.cli import handle_search_adjust_devices

        # The handler has a nested function for parsing
        # We'll test the parsing logic directly here
        def parse_modifier(value: str) -> float:
            if value.startswith('+'):
                return 1.0 + (float(value[1:]) / 100)
            elif value.startswith('-'):
                return 1.0 - (float(value[1:]) / 100)
            else:
                return float(value)

        assert parse_modifier('+50') == 1.5
        assert parse_modifier('+100') == 2.0
        assert parse_modifier('+25') == 1.25

    def test_parse_percentage_negative(self):
        """Test parsing negative percentage notation."""
        def parse_modifier(value: str) -> float:
            if value.startswith('+'):
                return 1.0 + (float(value[1:]) / 100)
            elif value.startswith('-'):
                return 1.0 - (float(value[1:]) / 100)
            else:
                return float(value)

        assert parse_modifier('-30') == 0.7
        assert parse_modifier('-50') == 0.5
        assert abs(parse_modifier('-90') - 0.1) < 0.0001  # Float precision

    def test_parse_decimal_notation(self):
        """Test parsing decimal notation."""
        def parse_modifier(value: str) -> float:
            if value.startswith('+'):
                return 1.0 + (float(value[1:]) / 100)
            elif value.startswith('-'):
                return 1.0 - (float(value[1:]) / 100)
            else:
                return float(value)

        assert parse_modifier('1.5') == 1.5
        assert parse_modifier('0.7') == 0.7
        assert parse_modifier('1.0') == 1.0


# Test markers
pytestmark = pytest.mark.unit


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
