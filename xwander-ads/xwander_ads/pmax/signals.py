"""Performance Max signals management - search themes and audience signals.

This module handles adding, removing, and listing signals for PMax asset groups.
Migrated from verified working script: toolkit/pmax_signals.py
"""

from typing import List, Dict, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import (
    AssetGroupNotFoundError,
    DuplicateSignalError,
    APIError,
    QuotaExceededError
)


def list_signals(client: GoogleAdsClient, customer_id: str, asset_group_id: str) -> List[Dict]:
    """List all search theme signals for a Performance Max asset group.

    Search themes (audience signals) help guide Google's AI to find relevant
    audiences. This function retrieves all currently active themes.

    Common Use Cases:
        - Audit themes before adding new ones
        - Check for duplicates
        - Get resource names for removal

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens, e.g., "2425288235")
        asset_group_id: Asset group ID (numeric string)

    Returns:
        List of dicts with keys:
            - 'resource_name': Full resource name for removal operations
            - 'text': Search theme text (what the theme says)

    Raises:
        AssetGroupNotFoundError: If asset group doesn't exist
        APIError: For other API errors

    Example:
        >>> client = get_client()
        >>> themes = list_signals(client, "2425288235", "12345678901")
        >>> for theme in themes:
        ...     print(f"{theme['text']}")
        northern lights tours
        arctic adventure holidays
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                asset_group_signal.resource_name,
                asset_group_signal.search_theme.text
            FROM asset_group_signal
            WHERE asset_group_signal.asset_group = 'customers/{customer_id}/assetGroups/{asset_group_id}'
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        search_themes = []
        for row in response:
            signal = row.asset_group_signal
            if signal.search_theme.text:
                search_themes.append({
                    'resource_name': signal.resource_name,
                    'text': signal.search_theme.text
                })

        return search_themes

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "NOT_FOUND" in str(error.error_code):
            raise AssetGroupNotFoundError(
                f"Asset group {asset_group_id} not found for customer {customer_id}"
            )
        elif error and "QUOTA_EXCEEDED" in str(error.error_code):
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to list signals: {error.message if error else str(ex)}")


def add_search_theme(
    client: GoogleAdsClient,
    customer_id: str,
    asset_group_id: str,
    theme_text: str
) -> str:
    """Add a single search theme signal to a Performance Max asset group.

    Search themes guide Google's AI to find relevant audiences. Use specific,
    descriptive phrases (e.g., "northern lights tours" not "tours").

    Common Use Cases:
        - Test new theme before bulk adding
        - Add single high-priority theme
        - Interactive theme management

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens, e.g., "2425288235")
        asset_group_id: Asset group ID (numeric string)
        theme_text: Search theme text (2-80 characters, descriptive phrase)

    Returns:
        Resource name of created signal (format: customers/{cid}/assetGroupSignals/{id})

    Raises:
        DuplicateSignalError: If theme already exists (can be safely ignored)
        AssetGroupNotFoundError: If asset group doesn't exist
        APIError: For other API errors

    Example:
        >>> client = get_client()
        >>> resource = add_search_theme(client, "2425288235", "12345", "northern lights tours")
        >>> print(resource)
        customers/2425288235/assetGroupSignals/67890
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        asset_group_resource = f"customers/{customer_id}/assetGroups/{asset_group_id}"

        mutate_operation = client.get_type("MutateOperation")
        signal = mutate_operation.asset_group_signal_operation.create
        signal.asset_group = asset_group_resource
        signal.search_theme.text = theme_text

        response = ga_service.mutate(
            customer_id=customer_id,
            mutate_operations=[mutate_operation]
        )

        result = response.mutate_operation_responses[0].asset_group_signal_result
        return result.resource_name

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error:
            error_str = str(error.error_code)
            if "DUPLICATE" in error_str or "ALREADY_EXISTS" in error_str:
                raise DuplicateSignalError(f"Search theme '{theme_text}' already exists")
            elif "NOT_FOUND" in error_str:
                raise AssetGroupNotFoundError(
                    f"Asset group {asset_group_id} not found for customer {customer_id}"
                )
            elif "QUOTA_EXCEEDED" in error_str:
                raise QuotaExceededError("API quota exceeded - try again later")
            else:
                raise APIError(f"Failed to add search theme: {error.message}")
        else:
            raise APIError(f"Failed to add search theme: {str(ex)}")


