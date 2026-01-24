"""Responsive Search Ad (RSA) management.

This module handles CRUD operations for Responsive Search Ads with
headline/description validation and pinning support.

Key Features:
    - Create RSAs with 3-15 headlines and 2-4 descriptions
    - Support for headline pinning (HEADLINE_1, HEADLINE_2, HEADLINE_3)
    - Description pinning (DESCRIPTION_1, DESCRIPTION_2)
    - Bulk RSA creation from lists
    - URL path customization

API Version: v22 (google-ads-python 28.4.1)
"""

from typing import List, Dict, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import (
    ValidationError,
    APIError,
    QuotaExceededError,
)


# RSA validation constraints
RSA_VALIDATION = {
    "headline": {
        "min_count": 3,
        "max_count": 15,
        "min_length": 1,
        "max_length": 30,
    },
    "description": {
        "min_count": 2,
        "max_count": 4,
        "min_length": 1,
        "max_length": 90,
    },
    "path": {
        "max_length": 15,
    },
    "final_url": {
        "min_count": 1,
        "max_count": 10,
    },
}

# Valid pinning positions
HEADLINE_PINS = {"HEADLINE_1", "HEADLINE_2", "HEADLINE_3", None}
DESCRIPTION_PINS = {"DESCRIPTION_1", "DESCRIPTION_2", None}


def validate_rsa_config(
    headlines: List[Dict],
    descriptions: List[Dict],
    final_urls: List[str],
    path1: Optional[str] = None,
    path2: Optional[str] = None,
) -> List[str]:
    """Validate RSA configuration.

    Validates all RSA components against Google Ads requirements.

    Args:
        headlines: List of headline dicts with 'text' and optional 'pinned_to'
        descriptions: List of description dicts with 'text' and optional 'pinned_to'
        final_urls: List of landing page URLs
        path1: Display URL path 1 (optional)
        path2: Display URL path 2 (optional)

    Returns:
        List of validation error messages. Empty list if valid.

    Example:
        >>> errors = validate_rsa_config(
        ...     headlines=[{"text": "Too long headline exceeding thirty characters limit"}],
        ...     descriptions=[{"text": "OK description"}],
        ...     final_urls=["https://xwander.com"]
        ... )
        >>> print(errors)
        ['Headline count 1 is below minimum 3', 'Headline 1 exceeds 30 chars: 50']
    """
    errors = []
    h_rules = RSA_VALIDATION["headline"]
    d_rules = RSA_VALIDATION["description"]
    p_rules = RSA_VALIDATION["path"]
    u_rules = RSA_VALIDATION["final_url"]

    # Headline count validation
    if len(headlines) < h_rules["min_count"]:
        errors.append(f"Headline count {len(headlines)} is below minimum {h_rules['min_count']}")
    if len(headlines) > h_rules["max_count"]:
        errors.append(f"Headline count {len(headlines)} exceeds maximum {h_rules['max_count']}")

    # Headline text validation
    for i, h in enumerate(headlines, 1):
        text = h.get("text", "")
        if len(text) < h_rules["min_length"]:
            errors.append(f"Headline {i} is empty")
        if len(text) > h_rules["max_length"]:
            errors.append(f"Headline {i} exceeds {h_rules['max_length']} chars: {len(text)}")
        pin = h.get("pinned_to")
        if pin and pin not in HEADLINE_PINS:
            errors.append(f"Headline {i} has invalid pin position: {pin}")

    # Description count validation
    if len(descriptions) < d_rules["min_count"]:
        errors.append(f"Description count {len(descriptions)} is below minimum {d_rules['min_count']}")
    if len(descriptions) > d_rules["max_count"]:
        errors.append(f"Description count {len(descriptions)} exceeds maximum {d_rules['max_count']}")

    # Description text validation
    for i, d in enumerate(descriptions, 1):
        text = d.get("text", "")
        if len(text) < d_rules["min_length"]:
            errors.append(f"Description {i} is empty")
        if len(text) > d_rules["max_length"]:
            errors.append(f"Description {i} exceeds {d_rules['max_length']} chars: {len(text)}")
        pin = d.get("pinned_to")
        if pin and pin not in DESCRIPTION_PINS:
            errors.append(f"Description {i} has invalid pin position: {pin}")

    # URL validation
    if len(final_urls) < u_rules["min_count"]:
        errors.append("At least one final URL is required")
    if len(final_urls) > u_rules["max_count"]:
        errors.append(f"Final URL count {len(final_urls)} exceeds maximum {u_rules['max_count']}")

    for i, url in enumerate(final_urls, 1):
        if not url.startswith(("http://", "https://")):
            errors.append(f"Final URL {i} must start with http:// or https://")

    # Path validation
    if path1 and len(path1) > p_rules["max_length"]:
        errors.append(f"Path1 exceeds {p_rules['max_length']} chars: {len(path1)}")
    if path2 and len(path2) > p_rules["max_length"]:
        errors.append(f"Path2 exceeds {p_rules['max_length']} chars: {len(path2)}")

    return errors


