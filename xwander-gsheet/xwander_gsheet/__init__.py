"""
xwander-gsheet - AI-first Google Sheets management

Section-based abstraction for Google Sheets with local-first JSON state.

Example:
    from xwander_gsheet import GSheet, GSheetAuth

    sheet = GSheet.create_new("My Order")
    sheet.set_title("PURCHASE ORDER")
    sheet.add_summary_row("Total", 1000, format='currency')
    sheet.sync()
"""

from .gsheet import GSheet, GSheetAuth

__version__ = "2.0.0"
__all__ = ["GSheet", "GSheetAuth"]
