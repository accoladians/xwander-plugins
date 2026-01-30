"""Tests for transforms module."""

import pytest
from unittest.mock import MagicMock, patch, call

from xwander_airtable.transforms import Transforms, TransformResult
from xwander_airtable.formula import F


@pytest.fixture
def mock_client():
    """Create a mock AirtableClient."""
    client = MagicMock()
    # Schema for select field detection
    client.get_table_schema.return_value = {
        "id": "tbl123",
        "name": "Events",
        "fields": [
            {"id": "fld1", "name": "Name", "type": "singleLineText"},
            {
                "id": "fld2",
                "name": "Track",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"id": "sel1", "name": "Academy", "color": "greenLight2"},
                        {"id": "sel2", "name": "Day Tours", "color": "yellowLight2"},
                    ]
                },
            },
            {"id": "fld3", "name": "Notes", "type": "multilineText"},
        ],
    }
    return client


@pytest.fixture
def transforms(mock_client):
    return Transforms(mock_client)


class TestRenameValues:
    def test_select_field_uses_field_rename(self, transforms):
        """Select fields should rename at field level, not record level."""
        transforms.client.request.return_value = {"id": "fld2"}
        transforms.client.list_records.return_value = [
            {"id": "rec1", "fields": {"Track": "Holiday Packages"}},
            {"id": "rec2", "fields": {"Track": "Holiday Packages"}},
        ]

        result = transforms.rename_values(
            "app123", "Events", "Track", "Academy", "Holiday Packages"
        )

        assert result.method == "field_rename"
        assert result.field_updated is True
        assert result.records_affected == 2

    def test_text_field_uses_batch_update(self, transforms):
        """Text fields should use batch record update."""
        transforms.client.list_records.return_value = [
            {"id": "rec1", "fields": {"Notes": "old text"}},
            {"id": "rec2", "fields": {"Notes": "old text"}},
        ]
        mock_batch_result = MagicMock()
        mock_batch_result.successful = 2
        mock_batch_result.total = 2
        mock_batch_result.duration_seconds = 0.5
        transforms.client.batch_update.return_value = mock_batch_result

        result = transforms.rename_values(
            "app123", "Events", "Notes", "old text", "new text"
        )

        assert result.method == "record_update"
        assert result.records_affected == 2
        transforms.client.batch_update.assert_called_once()


class TestSetValuesWhere:
    def test_set_values_matching_formula(self, transforms):
        transforms.client.list_records.return_value = [
            {"id": "rec1", "fields": {"Status": "Active"}},
            {"id": "rec2", "fields": {"Status": "Active"}},
        ]
        mock_result = MagicMock()
        mock_result.successful = 2
        transforms.client.batch_update.return_value = mock_result

        result = transforms.set_values_where(
            "app123", "Events", "Status", "Done",
            formula=F.equals("Track", "Academy")
        )

        # Should have called list_records with formula
        transforms.client.list_records.assert_called_once()
        # Should have called batch_update with updates
        transforms.client.batch_update.assert_called_once()
        updates = transforms.client.batch_update.call_args[1].get("updates") or \
                  transforms.client.batch_update.call_args[0][2]
        assert all(u["fields"]["Status"] == "Done" for u in updates)

    def test_no_matching_records(self, transforms):
        transforms.client.list_records.return_value = []

        result = transforms.set_values_where(
            "app123", "Events", "Status", "Done",
            formula=F.equals("Track", "NonExistent")
        )

        assert result.records_affected == 0
        transforms.client.batch_update.assert_not_called()


class TestCopyField:
    def test_copy_field_values(self, transforms):
        transforms.client.list_records.return_value = [
            {"id": "rec1", "fields": {"Name": "Event A"}},
            {"id": "rec2", "fields": {"Name": "Event B"}},
        ]
        mock_result = MagicMock()
        mock_result.successful = 2
        transforms.client.batch_update.return_value = mock_result

        result = transforms.copy_field(
            "app123", "Events", "Name", "Display Name"
        )

        transforms.client.batch_update.assert_called_once()
        updates = transforms.client.batch_update.call_args[0][2]
        assert updates[0]["fields"]["Display Name"] == "Event A"
        assert updates[1]["fields"]["Display Name"] == "Event B"

    def test_copy_with_transform(self, transforms):
        transforms.client.list_records.return_value = [
            {"id": "rec1", "fields": {"Name": "event a"}},
        ]
        mock_result = MagicMock()
        mock_result.successful = 1
        transforms.client.batch_update.return_value = mock_result

        result = transforms.copy_field(
            "app123", "Events", "Name", "Display Name",
            transform_fn=str.upper
        )

        updates = transforms.client.batch_update.call_args[0][2]
        assert updates[0]["fields"]["Display Name"] == "EVENT A"

    def test_skip_none_values(self, transforms):
        transforms.client.list_records.return_value = [
            {"id": "rec1", "fields": {"Name": "Event A"}},
            {"id": "rec2", "fields": {}},  # Missing Name field
        ]
        mock_result = MagicMock()
        mock_result.successful = 1
        transforms.client.batch_update.return_value = mock_result

        result = transforms.copy_field(
            "app123", "Events", "Name", "Display Name"
        )

        updates = transforms.client.batch_update.call_args[0][2]
        assert len(updates) == 1  # Only rec1, rec2 skipped


class TestTransformResult:
    def test_field_rename_str(self):
        r = TransformResult(method="field_rename", records_affected=78)
        assert "field_rename" in str(r)
        assert "78" in str(r)

    def test_record_update_str(self):
        mock_batch = MagicMock()
        mock_batch.successful = 10
        mock_batch.total = 12
        mock_batch.duration_seconds = 2.5
        r = TransformResult(method="record_update", batch_result=mock_batch)
        assert "record_update" in str(r)
        assert "10/12" in str(r)
