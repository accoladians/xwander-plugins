#!/usr/bin/env python3
"""
Example: Create a purchase order spreadsheet using gsheet.py v2.0

This example demonstrates the AI-first, section-based approach
that eliminates hardcoded cell ranges.
"""

import sys
# Add plugin to path for direct import
sys.path.insert(0, '/srv/plugins/xwander-gsheet')

from xwander_gsheet import GSheet

def main():
    # Create new spreadsheet in AI Automation shared drive
    sheet = GSheet.create_new("Example Purchase Order 2026-01-05")

    # Title section (merged, centered, dark blue background)
    sheet.set_title("KUPILKA PURCHASE ORDER - January 2026")

    # Summary section (key-value pairs)
    sheet.add_summary_row("Total Investment", 1791.22, format='currency')
    sheet.add_summary_row("Expected Revenue (12m)", 5169.25, format='currency')
    sheet.add_summary_row("Expected Margin", 1878.03, format='currency')
    sheet.add_summary_row("Margin %", 42.5, format='percentage')
    sheet.add_summary_row("Total Units", 200)
    sheet.add_summary_row("Total SKUs", 23)
    sheet.add_summary_row("Payback Period", "3.4 months")
    sheet.add_summary_row("ROI", "188%")

    # Header section (frozen, blue background)
    sheet.set_header([
        'Priority', 'Catalog SKU', 'Product', 'Color',
        'Qty', 'Cost/Unit', 'Total Cost', 'Retail Price',
        'Margin %', 'Note'
    ])

    # Data section (one row per variation)
    products = [
        {'priority': 'P0', 'catalog_sku': 'KP21-KEL', 'product': 'Kupilka 21',
         'color': 'Kelo', 'qty': 15, 'cost': 8.30, 'total': 124.50,
         'retail': 17.50, 'margin': 52.6, 'note': 'Best seller, restock critical'},
        {'priority': 'P0', 'catalog_sku': 'KP21-MUS', 'product': 'Kupilka 21',
         'color': 'Mustikka', 'qty': 10, 'cost': 8.30, 'total': 83.00,
         'retail': 17.50, 'margin': 52.6, 'note': 'Second best color'},
        {'priority': 'P1', 'catalog_sku': 'KP55-KEL', 'product': 'Kupilka 55',
         'color': 'Kelo', 'qty': 8, 'cost': 9.99, 'total': 79.92,
         'retail': 19.90, 'margin': 49.8, 'note': 'Larger bowl, steady sales'},
        {'priority': 'P2', 'catalog_sku': 'SUOV-RUS', 'product': 'SUOVA 20',
         'color': 'Ruskea', 'qty': 3, 'cost': 8.99, 'total': 26.97,
         'retail': 18.90, 'margin': 52.4, 'note': 'Test new product - all colors'},
    ]

    for p in products:
        sheet.add_data_row(p)

    # Footer section (notes, actions)
    sheet.add_footer_line("")
    sheet.add_footer_line("CRITICAL ACTIONS")
    sheet.add_footer_line("1. Price Optimization - Review before ordering")
    sheet.add_footer_line("2. SUOVA 20 - Test all 5 colors (2-3 units each)")
    sheet.add_footer_line("")
    sheet.add_footer_line("Competitor Sources: varuste.net, partioaitta.fi, scandinavianoutdoor.fi")

    # Sync to Google Sheets (single API call for all data)
    stats = sheet.sync()
    print(f"Synced {stats['rows_updated']} rows across {len(stats['sections_synced'])} sections")

    # Save JSON state for future updates
    sheet.save('/tmp/example_order_state.json')

    print(f"\nSpreadsheet URL: {sheet.get_url()}")
    print(f"State saved to: /tmp/example_order_state.json")

    # Demonstrate query/update
    p0_rows = sheet.find_data_rows({'priority': 'P0'})
    print(f"\nFound {len(p0_rows)} P0 products:")
    for row in p0_rows:
        print(f"  - {row['product']} ({row['color']}): {row['qty']} units")


if __name__ == '__main__':
    main()
