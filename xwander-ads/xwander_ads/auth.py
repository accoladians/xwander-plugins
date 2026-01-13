"""Google Ads authentication - OAuth2 flow.

This module provides authentication support for Google Ads API.
It imports from xwander-google-auth plugin for shared credential management.
"""

import logging
import os
from pathlib import Path
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from .exceptions import AuthenticationError

# Config location - use existing platform location if available
CONFIG_PATHS = [
    Path.home() / '.google-ads.yaml',  # Standard location
    Path("/srv/xwander-platform/.env/google-apis/google-ads.yaml"),
    Path("/srv/xwander-platform/tools/business-tools/google-ads.yaml"),
    Path.home() / '.google-ads' / 'config.yaml'
]


def find_config():
    """Find existing config file."""
    for path in CONFIG_PATHS:
        if path.exists():
            return path
    return Path.home() / '.google-ads' / 'config.yaml'  # Default location


def get_client(config_path=None, version="v20"):
    """Get authenticated Google Ads client.

    Args:
        config_path: Optional path to google-ads.yaml config file
        version: API version to use (v20, v21, v22). Default: v20

    Returns:
        GoogleAdsClient instance

    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        if not config_path:
            config_path = find_config()

        if not Path(config_path).exists():
            raise AuthenticationError(
                f"Config file not found at {config_path}. "
                "Run: xw ads auth setup"
            )

        return GoogleAdsClient.load_from_storage(
            str(config_path), version=version
        )

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and hasattr(error.error_code, 'authentication_error'):
            raise AuthenticationError(
                "Authentication failed - check your refresh token"
            )
        elif error and hasattr(error.error_code, 'authorization_error'):
            raise AuthenticationError(
                "Authorization failed - check developer token access"
            )
        else:
            raise AuthenticationError(f"API error: {error.message if error else str(ex)}")

    except Exception as e:
        logging.error(f"Failed to create client: {e}")
        raise AuthenticationError(f"Failed to create Google Ads client: {e}")


def test_auth(config_path=None, version="v20"):
    """Test if authentication works.

    Args:
        config_path: Optional path to config file
        version: API version to test

    Returns:
        bool: True if auth works, False otherwise
    """
    try:
        client = get_client(config_path, version)

        # Simple test - get accessible customers
        customer_service = client.get_service("CustomerService")
        customers = customer_service.list_accessible_customers()
        customer_count = len(customers.resource_names)

        print(f"✓ Auth works! Found {customer_count} accounts")

        # Show first few customer IDs
        if customer_count > 0:
            print("\nAccessible accounts:")
            for resource_name in customers.resource_names[:5]:
                customer_id = resource_name.split('/')[-1]
                print(f"  - {customer_id}")
            if customer_count > 5:
                print(f"  ... and {customer_count - 5} more")

        return True

    except AuthenticationError as e:
        print(f"✗ {e}")
        return False
    except Exception as e:
        print(f"✗ Auth test failed: {e}")
        return False
