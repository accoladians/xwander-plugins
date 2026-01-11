"""
gsheet.py - Local-First Google Sheets Management

Version: 2.0.0 (Core)
AI-friendly section-based abstraction for Google Sheets.

Example:
    sheet = GSheet.create_new("My Order")
    sheet.set_title("PURCHASE ORDER")
    sheet.add_summary_row("Total", 1000, format='currency')
    sheet.set_header(['Priority', 'Product', 'Qty'])
    sheet.add_data_row({'priority': 'P0', 'product': 'Widget', 'qty': 10})
    sheet.sync()
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import gspread
from google.oauth2 import service_account


class GSheetAuth:
    """Authentication helper for Google Sheets."""

    DEFAULT_SERVICE_ACCOUNT = "/srv/xwander-platform/projects/alone/service_account.json"
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    @staticmethod
    def from_service_account(json_path: str) -> gspread.Client:
        """
        Create gspread client from service account JSON.

        Args:
            json_path: Path to service account JSON

        Returns:
            gspread.Client
        """
        creds = service_account.Credentials.from_service_account_file(
            json_path,
            scopes=GSheetAuth.SCOPES
        )
        return gspread.authorize(creds)

    @staticmethod
    def get_default_client() -> gspread.Client:
        """
        Get client using default service account.

        Returns:
            gspread.Client
        """
        return GSheetAuth.from_service_account(GSheetAuth.DEFAULT_SERVICE_ACCOUNT)


class GSheet:
    """
    Local-first Google Sheets manager with section-based updates.

    Maintains JSON state file locally, syncs to Google Sheets on demand.
    Abstracts away cell position calculation - sections handle layout.
    """

    DEFAULT_SHARED_DRIVE_ID = "0AOx6w8RvMATMUk9PVA"

    def __init__(self, spreadsheet_id: Optional[str] = None, worksheet_name: str = "Sheet1"):
        """
        Initialize GSheet instance.

        Args:
            spreadsheet_id: Google Sheets ID (optional, can create new)
            worksheet_name: Worksheet name (default: "Sheet1")
        """
        self._spreadsheet_id = spreadsheet_id
        self._worksheet_name = worksheet_name
        self._client = None
        self._spreadsheet = None
        self._worksheet = None

        # JSON state
        self._meta = {
            "version": "2.0.0",
            "spreadsheet_id": spreadsheet_id,
            "worksheet_name": worksheet_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_synced": None
        }
        self._sections = {}
        self._section_order = []
        self._section_boundaries = {}

    @classmethod
    def load(cls, json_path: str) -> 'GSheet':
        """
        Load existing GSheet from JSON state file.

        Args:
            json_path: Path to JSON state file

        Returns:
            GSheet instance
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        sheet = cls(
            spreadsheet_id=state['_meta']['spreadsheet_id'],
            worksheet_name=state['_meta']['worksheet_name']
        )
        sheet._meta = state['_meta']
        sheet._sections = state.get('sections', {})
        sheet._section_order = state.get('section_order', [])
        sheet._section_boundaries = state.get('section_boundaries', {})

        return sheet

    @classmethod
    def create_new(cls, title: str, shared_drive_id: Optional[str] = None) -> 'GSheet':
        """
        Create new Google Spreadsheet and initialize GSheet.

        Args:
            title: Spreadsheet title
            shared_drive_id: Optional Shared Drive ID (default: AI Automation drive)

        Returns:
            GSheet instance
        """
        client = GSheetAuth.get_default_client()
        drive_id = shared_drive_id or cls.DEFAULT_SHARED_DRIVE_ID

        spreadsheet = client.create(title, folder_id=drive_id)

        sheet = cls(spreadsheet_id=spreadsheet.id, worksheet_name="Sheet1")
        sheet._client = client
        sheet._spreadsheet = spreadsheet
        sheet._worksheet = spreadsheet.sheet1

        return sheet

    def set_title(self, text: str, format: Optional[Dict] = None) -> None:
        """
        Set title row (merged cell across columns).

        Args:
            text: Title text
            format: Optional formatting dict

        Example:
            sheet.set_title("PURCHASE ORDER", format={
                'backgroundColor': '#1e3a8a',
                'textFormat': {'bold': True, 'fontSize': 14}
            })
        """
        default_format = {
            'backgroundColor': '#1e3a8a',
            'textFormat': {
                'bold': True,
                'fontSize': 14,
                'foregroundColor': '#ffffff'
            },
            'horizontalAlignment': 'CENTER'
        }

        if 'title' not in self._sections:
            self._sections['title'] = {'type': 'title', 'rows': []}
            if 'title' not in self._section_order:
                self._section_order.insert(0, 'title')

        self._sections['title']['rows'] = [{
            'cells': [{
                'value': text,
                'colspan': 12,
                'format': format or default_format
            }]
        }]

    def add_summary_row(self, key: str, value: Any, format: Optional[str] = None) -> None:
        """
        Add key-value row to summary section.

        Args:
            key: Label (e.g., "Total Investment")
            value: Value (number, string)
            format: Optional format ('currency', 'percentage', 'number')

        Example:
            sheet.add_summary_row("Total Investment", 1791.22, format='currency')
            sheet.add_summary_row("Margin %", 42.5, format='percentage')
        """
        if 'summary' not in self._sections:
            self._sections['summary'] = {'type': 'key_value', 'rows': []}
            if 'summary' not in self._section_order:
                # Insert after title if it exists
                idx = self._section_order.index('title') + 1 if 'title' in self._section_order else 0
                self._section_order.insert(idx, 'summary')

        self._sections['summary']['rows'].append({
            'key': key,
            'value': value,
            'format': format
        })

    def set_header(self, columns: List[str], freeze: bool = True) -> None:
        """
        Set header row with column names.

        Args:
            columns: List of column names
            freeze: Whether to freeze this row (default: True)

        Example:
            sheet.set_header(['Priority', 'SKU', 'Product', 'Qty'])
        """
        default_format = {
            'backgroundColor': '#3b82f6',
            'textFormat': {
                'bold': True,
                'foregroundColor': '#ffffff'
            },
            'horizontalAlignment': 'CENTER'
        }

        if 'header' not in self._sections:
            self._sections['header'] = {'type': 'header', 'rows': []}
            # Insert before data if it exists, otherwise at end
            if 'data' in self._section_order:
                idx = self._section_order.index('data')
                self._section_order.insert(idx, 'header')
            elif 'header' not in self._section_order:
                self._section_order.append('header')

        self._sections['header']['rows'] = [{
            'cells': columns,
            'format': default_format,
            'freeze': freeze
        }]

    def add_data_row(self, data: Dict[str, Any]) -> None:
        """
        Add row to data table.

        Args:
            data: Dict mapping column names to values

        Example:
            sheet.add_data_row({
                'priority': 'P0',
                'product': 'Widget',
                'qty': 15,
                'cost': 8.30
            })
        """
        if 'data' not in self._sections:
            self._sections['data'] = {
                'type': 'table',
                'columns': [],
                'rows': []
            }
            if 'data' not in self._section_order:
                self._section_order.append('data')

        # Auto-detect columns from first row if not set
        if not self._sections['data']['columns']:
            self._sections['data']['columns'] = [
                {'name': key, 'type': self._infer_type(value)}
                for key, value in data.items()
            ]

        self._sections['data']['rows'].append(data)

    def update_data_row(self, match: Optional[Dict] = None, updates: Optional[Dict] = None) -> int:
        """
        Update rows matching criteria.

        Args:
            match: Dict to match row (e.g., {'product': 'Widget'})
            updates: Dict with updated values

        Returns:
            Number of rows updated

        Example:
            sheet.update_data_row(
                match={'product': 'Widget'},
                updates={'priority': 'P1', 'qty': 20}
            )
        """
        if 'data' not in self._sections or not updates:
            return 0

        count = 0
        for row in self._sections['data']['rows']:
            if self._matches_criteria(row, match):
                row.update(updates)
                count += 1

        return count

    def find_data_rows(self, criteria: Dict) -> List[Dict]:
        """
        Find rows matching criteria.

        Args:
            criteria: Dict to match (e.g., {'priority': 'P0'})

        Returns:
            List of matching rows

        Example:
            p0_rows = sheet.find_data_rows({'priority': 'P0'})
        """
        if 'data' not in self._sections:
            return []

        return [
            row for row in self._sections['data']['rows']
            if self._matches_criteria(row, criteria)
        ]

    def add_footer_line(self, text: str, format: Optional[Dict] = None) -> None:
        """
        Add line to footer section.

        Args:
            text: Footer text
            format: Optional formatting dict

        Example:
            sheet.add_footer_line("")  # Blank line
            sheet.add_footer_line("CRITICAL ACTIONS", format={'textFormat': {'bold': True}})
        """
        if 'footer' not in self._sections:
            self._sections['footer'] = {'type': 'text_block', 'rows': []}
            if 'footer' not in self._section_order:
                self._section_order.append('footer')

        self._sections['footer']['rows'].append({
            'text': text,
            'format': format
        })

    def sync(self, sections: str = 'auto') -> Dict:
        """
        Sync local state to Google Sheets.

        Args:
            sections: 'all' (full rebuild), 'auto' (all sections), or list of names

        Returns:
            Dict with sync stats

        Example:
            stats = sheet.sync()  # Sync all sections
        """
        if not self._spreadsheet_id:
            raise ValueError("Cannot sync: no spreadsheet_id. Use create_new() first.")

        # Initialize client if needed
        if not self._client:
            self._client = GSheetAuth.get_default_client()
            self._spreadsheet = self._client.open_by_key(self._spreadsheet_id)
            try:
                self._worksheet = self._spreadsheet.worksheet(self._worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                self._worksheet = self._spreadsheet.add_worksheet(
                    title=self._worksheet_name,
                    rows=500,
                    cols=20
                )

        # Build all rows
        all_rows = []
        self._section_boundaries = {}
        current_row = 1

        for section_name in self._section_order:
            section = self._sections.get(section_name)
            if not section:
                continue

            start_row = current_row
            section_rows = self._build_section_rows(section)
            all_rows.extend(section_rows)
            end_row = current_row + len(section_rows) - 1

            self._section_boundaries[section_name] = {
                'start_row': start_row,
                'end_row': end_row
            }

            current_row = end_row + 1

        # Clear and update
        self._worksheet.clear()
        if all_rows:
            self._worksheet.update(values=all_rows, range_name='A1', value_input_option='USER_ENTERED')

        # Apply formatting
        self._apply_formatting()

        # Update metadata
        self._meta['last_synced'] = datetime.now(timezone.utc).isoformat()

        return {
            'sections_synced': list(self._section_boundaries.keys()),
            'rows_updated': len(all_rows),
            'timestamp': self._meta['last_synced']
        }

    def save(self, json_path: str) -> None:
        """
        Save JSON state to file.

        Args:
            json_path: Path to save JSON
        """
        state = {
            '_meta': self._meta,
            'sections': self._sections,
            'section_order': self._section_order,
            'section_boundaries': self._section_boundaries
        }

        # Ensure directory exists
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def get_url(self) -> str:
        """Get Google Sheets URL."""
        if not self._spreadsheet_id:
            return ""
        return f"https://docs.google.com/spreadsheets/d/{self._spreadsheet_id}"

    def get_stats(self) -> Dict:
        """Get statistics about the sheet."""
        total_rows = sum(
            len(self._sections[s].get('rows', []))
            for s in self._section_order
            if s in self._sections
        )

        return {
            'sections': len(self._section_order),
            'total_rows': total_rows,
            'data_rows': len(self._sections.get('data', {}).get('rows', [])),
            'spreadsheet_id': self._spreadsheet_id,
            'worksheet_name': self._worksheet_name
        }

    # --- Private Methods ---

    def _build_section_rows(self, section: Dict) -> List[List[Any]]:
        """Build rows array for a section."""
        section_type = section.get('type')

        if section_type == 'title':
            return [[row['cells'][0]['value']] for row in section.get('rows', [])]

        elif section_type == 'key_value':
            rows = []
            for row in section.get('rows', []):
                value = self._format_value(row['value'], row.get('format'))
                rows.append([row['key'], value])
            return rows

        elif section_type == 'header':
            return [[cell for cell in row['cells']] for row in section.get('rows', [])]

        elif section_type == 'table':
            rows = []
            columns = section.get('columns', [])
            for row_data in section.get('rows', []):
                row = []
                for col in columns:
                    col_name = col['name']
                    value = row_data.get(col_name, '')
                    formatted = self._format_value(value, col.get('type'))
                    row.append(formatted)
                rows.append(row)
            return rows

        elif section_type == 'text_block':
            return [[row.get('text', '')] for row in section.get('rows', [])]

        return []

    def _format_value(self, value: Any, format_type: Optional[str]) -> Any:
        """Format value based on type."""
        if value is None or value == '':
            return ''

        if format_type == 'currency':
            try:
                return float(value)
            except (ValueError, TypeError):
                return value

        elif format_type == 'percentage':
            try:
                # Store as decimal for Google Sheets percentage format
                return float(value) / 100
            except (ValueError, TypeError):
                return value

        elif format_type == 'number':
            try:
                return float(value)
            except (ValueError, TypeError):
                return value

        return value

    def _infer_type(self, value: Any) -> str:
        """Infer column type from value."""
        if isinstance(value, (int, float)):
            return 'number'
        return 'text'

    def _matches_criteria(self, row: Dict, criteria: Optional[Dict]) -> bool:
        """Check if row matches criteria dict."""
        if not criteria:
            return True
        return all(row.get(k) == v for k, v in criteria.items())

    def _apply_formatting(self) -> None:
        """Apply formatting to sections."""
        for section_name, bounds in self._section_boundaries.items():
            section = self._sections.get(section_name)
            if not section:
                continue

            section_type = section.get('type')
            start_row = bounds['start_row']
            end_row = bounds['end_row']

            # Title formatting
            if section_type == 'title' and section.get('rows'):
                row_data = section['rows'][0]
                cell_format = row_data['cells'][0].get('format', {})
                if cell_format:
                    range_name = f'A{start_row}'
                    self._worksheet.format(range_name, cell_format)
                    # Merge cells if colspan specified
                    colspan = row_data['cells'][0].get('colspan', 1)
                    if colspan > 1:
                        self._worksheet.merge_cells(
                            start_row, 1, start_row, colspan
                        )

            # Header formatting
            elif section_type == 'header' and section.get('rows'):
                row_data = section['rows'][0]
                cell_format = row_data.get('format', {})
                if cell_format:
                    # Get number of columns
                    num_cols = len(row_data['cells'])
                    range_name = f'A{start_row}:{self._col_letter(num_cols)}{start_row}'
                    self._worksheet.format(range_name, cell_format)

                # Freeze header row
                if row_data.get('freeze', False):
                    self._worksheet.freeze(rows=start_row)

            # Data table formatting
            elif section_type == 'table':
                columns = section.get('columns', [])
                for col_idx, col in enumerate(columns):
                    col_type = col.get('type')
                    if col_type in ('currency', 'percentage', 'number'):
                        col_letter = self._col_letter(col_idx + 1)
                        range_name = f'{col_letter}{start_row}:{col_letter}{end_row}'

                        if col_type == 'currency':
                            self._worksheet.format(range_name, {
                                'numberFormat': {
                                    'type': 'CURRENCY',
                                    'pattern': '€#,##0.00'
                                }
                            })
                        elif col_type == 'percentage':
                            self._worksheet.format(range_name, {
                                'numberFormat': {
                                    'type': 'PERCENT',
                                    'pattern': '0.0%'
                                }
                            })

    def _col_letter(self, col_num: int) -> str:
        """Convert column number to letter (1=A, 2=B, ..., 27=AA)."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(col_num % 26 + ord('A')) + result
            col_num //= 26
        return result