def create_rsa(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: str,
    headlines: List[Dict],
    descriptions: List[Dict],
    final_urls: List[str],
    path1: Optional[str] = None,
    path2: Optional[str] = None,
    status: str = "PAUSED",
) -> Dict:
    """Create a Responsive Search Ad.

    RSAs dynamically combine headlines and descriptions to create
    the best-performing ad for each search query.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens, e.g., "2425288235")
        ad_group_id: Parent ad group ID (e.g., "12345678901")
        headlines: List of headline dicts (3-15 required):
            - text: Headline text (max 30 chars)
            - pinned_to: Optional position (HEADLINE_1, HEADLINE_2, HEADLINE_3)
        descriptions: List of description dicts (2-4 required):
            - text: Description text (max 90 chars)
            - pinned_to: Optional position (DESCRIPTION_1, DESCRIPTION_2)
        final_urls: Landing page URLs (at least 1)
        path1: Display URL path 1 (max 15 chars)
        path2: Display URL path 2 (max 15 chars)
        status: PAUSED (default) or ENABLED

    Returns:
        Dict with:
            - ad_id: Created ad ID
            - resource_name: Full resource name
            - ad_group_id: Parent ad group ID
            - headline_count: Number of headlines
            - description_count: Number of descriptions
            - url: Link to Google Ads UI

    Raises:
        ValidationError: Invalid headlines/descriptions
        APIError: API failures
        QuotaExceededError: If API quota exceeded

    Example:
        >>> headlines = [
        ...     {"text": "Northern Lights Tours", "pinned_to": "HEADLINE_1"},
        ...     {"text": "Book Now - Best Prices"},
        ...     {"text": "Expert Arctic Guides"},
        ...     {"text": "Small Group Adventures"},
        ...     {"text": "Guaranteed Aurora Viewing"},
        ... ]
        >>> descriptions = [
        ...     {"text": "Experience the magical Northern Lights in Finnish Lapland. Professional guides."},
        ...     {"text": "Join our award-winning tours from Ivalo. Book online with instant confirmation."},
        ... ]
        >>> result = create_rsa(
        ...     client, "2425288235", "12345678901",
        ...     headlines=headlines,
        ...     descriptions=descriptions,
        ...     final_urls=["https://xwander.com/northern-lights"],
        ...     path1="tours",
        ...     path2="aurora"
        ... )
        >>> print(f"Created RSA: {result['ad_id']}")
    """
    # Validate configuration
    errors = validate_rsa_config(headlines, descriptions, final_urls, path1, path2)
    if errors:
        raise ValidationError(f"RSA validation failed: {'; '.join(errors)}")

    try:
        ad_group_ad_service = client.get_service("AdGroupAdService")

        # Create operation
        operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.create

        # Set ad group
        ad_group_ad.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"

        # Set status
        if status.upper() == "ENABLED":
            ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED
        else:
            ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

        # Set final URLs
        for url in final_urls:
            ad_group_ad.ad.final_urls.append(url)

        # Configure RSA
        rsa = ad_group_ad.ad.responsive_search_ad

        # Add headlines with optional pinning
        for h in headlines:
            headline_asset = client.get_type("AdTextAsset")
            headline_asset.text = h["text"]

            # Set pinning if specified
            pin = h.get("pinned_to")
            if pin:
                pin_enum = client.enums.ServedAssetFieldTypeEnum
                if pin == "HEADLINE_1":
                    headline_asset.pinned_field = pin_enum.HEADLINE_1
                elif pin == "HEADLINE_2":
                    headline_asset.pinned_field = pin_enum.HEADLINE_2
                elif pin == "HEADLINE_3":
                    headline_asset.pinned_field = pin_enum.HEADLINE_3

            rsa.headlines.append(headline_asset)

        # Add descriptions with optional pinning
        for d in descriptions:
            desc_asset = client.get_type("AdTextAsset")
            desc_asset.text = d["text"]

            # Set pinning if specified
            pin = d.get("pinned_to")
            if pin:
                pin_enum = client.enums.ServedAssetFieldTypeEnum
                if pin == "DESCRIPTION_1":
                    desc_asset.pinned_field = pin_enum.DESCRIPTION_1
                elif pin == "DESCRIPTION_2":
                    desc_asset.pinned_field = pin_enum.DESCRIPTION_2

            rsa.descriptions.append(desc_asset)

        # Set display paths
        if path1:
            rsa.path1 = path1
        if path2:
            rsa.path2 = path2

        # Execute mutation
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[operation],
        )

        # Extract result
        result = response.results[0]
        resource_name = result.resource_name
        # Resource name format: customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}
        parts = resource_name.split("/")[-1].split("~")
        ad_id = parts[1] if len(parts) > 1 else parts[0]

        return {
            "ad_id": ad_id,
            "resource_name": resource_name,
            "ad_group_id": ad_group_id,
            "headline_count": len(headlines),
            "description_count": len(descriptions),
            "status": status.upper(),
            "url": f"https://ads.google.com/aw/ads?adId={ad_id}&__e={customer_id}",
        }

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "QUOTA_EXCEEDED" in str(error.error_code):
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to create RSA: {error.message if error else str(ex)}")


