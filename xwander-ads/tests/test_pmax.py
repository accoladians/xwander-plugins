"""Integration tests for Performance Max module.

These tests verify the PMax module works correctly with the Google Ads API.
They use the production Xwander Nordic account for real integration testing.

Run with:
    cd /srv/plugins/xwander-ads
    python3 -m pytest tests/test_pmax.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from google.ads.googleads.errors import GoogleAdsException

from xwander_ads.auth import get_client
from xwander_ads.pmax import (
    campaigns,
    signals
)
from xwander_ads.exceptions import (
    AssetGroupNotFoundError,
    CampaignNotFoundError,
    DuplicateSignalError,
    APIError,
    QuotaExceededError
)


# Test configuration
CUSTOMER_ID = "2425288235"
CAMPAIGN_ID = "23423204148"
ASSET_GROUP_ID = "6655152002"  # EN asset group


class TestAuthentication:
    """Test authentication and client creation."""

    def test_get_client_default_version(self):
        """Test client creation with default API version."""
        client = get_client()
        assert client is not None

    def test_get_client_specific_version(self):
        """Test client creation with specific API version."""
        client = get_client(version="v22")
        assert client is not None

    def test_get_client_invalid_config_raises_error(self):
        """Test that missing config raises AuthenticationError."""
        from xwander_ads.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            get_client(config_path="/nonexistent/path/google-ads.yaml")


class TestCampaigns:
    """Test campaign management functions."""

    @pytest.fixture
    def client(self):
        """Get authenticated client for tests."""
        return get_client()

    def test_list_campaigns(self, client):
        """Test listing Performance Max campaigns."""
        campaign_list = campaigns.list_campaigns(client, CUSTOMER_ID)

        assert isinstance(campaign_list, list)
        assert len(campaign_list) > 0

        # Check first campaign structure
        campaign = campaign_list[0]
        assert 'id' in campaign
        assert 'name' in campaign
        assert 'status' in campaign
        assert 'budget_micros' in campaign

    def test_list_campaigns_enabled_only(self, client):
        """Test listing only enabled campaigns."""
        campaign_list = campaigns.list_campaigns(client, CUSTOMER_ID, enabled_only=True)

        assert isinstance(campaign_list, list)
        # All campaigns should be ENABLED
        for campaign in campaign_list:
            assert campaign['status'] == 'ENABLED'

    def test_get_campaign(self, client):
        """Test getting specific campaign details."""
        campaign = campaigns.get_campaign(client, CUSTOMER_ID, CAMPAIGN_ID)

        assert campaign is not None
        assert campaign['id'] == int(CAMPAIGN_ID)
        assert 'name' in campaign
        assert 'budget_micros' in campaign
        assert 'resource_name' in campaign

    def test_get_campaign_not_found_raises_error(self, client):
        """Test that non-existent campaign raises CampaignNotFoundError."""
        with pytest.raises(CampaignNotFoundError):
            campaigns.get_campaign(client, CUSTOMER_ID, "9999999999")

    def test_list_asset_groups(self, client):
        """Test listing asset groups."""
        asset_groups = campaigns.list_asset_groups(client, CUSTOMER_ID)

        assert isinstance(asset_groups, list)
        assert len(asset_groups) > 0

        # Check structure
        ag = asset_groups[0]
        assert 'id' in ag
        assert 'name' in ag
        assert 'campaign_id' in ag
        assert 'status' in ag

    def test_list_asset_groups_filtered_by_campaign(self, client):
        """Test listing asset groups filtered by campaign."""
        asset_groups = campaigns.list_asset_groups(
            client, CUSTOMER_ID, campaign_id=CAMPAIGN_ID
        )

        assert isinstance(asset_groups, list)
        # All should belong to the specified campaign
        for ag in asset_groups:
            assert ag['campaign_id'] == CAMPAIGN_ID

    def test_get_campaign_stats(self, client):
        """Test getting campaign statistics."""
        stats = campaigns.get_campaign_stats(
            client, CUSTOMER_ID, CAMPAIGN_ID, date_range="LAST_7_DAYS"
        )

        assert stats is not None
        assert 'campaign_id' in stats
        assert 'cost_micros' in stats
        assert 'impressions' in stats
        assert 'clicks' in stats
        assert 'conversions' in stats


class TestSignals:
    """Test signal management functions."""

    @pytest.fixture
    def client(self):
        """Get authenticated client for tests."""
        return get_client()

    def test_list_signals(self, client):
        """Test listing search themes."""
        signal_list = signals.list_signals(client, CUSTOMER_ID, ASSET_GROUP_ID)

        assert isinstance(signal_list, list)
        # Should have at least some signals
        if len(signal_list) > 0:
            signal = signal_list[0]
            assert 'resource_name' in signal
            assert 'text' in signal

    def test_list_signals_invalid_asset_group_raises_error(self, client):
        """Test that invalid asset group raises AssetGroupNotFoundError."""
        with pytest.raises(AssetGroupNotFoundError):
            signals.list_signals(client, CUSTOMER_ID, "9999999999")

    def test_add_and_remove_search_theme(self, client):
        """Test adding and removing a search theme (integration test)."""
        test_theme = "test theme integration test 2026"

        # Add theme
        try:
            resource_name = signals.add_search_theme(
                client, CUSTOMER_ID, ASSET_GROUP_ID, test_theme
            )
            assert resource_name is not None
            assert 'assetGroupSignals' in resource_name

            # Verify it was added
            signal_list = signals.list_signals(client, CUSTOMER_ID, ASSET_GROUP_ID)
            themes = [s['text'] for s in signal_list]
            assert test_theme in themes

        finally:
            # Clean up - remove the test theme
            try:
                signal_list = signals.list_signals(client, CUSTOMER_ID, ASSET_GROUP_ID)
                test_signal = next(
                    (s for s in signal_list if s['text'] == test_theme),
                    None
                )
                if test_signal:
                    signals.remove_signal(
                        client, CUSTOMER_ID, test_signal['resource_name']
                    )
            except Exception:
                pass  # Best effort cleanup

    def test_add_duplicate_theme_raises_error(self, client):
        """Test that adding duplicate theme raises DuplicateSignalError."""
        # Get existing theme
        signal_list = signals.list_signals(client, CUSTOMER_ID, ASSET_GROUP_ID)
        if len(signal_list) == 0:
            pytest.skip("No existing signals to test duplicate")

        existing_theme = signal_list[0]['text']

        # Try to add duplicate
        with pytest.raises(DuplicateSignalError):
            signals.add_search_theme(
                client, CUSTOMER_ID, ASSET_GROUP_ID, existing_theme
            )

    def test_bulk_add_themes(self, client):
        """Test bulk adding themes."""
        test_themes = [
            "bulk test theme 1 2026",
            "bulk test theme 2 2026",
            "bulk test theme 3 2026"
        ]

        try:
            # Add themes
            results = signals.bulk_add_themes(
                client, CUSTOMER_ID, ASSET_GROUP_ID, test_themes
            )

            assert len(results) == len(test_themes)

            # Verify they were added
            signal_list = signals.list_signals(client, CUSTOMER_ID, ASSET_GROUP_ID)
            signal_texts = [s['text'] for s in signal_list]

            for theme in test_themes:
                assert theme in signal_texts

        finally:
            # Clean up
            try:
                signal_list = signals.list_signals(client, CUSTOMER_ID, ASSET_GROUP_ID)
                for theme in test_themes:
                    test_signal = next(
                        (s for s in signal_list if s['text'] == theme),
                        None
                    )
                    if test_signal:
                        signals.remove_signal(
                            client, CUSTOMER_ID, test_signal['resource_name']
                        )
            except Exception:
                pass  # Best effort cleanup

    def test_bulk_add_themes_with_empty_lines(self, client):
        """Test bulk add handles empty lines correctly."""
        test_themes = [
            "bulk test non-empty 2026",
            "",
            "   ",
            "bulk test non-empty 2 2026"
        ]

        try:
            results = signals.bulk_add_themes(
                client, CUSTOMER_ID, ASSET_GROUP_ID, test_themes
            )

            # Should only add non-empty themes
            assert len(results) == 2

        finally:
            # Clean up
            try:
                signal_list = signals.list_signals(client, CUSTOMER_ID, ASSET_GROUP_ID)
                for theme in ["bulk test non-empty 2026", "bulk test non-empty 2 2026"]:
                    test_signal = next(
                        (s for s in signal_list if s['text'] == theme),
                        None
                    )
                    if test_signal:
                        signals.remove_signal(
                            client, CUSTOMER_ID, test_signal['resource_name']
                        )
            except Exception:
                pass

    def test_get_signal_stats(self, client):
        """Test getting signal statistics."""
        stats = signals.get_signal_stats(client, CUSTOMER_ID, ASSET_GROUP_ID)

        assert 'asset_group_id' in stats
        assert 'total_signals' in stats
        assert 'search_themes' in stats
        assert 'signals' in stats

        assert stats['asset_group_id'] == ASSET_GROUP_ID
        assert isinstance(stats['total_signals'], int)
        assert isinstance(stats['search_themes'], list)


class TestExceptionHandling:
    """Test exception handling and error cases."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing error handling."""
        client = Mock()
        return client

    def test_asset_group_not_found_error(self):
        """Test AssetGroupNotFoundError attributes."""
        error = AssetGroupNotFoundError("Test error")
        assert error.exit_code == 4
        assert str(error) == "Test error"

    def test_campaign_not_found_error(self):
        """Test CampaignNotFoundError attributes."""
        error = CampaignNotFoundError("Test error")
        assert error.exit_code == 4
        assert str(error) == "Test error"

    def test_duplicate_signal_error(self):
        """Test DuplicateSignalError attributes."""
        error = DuplicateSignalError("Test error")
        assert error.exit_code == 5
        assert str(error) == "Test error"

    def test_quota_exceeded_error(self):
        """Test QuotaExceededError attributes."""
        error = QuotaExceededError("Test error")
        assert error.exit_code == 2
        assert str(error) == "Test error"

    def test_api_error(self):
        """Test APIError attributes."""
        error = APIError("Test error")
        assert error.exit_code == 1
        assert str(error) == "Test error"


class TestCLINormalization:
    """Test CLI helper functions."""

    def test_normalize_customer_id(self):
        """Test customer ID normalization."""
        from xwander_ads.cli import normalize_customer_id

        assert normalize_customer_id("2425288235") == "2425288235"
        assert normalize_customer_id("242-528-8235") == "2425288235"
        assert normalize_customer_id("242-528-8235") == normalize_customer_id("2425288235")

    def test_format_micros(self):
        """Test micros formatting."""
        from xwander_ads.cli import format_micros

        assert format_micros(1_000_000) == "EUR 1.00"
        assert format_micros(1_234_560_000) == "EUR 1,234.56"
        assert format_micros(0) == "EUR 0.00"
        assert format_micros(1_000_000, "USD") == "USD 1.00"


# Test markers
pytestmark = pytest.mark.integration


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
