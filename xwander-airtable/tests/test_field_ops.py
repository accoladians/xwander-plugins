"""Tests for field operations module."""

import pytest
from unittest.mock import MagicMock, patch

from xwander_airtable.field_ops import FieldOperations, VALID_COLORS, SELECT_TYPES
from xwander_airtable.exceptions import ValidationError, NotFoundError


@pytest.fixture
def mock_client():
    """Create a mock AirtableClient."""
    client = MagicMock()
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
                        {"id": "sel3", "name": "Week Packages", "color": "orangeLight2"},
                    ]
                },
            },
            {
                "id": "fld3",
                "name": "Tags",
                "type": "multipleSelects",
                "options": {
                    "choices": [
                        {"id": "sel4", "name": "Featured", "color": "blueLight2"},
                    ]
                },
            },
        ],
    }
    return client


@pytest.fixture
def ops(mock_client):
    return FieldOperations(mock_client)


class TestGetFieldInfo:
    def test_get_existing_field(self, ops):
        info = ops.get_field_info("app123", "Events", "Track")
        assert info["id"] == "fld2"
        assert info["type"] == "singleSelect"

    def test_get_nonexistent_field(self, ops):
        with pytest.raises(NotFoundError):
            ops.get_field_info("app123", "Events", "DoesNotExist")

    def test_get_nonexistent_table(self, ops):
        ops.client.get_table_schema.return_value = None
        with pytest.raises(NotFoundError):
            ops.get_field_info("app123", "Missing", "Track")


class TestGetOptions:
    def test_get_options(self, ops):
        options = ops.get_options("app123", "Events", "Track")
        assert len(options) == 3
        assert options[0]["name"] == "Academy"

    def test_non_select_field_raises(self, ops):
        with pytest.raises(ValidationError, match="not a select field"):
            ops.get_options("app123", "Events", "Name")


class TestRenameOption:
    def test_rename_builds_correct_payload(self, ops):
        ops.client.request.return_value = {"id": "fld2", "name": "Track"}
        ops.rename_option("app123", "Events", "Track", "Week Packages", "Holiday Packages")

        ops.client.request.assert_called_once()
        call_args = ops.client.request.call_args
        assert call_args[0][0] == "PATCH"
        payload = call_args[1]["json"]
        choices = payload["options"]["choices"]

        # sel3 should be renamed
        renamed = [c for c in choices if c["id"] == "sel3"][0]
        assert renamed["name"] == "Holiday Packages"

        # Others unchanged
        academy = [c for c in choices if c["id"] == "sel1"][0]
        assert academy["name"] == "Academy"

    def test_rename_nonexistent_raises(self, ops):
        with pytest.raises(NotFoundError):
            ops.rename_option("app123", "Events", "Track", "NoSuchOption", "New")

    def test_rename_to_existing_raises(self, ops):
        with pytest.raises(ValidationError, match="already exists"):
            ops.rename_option("app123", "Events", "Track", "Academy", "Day Tours")

    def test_rename_invalidates_cache(self, ops):
        ops.client.request.return_value = {"id": "fld2"}
        ops.rename_option("app123", "Events", "Track", "Week Packages", "Holiday Packages")
        ops.client.invalidate_cache.assert_called_once_with("app123")


class TestAddOption:
    def test_add_option_payload(self, ops):
        ops.client.request.return_value = {"id": "fld2"}
        ops.add_option("app123", "Events", "Track", "Erasmus+", color="blueLight2")

        call_args = ops.client.request.call_args
        payload = call_args[1]["json"]
        choices = payload["options"]["choices"]

        # 3 existing + 1 new
        assert len(choices) == 4
        new_choice = choices[-1]
        assert new_choice["name"] == "Erasmus+"
        assert new_choice["color"] == "blueLight2"
        assert "id" not in new_choice  # New options don't have IDs

    def test_add_duplicate_raises(self, ops):
        with pytest.raises(ValidationError, match="already exists"):
            ops.add_option("app123", "Events", "Track", "Academy")

    def test_add_invalid_color_raises(self, ops):
        with pytest.raises(ValidationError, match="Invalid color"):
            ops.add_option("app123", "Events", "Track", "New", color="neonPink")


class TestDeleteOption:
    def test_delete_option(self, ops):
        ops.client.request.return_value = {"id": "fld2"}
        ops.delete_option("app123", "Events", "Track", "Week Packages")

        call_args = ops.client.request.call_args
        payload = call_args[1]["json"]
        choices = payload["options"]["choices"]

        # 3 - 1 = 2 remaining
        assert len(choices) == 2
        names = [c["name"] for c in choices]
        assert "Week Packages" not in names
        assert "Academy" in names

    def test_delete_nonexistent_raises(self, ops):
        with pytest.raises(NotFoundError):
            ops.delete_option("app123", "Events", "Track", "NoSuch")


class TestReorderOptions:
    def test_reorder(self, ops):
        ops.client.request.return_value = {"id": "fld2"}
        ops.reorder_options("app123", "Events", "Track",
                            ["Week Packages", "Day Tours", "Academy"])

        call_args = ops.client.request.call_args
        payload = call_args[1]["json"]
        choices = payload["options"]["choices"]

        assert choices[0]["name"] == "Week Packages"
        assert choices[1]["name"] == "Day Tours"
        assert choices[2]["name"] == "Academy"

    def test_reorder_nonexistent_raises(self, ops):
        with pytest.raises(NotFoundError):
            ops.reorder_options("app123", "Events", "Track",
                                ["NoSuch", "Academy"])


class TestValidColors:
    def test_light_colors(self):
        assert "blueLight2" in VALID_COLORS
        assert "orangeLight2" in VALID_COLORS

    def test_bright_colors(self):
        assert "greenBright" in VALID_COLORS

    def test_dark_colors(self):
        assert "redDark1" in VALID_COLORS