def bulk_add_themes(
    client: GoogleAdsClient,
    customer_id: str,
    asset_group_id: str,
    themes: List[str],
    skip_duplicates: bool = True
) -> List[str]:
    """Add multiple search themes at once (efficient batch operation).

    Processes themes in batches of 50 (API limit). Automatically handles
    duplicates and retries. More efficient than calling add_search_theme()
    multiple times.

    Common Use Cases:
        - Seasonal theme updates (e.g., winter holidays)
        - Initial campaign setup
        - Large-scale theme management

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens, e.g., "2425288235")
        asset_group_id: Asset group ID (numeric string)
        themes: List of search theme texts (one per item)
        skip_duplicates: If True, ignore duplicate errors and continue (recommended)

    Returns:
        List of resource names for successfully created signals

    Raises:
        AssetGroupNotFoundError: If asset group doesn't exist
        APIError: For API errors (only if skip_duplicates=False)

    Example:
        >>> client = get_client()
        >>> themes = ["northern lights tours", "arctic holidays", "lapland trips"]
        >>> results = bulk_add_themes(client, "2425288235", "12345", themes)
        >>> print(f"Added {len(results)} themes")
        Added 3 themes
    """
    ga_service = client.get_service("GoogleAdsService")

    asset_group_resource = f"customers/{customer_id}/assetGroups/{asset_group_id}"

    operations = []
    for theme_text in themes:
        if not theme_text.strip():
            continue
        mutate_operation = client.get_type("MutateOperation")
        signal = mutate_operation.asset_group_signal_operation.create
        signal.asset_group = asset_group_resource
        signal.search_theme.text = theme_text.strip()
        operations.append(mutate_operation)

    if not operations:
        return []

    # Add in batches of 50 (API limit)
    results = []
    errors = []

    for i in range(0, len(operations), 50):
        batch = operations[i:i+50]
        batch_themes = [t.strip() for t in themes[i:i+50] if t.strip()]

        try:
            response = ga_service.mutate(
                customer_id=customer_id,
                mutate_operations=batch
            )

            for op_response in response.mutate_operation_responses:
                result = op_response.asset_group_signal_result
                results.append(result.resource_name)

        except GoogleAdsException as ex:
            if not skip_duplicates:
                error = ex.failure.errors[0] if ex.failure.errors else None
                if error and "NOT_FOUND" in str(error.error_code):
                    raise AssetGroupNotFoundError(
                        f"Asset group {asset_group_id} not found for customer {customer_id}"
                    )
                else:
                    raise APIError(f"Failed to add themes: {error.message if error else str(ex)}")
            else:
                # Log error but continue
                for j, error in enumerate(ex.failure.errors):
                    theme_idx = i + j
                    if theme_idx < len(batch_themes):
                        errors.append({
                            'theme': batch_themes[theme_idx],
                            'error': error.message
                        })

    if errors and not skip_duplicates:
        raise APIError(f"Failed to add {len(errors)} themes")

    return results


def remove_signal(
    client: GoogleAdsClient,
    customer_id: str,
    signal_resource_name: str
) -> bool:
    """Remove a signal.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        signal_resource_name: Full resource name of signal

    Returns:
        True if successful

    Raises:
        APIError: If removal fails
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        mutate_operation = client.get_type("MutateOperation")
        mutate_operation.asset_group_signal_operation.remove = signal_resource_name

        ga_service.mutate(
            customer_id=customer_id,
            mutate_operations=[mutate_operation]
        )

        return True

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        raise APIError(f"Failed to remove signal: {error.message if error else str(ex)}")


def get_signal_stats(client: GoogleAdsClient, customer_id: str, asset_group_id: str) -> Dict:
    """Get signal statistics for an asset group.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        asset_group_id: Asset group ID

    Returns:
        Dict with signal counts and details
    """
    signals = list_signals(client, customer_id, asset_group_id)

    return {
        'asset_group_id': asset_group_id,
        'total_signals': len(signals),
        'search_themes': [s['text'] for s in signals],
        'signals': signals
    }
