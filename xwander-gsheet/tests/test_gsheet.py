#!/usr/bin/env python3
"""
Unit tests for gsheet.py v2.0

Tests the section-based Google Sheets abstraction.
Run with: python3 -m pytest test_gsheet.py -v
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest

# Import the module under test
from xwander_gsheet import GSheet, GSheetAuth


class TestGSheetInit:
    """Test GSheet initialization."""

    def test_init_default(self):
        """Test default initialization."""
        sheet = GSheet()
        assert sheet._spreadsheet_id is None
        assert sheet._worksheet_name == "Sheet1"
        assert sheet._meta['version'] == "2.0.0"
        assert sheet._sections == {}
        assert sheet._section_order == []

    def test_init_with_id(self):
        """Test initialization with spreadsheet ID."""
        sheet = GSheet(spreadsheet_id="abc123", worksheet_name="Test")
        assert sheet._spreadsheet_id == "abc123"
        assert sheet._worksheet_name == "Test"


class TestGSheetSections:
    """Test section operations."""

    def test_set_title(self):
        """Test title section."""
        sheet = GSheet()
        sheet.set_title("TEST TITLE")

        assert 'title' in sheet._sections
        assert sheet._sections['title']['type'] == 'title'
        assert sheet._sections['title']['rows'][0]['cells'][0]['value'] == "TEST TITLE"
        assert 'title' in sheet._section_order
        assert sheet._section_order[0] == 'title'

    def test_add_summary_row(self):
        """Test summary section."""
        sheet = GSheet()
        sheet.add_summary_row("Total Investment", 1791.22, format='currency')
        sheet.add_summary_row("Margin %", 42.5, format='percentage')

        assert 'summary' in sheet._sections
        assert sheet._sections['summary']['type'] == 'key_value'
        assert len(sheet._sections['summary']['rows']) == 2
        assert sheet._sections['summary']['rows'][0]['key'] == "Total Investment"
        assert sheet._sections['summary']['rows'][0]['value'] == 1791.22
        assert sheet._sections['summary']['rows'][0]['format'] == 'currency'

    def test_set_header(self):
        """Test header section."""
        sheet = GSheet()
        columns = ['Priority', 'SKU', 'Product', 'Qty']
        sheet.set_header(columns)

        assert 'header' in sheet._sections
        assert sheet._sections['header']['type'] == 'header'
        assert sheet._sections['header']['rows'][0]['cells'] == columns
        assert sheet._sections['header']['rows'][0]['freeze'] is True

    def test_add_data_row(self):
        """Test data section."""
        sheet = GSheet()
        data = {'priority': 'P0', 'product': 'Widget', 'qty': 15}
        sheet.add_data_row(data)

        assert 'data' in sheet._sections
        assert sheet._sections['data']['type'] == 'table'
        assert len(sheet._sections['data']['rows']) == 1
        assert sheet._sections['data']['rows'][0] == data
        # Auto-detected columns
        assert len(sheet._sections['data']['columns']) == 3

    def test_add_footer_line(self):
        """Test footer section."""
        sheet = GSheet()
        sheet.add_footer_line("CRITICAL ACTIONS")
        sheet.add_footer_line("1. Review before ordering")

        assert 'footer' in sheet._sections
        assert sheet._sections['footer']['type'] == 'text_block'
        assert len(sheet._sections['footer']['rows']) == 2

    def test_section_order(self):
        """Test section ordering."""
        sheet = GSheet()
        sheet.set_header(['A', 'B'])
        sheet.set_title("TITLE")
        sheet.add_data_row({'a': 1, 'b': 2})
        sheet.add_summary_row("Total", 100)

        # Title should be first despite being added second
        assert sheet._section_order[0] == 'title'
        # Summary after title
        assert sheet._section_order[1] == 'summary'


class TestGSheetDataOperations:
    """Test data CRUD operations."""

    def test_find_data_rows(self):
        """Test finding rows by criteria."""
        sheet = GSheet()
        sheet.add_data_row({'priority': 'P0', 'product': 'Widget A', 'qty': 10})
        sheet.add_data_row({'priority': 'P1', 'product': 'Widget B', 'qty': 5})
        sheet.add_data_row({'priority': 'P0', 'product': 'Widget C', 'qty': 15})

        p0_rows = sheet.find_data_rows({'priority': 'P0'})
        assert len(p0_rows) == 2
        assert p0_rows[0]['product'] == 'Widget A'
        assert p0_rows[1]['product'] == 'Widget C'

    def test_find_data_rows_no_match(self):
        """Test finding rows with no matches."""
        sheet = GSheet()
        sheet.add_data_row({'priority': 'P0', 'product': 'Widget', 'qty': 10})

        result = sheet.find_data_rows({'priority': 'P2'})
        assert result == []

    def test_update_data_row(self):
        """Test updating rows by criteria."""
        sheet = GSheet()
        sheet.add_data_row({'priority': 'P0', 'product': 'Widget', 'qty': 10})
        sheet.add_data_row({'priority': 'P1', 'product': 'Gadget', 'qty': 5})

        count = sheet.update_data_row(
            match={'product': 'Widget'},
            updates={'priority': 'P1', 'qty': 20}
        )

        assert count == 1
        assert sheet._sections['data']['rows'][0]['priority'] == 'P1'
        assert sheet._sections['data']['rows'][0]['qty'] == 20

    def test_update_data_row_multiple(self):
        """Test updating multiple matching rows."""
        sheet = GSheet()
        sheet.add_data_row({'priority': 'P0', 'product': 'Widget A', 'qty': 10})
        sheet.add_data_row({'priority': 'P0', 'product': 'Widget B', 'qty': 15})
        sheet.add_data_row({'priority': 'P1', 'product': 'Widget C', 'qty': 5})

        count = sheet.update_data_row(
            match={'priority': 'P0'},
            updates={'priority': 'P1'}
        )

        assert count == 2


class TestGSheetJsonState:
    """Test JSON state persistence."""

    def test_save_and_load(self):
        """Test saving and loading JSON state."""
        sheet = GSheet(spreadsheet_id="test123", worksheet_name="Sheet1")
        sheet.set_title("TEST")
        sheet.add_summary_row("Total", 100, format='currency')
        sheet.set_header(['A', 'B', 'C'])
        sheet.add_data_row({'a': 1, 'b': 2, 'c': 3})

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            sheet.save(json_path)

            # Load and verify
            loaded = GSheet.load(json_path)
            assert loaded._spreadsheet_id == "test123"
            assert loaded._worksheet_name == "Sheet1"
            assert 'title' in loaded._sections
            assert 'summary' in loaded._sections
            assert 'header' in loaded._sections
            assert 'data' in loaded._sections
            assert len(loaded._sections['data']['rows']) == 1

        finally:
            os.unlink(json_path)


class TestGSheetRowBuilding:
    """Test row building for sync."""

    def test_build_title_rows(self):
        """Test title row building."""
        sheet = GSheet()
        sheet.set_title("TEST TITLE")

        rows = sheet._build_section_rows(sheet._sections['title'])
        assert rows == [["TEST TITLE"]]

    def test_build_summary_rows(self):
        """Test summary row building."""
        sheet = GSheet()
        sheet.add_summary_row("Total", 100, format='currency')
        sheet.add_summary_row("Count", 5)

        rows = sheet._build_section_rows(sheet._sections['summary'])
        assert len(rows) == 2
        assert rows[0] == ["Total", 100.0]
        assert rows[1] == ["Count", 5]

    def test_build_header_rows(self):
        """Test header row building."""
        sheet = GSheet()
        sheet.set_header(['A', 'B', 'C'])

        rows = sheet._build_section_rows(sheet._sections['header'])
        assert rows == [['A', 'B', 'C']]

    def test_build_data_rows(self):
        """Test data row building."""
        sheet = GSheet()
        sheet.add_data_row({'a': 1, 'b': 2})
        sheet.add_data_row({'a': 3, 'b': 4})

        rows = sheet._build_section_rows(sheet._sections['data'])
        assert rows == [[1, 2], [3, 4]]


class TestGSheetFormatting:
    """Test value formatting."""

    def test_format_currency(self):
        """Test currency formatting."""
        sheet = GSheet()
        result = sheet._format_value(100.5, 'currency')
        assert result == 100.5  # Number, not string

    def test_format_percentage(self):
        """Test percentage formatting."""
        sheet = GSheet()
        result = sheet._format_value(42.5, 'percentage')
        assert result == 0.425  # Converted to decimal

    def test_format_number(self):
        """Test number formatting."""
        sheet = GSheet()
        result = sheet._format_value("100", 'number')
        assert result == 100.0

    def test_format_none(self):
        """Test None value formatting."""
        sheet = GSheet()
        result = sheet._format_value(None, 'currency')
        assert result == ''


class TestGSheetHelpers:
    """Test helper methods."""

    def test_col_letter_single(self):
        """Test single letter column conversion."""
        sheet = GSheet()
        assert sheet._col_letter(1) == 'A'
        assert sheet._col_letter(2) == 'B'
        assert sheet._col_letter(26) == 'Z'

    def test_col_letter_double(self):
        """Test double letter column conversion."""
        sheet = GSheet()
        assert sheet._col_letter(27) == 'AA'
        assert sheet._col_letter(28) == 'AB'
        assert sheet._col_letter(52) == 'AZ'
        assert sheet._col_letter(53) == 'BA'

    def test_infer_type_number(self):
        """Test type inference for numbers."""
        sheet = GSheet()
        assert sheet._infer_type(100) == 'number'
        assert sheet._infer_type(3.14) == 'number'

    def test_infer_type_text(self):
        """Test type inference for text."""
        sheet = GSheet()
        assert sheet._infer_type("hello") == 'text'
        assert sheet._infer_type(None) == 'text'

    def test_matches_criteria(self):
        """Test criteria matching."""
        sheet = GSheet()
        row = {'priority': 'P0', 'product': 'Widget', 'qty': 10}

        assert sheet._matches_criteria(row, {'priority': 'P0'}) is True
        assert sheet._matches_criteria(row, {'priority': 'P1'}) is False
        assert sheet._matches_criteria(row, {'priority': 'P0', 'qty': 10}) is True
        assert sheet._matches_criteria(row, None) is True
        assert sheet._matches_criteria(row, {}) is True

    def test_get_url(self):
        """Test URL generation."""
        sheet = GSheet(spreadsheet_id="abc123")
        assert sheet.get_url() == "https://docs.google.com/spreadsheets/d/abc123"

        sheet_no_id = GSheet()
        assert sheet_no_id.get_url() == ""

    def test_get_stats(self):
        """Test statistics."""
        sheet = GSheet()
        sheet.set_title("TEST")
        sheet.add_data_row({'a': 1})
        sheet.add_data_row({'a': 2})

        stats = sheet.get_stats()
        assert stats['sections'] == 2  # title + data
        assert stats['data_rows'] == 2


class TestGSheetAuth:
    """Test authentication helper."""

    def test_default_service_account_path(self):
        """Test default service account path."""
        assert GSheetAuth.DEFAULT_SERVICE_ACCOUNT == "/srv/xwander-platform/projects/alone/service_account.json"

    def test_scopes(self):
        """Test required OAuth scopes."""
        assert 'https://www.googleapis.com/auth/spreadsheets' in GSheetAuth.SCOPES
        assert 'https://www.googleapis.com/auth/drive' in GSheetAuth.SCOPES


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