def list_rsas(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """List Responsive Search Ads.

    Retrieves RSAs with headlines, descriptions, and performance metrics.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        ad_group_id: Filter by ad group ID (optional)
        campaign_id: Filter by campaign ID (optional)
        limit: Maximum ads to return (default: 100, max: 10000)

    Returns:
        List of dicts with:
            - ad_id: Ad ID
            - ad_group_id: Parent ad group ID
            - ad_group_name: Ad group name
            - campaign_id: Campaign ID
            - status: ENABLED/PAUSED/REMOVED
            - headlines: List of headline texts
            - descriptions: List of description texts
            - final_urls: Landing page URLs
            - path1: Display path 1
            - path2: Display path 2
            - ad_strength: POOR/AVERAGE/GOOD/EXCELLENT
            - impressions: Total impressions
            - clicks: Total clicks

    Raises:
        APIError: For API errors

    Example:
        >>> rsas = list_rsas(client, "2425288235", campaign_id="12345678901")
        >>> for rsa in rsas:
        ...     print(f"{rsa['ad_id']}: {len(rsa['headlines'])} headlines, {rsa['ad_strength']}")
    """
    limit = min(max(1, limit), 10000)

    try:
        ga_service = client.get_service("GoogleAdsService")

        # Build filter clauses
        filters = ["ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'"]
        filters.append("ad_group_ad.status != 'REMOVED'")

        if ad_group_id:
            filters.append(f"ad_group.id = {ad_group_id}")
        if campaign_id:
            filters.append(f"campaign.id = {campaign_id}")

        where_clause = " AND ".join(filters)

        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.status,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls,
                ad_group_ad.ad.responsive_search_ad.path1,
                ad_group_ad.ad.responsive_search_ad.path2,
                ad_group_ad.ad_strength,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions
            FROM ad_group_ad
            WHERE {where_clause}
            ORDER BY ad_group.name
            LIMIT {limit}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        rsas = []
        for row in response:
            ad = row.ad_group_ad.ad
            rsa_info = ad.responsive_search_ad

            # Extract headline texts
            headlines = [h.text for h in rsa_info.headlines]

            # Extract description texts
            descriptions = [d.text for d in rsa_info.descriptions]

            # Extract final URLs
            final_urls = list(ad.final_urls)

            rsas.append({
                "ad_id": str(ad.id),
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "status": row.ad_group_ad.status.name,
                "headlines": headlines,
                "descriptions": descriptions,
                "final_urls": final_urls,
                "path1": rsa_info.path1 or "",
                "path2": rsa_info.path2 or "",
                "ad_strength": row.ad_group_ad.ad_strength.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": row.metrics.conversions,
            })

        return rsas

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "QUOTA_EXCEEDED" in str(error.error_code):
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to list RSAs: {error.message if error else str(ex)}")


def get_rsa(
    client: GoogleAdsClient,
    customer_id: str,
    ad_id: str,
) -> Dict:
    """Get RSA details including all headlines and descriptions.

    Retrieves comprehensive RSA information with pinning details.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        ad_id: Ad ID

    Returns:
        Dict with RSA details:
            - ad_id: Ad ID
            - ad_group_id: Parent ad group ID
            - status: Ad status
            - headlines: List of dicts with 'text' and 'pinned_to'
            - descriptions: List of dicts with 'text' and 'pinned_to'
            - final_urls: Landing page URLs
            - path1: Display path 1
            - path2: Display path 2
            - ad_strength: Ad strength rating
            - resource_name: Full resource name

    Raises:
        ValidationError: If ad not found
        APIError: For API errors

    Example:
        >>> rsa = get_rsa(client, "2425288235", "67890123456")
        >>> print(f"Headlines: {len(rsa['headlines'])}, Strength: {rsa['ad_strength']}")
    """
    try:
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.status,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls,
                ad_group_ad.ad.responsive_search_ad.path1,
                ad_group_ad.ad.responsive_search_ad.path2,
                ad_group_ad.ad_strength,
                ad_group_ad.resource_name,
                ad_group.id,
                ad_group.name,
                campaign.id,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions
            FROM ad_group_ad
            WHERE ad_group_ad.ad.id = {ad_id}
            AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        for row in response:
            ad = row.ad_group_ad.ad
            rsa_info = ad.responsive_search_ad

            # Extract headlines with pinning info
            headlines = []
            for h in rsa_info.headlines:
                headline_dict = {"text": h.text}
                if h.pinned_field:
                    headline_dict["pinned_to"] = h.pinned_field.name
                headlines.append(headline_dict)

            # Extract descriptions with pinning info
            descriptions = []
            for d in rsa_info.descriptions:
                desc_dict = {"text": d.text}
                if d.pinned_field:
                    desc_dict["pinned_to"] = d.pinned_field.name
                descriptions.append(desc_dict)

            return {
                "ad_id": str(ad.id),
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "campaign_id": str(row.campaign.id),
                "status": row.ad_group_ad.status.name,
                "headlines": headlines,
                "descriptions": descriptions,
                "final_urls": list(ad.final_urls),
                "path1": rsa_info.path1 or "",
                "path2": rsa_info.path2 or "",
                "ad_strength": row.ad_group_ad.ad_strength.name,
                "resource_name": row.ad_group_ad.resource_name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": row.metrics.conversions,
            }

        raise ValidationError(f"RSA with ad_id {ad_id} not found")

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error and "QUOTA_EXCEEDED" in str(error.error_code):
            raise QuotaExceededError("API quota exceeded - try again later")
        else:
            raise APIError(f"Failed to get RSA: {error.message if error else str(ex)}")


def bulk_create_rsas(
    client: GoogleAdsClient,
    customer_id: str,
    rsas_list: List[Dict],
) -> List[Dict]:
    """Create multiple RSAs in batch.

    Creates RSAs with partial failure support - some may succeed while
    others fail validation.

    Args:
        client: Authenticated GoogleAdsClient
        customer_id: Customer ID (without hyphens)
        rsas_list: List of RSA configs, each with:
            - ad_group_id: Parent ad group ID (required)
            - headlines: List of headline dicts (required)
            - descriptions: List of description dicts (required)
            - final_urls: List of landing page URLs (required)
            - path1: Display URL path 1 (optional)
            - path2: Display URL path 2 (optional)
            - status: PAUSED or ENABLED (optional, default PAUSED)

    Returns:
        List of result dicts, each with:
            - index: Position in input list
            - status: 'success' or 'error'
            - ad_id: Created ad ID (if success)
            - resource_name: Full resource name (if success)
            - error: Error message (if error)

    Raises:
        APIError: For batch-level API failures

    Example:
        >>> rsas = [
        ...     {
        ...         "ad_group_id": "12345",
        ...         "headlines": [{"text": "H1"}, {"text": "H2"}, {"text": "H3"}],
        ...         "descriptions": [{"text": "D1"}, {"text": "D2"}],
        ...         "final_urls": ["https://xwander.com/tours"],
        ...     },
        ...     {
        ...         "ad_group_id": "67890",
        ...         "headlines": [{"text": "H1"}, {"text": "H2"}, {"text": "H3"}],
        ...         "descriptions": [{"text": "D1"}, {"text": "D2"}],
        ...         "final_urls": ["https://xwander.com/packages"],
        ...     },
        ... ]
        >>> results = bulk_create_rsas(client, "2425288235", rsas)
        >>> for r in results:
        ...     print(f"Index {r['index']}: {r['status']}")
    """
    if not rsas_list:
        return []

    results = []

    # Pre-validate all RSAs
    operations = []
    valid_indices = []

    for i, rsa_config in enumerate(rsas_list):
        # Validate required fields
        if "ad_group_id" not in rsa_config:
            results.append({
                "index": i,
                "status": "error",
                "error": "Missing required field: ad_group_id",
            })
            continue

        headlines = rsa_config.get("headlines", [])
        descriptions = rsa_config.get("descriptions", [])
        final_urls = rsa_config.get("final_urls", [])
        path1 = rsa_config.get("path1")
        path2 = rsa_config.get("path2")

        # Validate RSA config
        errors = validate_rsa_config(headlines, descriptions, final_urls, path1, path2)
        if errors:
            results.append({
                "index": i,
                "status": "error",
                "error": "; ".join(errors),
            })
            continue

        # Build operation
        try:
            operation = client.get_type("AdGroupAdOperation")
            ad_group_ad = operation.create

            ad_group_id = rsa_config["ad_group_id"]
            ad_group_ad.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"

            status = rsa_config.get("status", "PAUSED")
            if status.upper() == "ENABLED":
                ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED
            else:
                ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

            for url in final_urls:
                ad_group_ad.ad.final_urls.append(url)

            rsa = ad_group_ad.ad.responsive_search_ad

            for h in headlines:
                headline_asset = client.get_type("AdTextAsset")
                headline_asset.text = h["text"]
                pin = h.get("pinned_to")
                if pin:
                    pin_enum = client.enums.ServedAssetFieldTypeEnum
                    if pin == "HEADLINE_1":
                        headline_asset.pinned_field = pin_enum.HEADLINE_1
                    elif pin == "HEADLINE_2":
                        headline_asset.pinned_field = pin_enum.HEADLINE_2
                    elif pin == "HEADLINE_3":
                        headline_asset.pinned_field = pin_enum.HEADLINE_3
                rsa.headlines.append(headline_asset)

            for d in descriptions:
                desc_asset = client.get_type("AdTextAsset")
                desc_asset.text = d["text"]
                pin = d.get("pinned_to")
                if pin:
                    pin_enum = client.enums.ServedAssetFieldTypeEnum
                    if pin == "DESCRIPTION_1":
                        desc_asset.pinned_field = pin_enum.DESCRIPTION_1
                    elif pin == "DESCRIPTION_2":
                        desc_asset.pinned_field = pin_enum.DESCRIPTION_2
                rsa.descriptions.append(desc_asset)

            if path1:
                rsa.path1 = path1
            if path2:
                rsa.path2 = path2

            operations.append(operation)
            valid_indices.append(i)

        except Exception as e:
            results.append({
                "index": i,
                "status": "error",
                "error": str(e),
            })

    # Execute batch if we have valid operations
    if operations:
        try:
            ad_group_ad_service = client.get_service("AdGroupAdService")

            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=operations,
                partial_failure=True,
            )

            # Process results
            for j, result in enumerate(response.results):
                original_index = valid_indices[j]
                if result.resource_name:
                    parts = result.resource_name.split("/")[-1].split("~")
                    ad_id = parts[1] if len(parts) > 1 else parts[0]
                    results.append({
                        "index": original_index,
                        "status": "success",
                        "ad_id": ad_id,
                        "resource_name": result.resource_name,
                        "ad_group_id": rsas_list[original_index]["ad_group_id"],
                    })
                else:
                    results.append({
                        "index": original_index,
                        "status": "error",
                        "error": "Failed to create RSA",
                    })

            # Check for partial failure errors
            if response.partial_failure_error:
                # Parse partial failure errors
                for error in response.partial_failure_error.details:
                    # Find which operation failed
                    pass  # Simplified - detailed error parsing can be added later

        except GoogleAdsException as ex:
            error = ex.failure.errors[0] if ex.failure.errors else None
            if error and "QUOTA_EXCEEDED" in str(error.error_code):
                raise QuotaExceededError("API quota exceeded - try again later")
            else:
                raise APIError(f"Batch RSA creation failed: {error.message if error else str(ex)}")

    # Sort results by original index
    results.sort(key=lambda x: x["index"])

    return results
