"""
Tests for Conversion Action Manager

Tests conversion action CRUD operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from xwander_ads.conversions.actions import ConversionActionManager
from xwander_ads.exceptions import GoogleAdsError


class TestConversionActionManager:
    """Test ConversionActionManager"""

    @pytest.fixture
    def mock_client(self):
        """Create mock GoogleAdsClient"""
        client = Mock()
        client.get_service = Mock()
        client.get_type = Mock()
        client.enums = Mock()

        # Mock enums
        client.enums.ConversionActionTypeEnum = Mock()
        client.enums.ConversionActionCategoryEnum = Mock()
        client.enums.ConversionActionStatusEnum = Mock()
        client.enums.ConversionActionCountingTypeEnum = Mock()

        return client

    @pytest.fixture
    def manager(self, mock_client):
        """Create ConversionActionManager with mocked client"""
        return ConversionActionManager(mock_client)

    def test_extract_tag_info_valid(self, manager):
        """Test extracting conversion ID and label from tag snippet"""
        mock_conv = Mock()
        mock_snippet = Mock()
        mock_snippet.type_.name = "WEBPAGE"
        mock_snippet.event_snippet = """
            gtag('event', 'conversion', {
                'send_to': 'AW-2425288235/AbC123xYz',
                'value': 1.0,
                'currency': 'EUR'
            });
        """

        mock_conv.tag_snippets = [mock_snippet]

        result = manager._extract_tag_info(mock_conv)

        assert result['conversion_id'] == '2425288235'
        assert result['conversion_label'] == 'AbC123xYz'
        assert result['type'] == 'WEBPAGE'

    def test_extract_tag_info_no_snippets(self, manager):
        """Test extracting tag info when no snippets present"""
        mock_conv = Mock()
        mock_conv.tag_snippets = []

        result = manager._extract_tag_info(mock_conv)

        assert result == {}

    def test_list_conversions_filters(self, manager, mock_client):
        """Test list_conversions with various filters"""
        mock_service = Mock()
        mock_client.get_service.return_value = mock_service

        # Mock response
        mock_conv = Mock()
        mock_conv.id = 123456
        mock_conv.name = "Test Conversion"
        mock_conv.type_.name = "WEBPAGE"
        mock_conv.category.name = "PURCHASE"
        mock_conv.status.name = "ENABLED"
        mock_conv.primary_for_goal = True
        mock_conv.counting_type.name = "ONE_PER_CLICK"
        mock_conv.click_through_lookback_window_days = 90
        mock_conv.view_through_lookback_window_days = 1
        mock_conv.value_settings.default_value = 50.0
        mock_conv.value_settings.always_use_default_value = True
        mock_conv.tag_snippets = []

        mock_row = Mock()
        mock_row.conversion_action = mock_conv

        mock_service.search.return_value = [mock_row]

        # Test list all
        results = manager.list_conversions("123456")

        assert len(results) == 1
        assert results[0]['id'] == 123456
        assert results[0]['name'] == "Test Conversion"
        assert results[0]['type'] == "WEBPAGE"

        # Verify query contains WHERE clause to exclude removed
        call_args = mock_service.search.call_args
        assert "REMOVED" in call_args.kwargs['query']

    def test_get_conversion_labels_webpage_only(self, manager, mock_client):
        """Test get_conversion_labels filters WEBPAGE types"""
        mock_service = Mock()
        mock_client.get_service.return_value = mock_service

        # Mock two conversions: one WEBPAGE, one UPLOAD_CLICKS
        mock_conv1 = Mock()
        mock_conv1.id = 111
        mock_conv1.name = "Webpage Conv"
        mock_conv1.type_.name = "WEBPAGE"
        mock_conv1.status.name = "ENABLED"
        mock_conv1.category.name = "PURCHASE"
        mock_conv1.tag_snippets = []

        mock_conv2 = Mock()
        mock_conv2.id = 222
        mock_conv2.name = "Upload Conv"
        mock_conv2.type_.name = "UPLOAD_CLICKS"
        mock_conv2.status.name = "ENABLED"
        mock_conv2.category.name = "PURCHASE"
        mock_conv2.tag_snippets = []

        # Mock other required fields
        for conv in [mock_conv1, mock_conv2]:
            conv.primary_for_goal = True
            conv.counting_type.name = "ONE_PER_CLICK"
            conv.click_through_lookback_window_days = 90
            conv.view_through_lookback_window_days = 1
            conv.value_settings.default_value = 0
            conv.value_settings.always_use_default_value = False

        mock_row1 = Mock()
        mock_row1.conversion_action = mock_conv1
        mock_row2 = Mock()
        mock_row2.conversion_action = mock_conv2

        mock_service.search.return_value = [mock_row1, mock_row2]

        # Get labels with webpage_only=True
        labels = manager.get_conversion_labels("123456", webpage_only=True)

        # Should only include WEBPAGE conversion
        assert len(labels) == 1
        assert "Webpage Conv" in labels
        assert "Upload Conv" not in labels

    def test_create_conversion_success(self, manager, mock_client):
        """Test successful conversion creation"""
        mock_conversion_service = Mock()
        mock_ga_service = Mock()

        mock_client.get_service.side_effect = lambda name: (
            mock_conversion_service if name == "ConversionActionService"
            else mock_ga_service
        )

        # Mock create response
        mock_result = Mock()
        mock_result.resource_name = "customers/123456/conversionActions/789012"

        mock_response = Mock()
        mock_response.results = [mock_result]

        mock_conversion_service.mutate_conversion_actions.return_value = mock_response

        # Mock label query response
        mock_conv = Mock()
        mock_snippet = Mock()
        mock_snippet.event_snippet = "'send_to': 'AW-123456/TestLabel'"
        mock_conv.tag_snippets = [Mock(type_=Mock(name="WEBPAGE"), event_snippet=mock_snippet.event_snippet)]

        mock_row = Mock()
        mock_row.conversion_action = mock_conv

        mock_ga_service.search.return_value = [mock_row]

        # Mock get_type for operation
        mock_operation = Mock()
        mock_operation.create = Mock()
        mock_client.get_type.return_value = mock_operation

        # Create conversion
        result = manager.create_conversion(
            customer_id="123456",
            name="Test Purchase",
            category="PURCHASE",
            value=100
        )

        assert result['success'] is True
        assert result['action_id'] == "789012"
        assert result['name'] == "Test Purchase"

    def test_update_conversion_status(self, manager, mock_client):
        """Test updating conversion status"""
        mock_service = Mock()
        mock_client.get_service.return_value = mock_service

        # Mock successful response
        mock_response = Mock()
        mock_service.mutate_conversion_actions.return_value = mock_response

        # Mock update operation
        mock_operation = Mock()
        mock_operation.update = Mock()
        mock_client.get_type.return_value = mock_operation

        result = manager.update_conversion(
            customer_id="123456",
            conversion_id="789012",
            status="PAUSED"
        )

        assert result['success'] is True
        assert 'status' in result['updated_fields']

    def test_remove_conversion(self, manager):
        """Test removing (disabling) a conversion"""
        with patch.object(manager, 'update_conversion') as mock_update:
            mock_update.return_value = {'success': True}

            result = manager.remove_conversion("123456", "789012")

            # Should call update_conversion with status=REMOVED
            mock_update.assert_called_once_with(
                customer_id="123456",
                conversion_id="789012",
                status="REMOVED"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
