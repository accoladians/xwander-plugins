#!/usr/bin/env python3
"""Verify xwander-ads plugin installation.

This script verifies that the plugin is correctly installed and all modules are importable.
"""

import sys

def test_imports():
    """Test all module imports."""
    print("Testing imports...")

    try:
        # Base package
        import xwander_ads
        print(f"  ✓ xwander_ads v{xwander_ads.__version__}")

        # Auth
        from xwander_ads import get_client, test_auth
        print("  ✓ auth module")

        # Exceptions
        from xwander_ads import (
            AdsError,
            AuthenticationError,
            AssetGroupNotFoundError,
            CampaignNotFoundError,
            DuplicateSignalError,
            QuotaExceededError
        )
        print("  ✓ exceptions module")

        # PMax
        from xwander_ads import pmax
        print("  ✓ pmax module")

        # PMax functions
        from xwander_ads.pmax import (
            list_campaigns,
            get_campaign,
            list_asset_groups,
            get_campaign_stats,
            list_signals,
            add_search_theme,
            bulk_add_themes,
            remove_signal,
            get_signal_stats
        )
        print("  ✓ pmax.campaigns functions")
        print("  ✓ pmax.signals functions")

        return True

    except ImportError as e:
        print(f"\n  ✗ Import failed: {e}")
        return False


def test_cli_utils():
    """Test CLI utility functions."""
    print("\nTesting CLI utilities...")

    try:
        from xwander_ads.cli import normalize_customer_id, format_micros

        # Test normalize_customer_id
        assert normalize_customer_id("242-528-8235") == "2425288235"
        assert normalize_customer_id("2425288235") == "2425288235"
        print("  ✓ normalize_customer_id()")

        # Test format_micros
        assert format_micros(1_000_000) == "EUR 1.00"
        assert format_micros(1_234_560_000) == "EUR 1,234.56"
        assert format_micros(1_000_000, "USD") == "USD 1.00"
        print("  ✓ format_micros()")

        return True

    except Exception as e:
        print(f"\n  ✗ CLI utils test failed: {e}")
        return False


def test_exception_hierarchy():
    """Test exception hierarchy and exit codes."""
    print("\nTesting exception hierarchy...")

    try:
        from xwander_ads.exceptions import (
            AdsError,
            AssetGroupNotFoundError,
            DuplicateSignalError,
            QuotaExceededError
        )

        # Test base error
        assert AdsError("test").exit_code == 1
        print("  ✓ AdsError (exit_code=1)")

        # Test specific errors
        assert AssetGroupNotFoundError("test").exit_code == 4
        print("  ✓ AssetGroupNotFoundError (exit_code=4)")

        assert DuplicateSignalError("test").exit_code == 5
        print("  ✓ DuplicateSignalError (exit_code=5)")

        assert QuotaExceededError("test").exit_code == 2
        print("  ✓ QuotaExceededError (exit_code=2)")

        return True

    except Exception as e:
        print(f"\n  ✗ Exception test failed: {e}")
        return False


def verify_files():
    """Verify required files exist."""
    print("\nVerifying file structure...")

    from pathlib import Path

    base_dir = Path(__file__).parent

    required_files = [
        "xwander_ads/__init__.py",
        "xwander_ads/auth.py",
        "xwander_ads/exceptions.py",
        "xwander_ads/cli.py",
        "xwander_ads/pmax/__init__.py",
        "xwander_ads/pmax/campaigns.py",
        "xwander_ads/pmax/signals.py",
        "docs/QUICK_REFERENCE.json",
        "docs/PMAX_GUIDE.md",
        "tests/test_pmax.py",
        "setup.py",
        "README.md",
        ".claude-plugin/plugin.json"
    ]

    all_exist = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ MISSING: {file_path}")
            all_exist = False

    return all_exist


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("  xwander-ads Plugin Installation Verification")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("CLI Utilities", test_cli_utils()))
    results.append(("Exception Hierarchy", test_exception_hierarchy()))
    results.append(("File Structure", verify_files()))

    # Summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")

    all_passed = all(result[1] for result in results)

    print()
    if all_passed:
        print("  ✓ All tests passed! Plugin is ready to use.")
        print()
        print("  Next steps:")
        print("    1. Install: pip install -e .")
        print("    2. Test auth: xw ads auth test")
        print("    3. List campaigns: xw ads pmax list --customer-id 2425288235 --campaigns")
        return 0
    else:
        print("  ✗ Some tests failed. Check output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
