"""Keyword management for Search campaigns.

This module handles keyword-level operations for Search ad groups,
including creation, retrieval, listing with performance metrics, bulk
creation, and removal. Implements the Phase 2 spec for keyword support.

Key Features:
    - Add single keywords with match type and optional CPC/final URL
    - List keywords with metrics and quality scores
    - Fetch individual keyword details
    - Bulk keyword creation with partial failure handling
    - Remove keywords safely

API Version: v22 (google-ads-python 28.4.1)
"""

from typing import Dict, List, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import (
    CampaignNotFoundError,
    APIError,
    QuotaExceededError,
    ValidationError,
    AdsError,
)


class KeywordNotFoundError(AdsError):
    """Keyword not found."""

    exit_code = 4


_VALID_MATCH_TYPES = {"EXACT", "PHRASE", "BROAD"}


def _validate_match_type(match_type: str) -> str:
    """Normalize and validate match type."""
    if not match_type:
        raise ValidationError("match_type is required (EXACT, PHRASE, BROAD)")
    normalized = match_type.upper()
    if normalized not in _VALID_MATCH_TYPES:
        raise ValidationError(f"match_type must be one of: {_VALID_MATCH_TYPES}")
    return normalized


def _validate_ids(ad_group_id: Optional[str] = None, criterion_id: Optional[str] = None) -> None:
    """Validate numeric IDs."""
    if ad_group_id is not None and (not str(ad_group_id).isdigit()):
        raise ValidationError("Valid ad_group_id is required")
    if criterion_id is not None and (not str(criterion_id).isdigit()):
        raise ValidationError("Valid criterion_id is required")


def add_keyword(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: str,
    keyword_text: str,
    match_type: str,
    cpc_bid_eur: Optional[float] = None,
    final_url: Optional[str] = None,
) -> Dict:
    """Add a keyword to an ad group.

    Args:
        client: Authenticated GoogleAdsClient.
        customer_id: Customer ID (e.g., "2425288235").
        ad_group_id: Target ad group ID.
        keyword_text: Keyword text (e.g., "aurora tours").
        match_type: Keyword match type: EXACT, PHRASE, BROAD.
        cpc_bid_eur: Optional max CPC bid in EUR.
        final_url: Optional final URL to attach to the keyword.

    Returns:
        Dict with:
            - criterion_id
            - resource_name
            - text
            - match_type

    Raises:
        ValidationError: If parameters are invalid.
        CampaignNotFoundError: If ad group/campaign is missing.
        QuotaExceededError: If API quota exceeded.
        APIError: For other API errors.

    Example:
        >>> add_keyword(client, "2425288235", "12345678901", "husky safari", "PHRASE", 1.2)
        {'criterion_id': '9876543210', 'resource_name': 'customers/...', 'text': 'husky safari', 'match_type': 'PHRASE'}
    """
    if not keyword_text or not keyword_text.strip():
        raise ValidationError("keyword_text is required")
    _validate_ids(ad_group_id=ad_group_id)
    match_type_normalized = _validate_match_type(match_type)
    if cpc_bid_eur is not None and cpc_bid_eur <= 0:
        raise ValidationError("cpc_bid_eur must be positive when provided")

    try:
        ad_group_criterion_service = client.get_service("AdGroupCriterionService")
        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        criterion.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
        criterion.keyword.text = keyword_text
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type_normalized]

        if cpc_bid_eur is not None:
            criterion.cpc_bid_micros = int(cpc_bid_eur * 1_000_000)
        if final_url:
            criterion.final_urls.append(final_url)

        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=[operation],
        )

        resource_name = response.results[0].resource_name
        criterion_id = resource_name.split("/")[-1]

        return {
            "criterion_id": criterion_id,
            "resource_name": resource_name,
            "text": keyword_text,
            "match_type": match_type_normalized,
        }

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error:
            error_msg = error.message
            if "QUOTA_EXCEEDED" in str(error.error_code):
                raise QuotaExceededError("API quota exceeded - try again later")
            if "NOT_FOUND" in str(error.error_code) or "ad group" in error_msg.lower():
                raise CampaignNotFoundError(f"Ad group {ad_group_id} not found")
            raise APIError(f"Failed to add keyword: {error_msg}")
        raise APIError(f"Failed to add keyword: {str(ex)}")


def list_keywords(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    include_negative: bool = False,
    limit: int = 1000,
) -> List[Dict]:
    """List keywords with performance metrics.

    Args:
        client: Authenticated GoogleAdsClient.
        customer_id: Customer ID.
        ad_group_id: Optional ad group filter.
        campaign_id: Optional campaign filter.
        include_negative: Include negative keywords when True.
        limit: Max rows to return (default 1000, max 10000).

    Returns:
        List of dicts:
            - criterion_id
            - text
            - match_type
            - status
            - is_negative
            - cpc_bid_micros
            - quality_score
            - impressions
            - clicks
            - conversions

    Raises:
        ValidationError: For invalid filters.
        APIError: For API issues.

    Example:
        >>> list_keywords(client, "2425288235", ad_group_id="12345678901", limit=50)
        [{'criterion_id': '111', 'text': 'aurora tour', 'match_type': 'PHRASE', ...}]
    """
    if ad_group_id:
        _validate_ids(ad_group_id=ad_group_id)
    if campaign_id:
        if not str(campaign_id).isdigit():
            raise ValidationError("campaign_id must be numeric")
    limit = min(max(1, limit), 10000)

    try:
        ga_service = client.get_service("GoogleAdsService")
        filters = ["ad_group_criterion.status != 'REMOVED'"]
        if not include_negative:
            filters.append("ad_group_criterion.negative = false")
        if ad_group_id:
            filters.append(f"ad_group.id = {ad_group_id}")
        if campaign_id:
            filters.append(f"campaign.id = {campaign_id}")

        where_clause = " AND ".join(filters)

        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.status,
                ad_group_criterion.negative,
                ad_group_criterion.cpc_bid_micros,
                ad_group_criterion.final_urls,
                ad_group_criterion.quality_info.quality_score,
                ad_group.id,
                ad_group.name,
                campaign.id,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM ad_group_criterion
            WHERE ad_group_criterion.type = 'KEYWORD'
            AND {where_clause}
            ORDER BY metrics.impressions DESC
            LIMIT {limit}
        """

        response = ga_service.search(customer_id=customer_id, query=query)

        keywords = []
        for row in response:
            keywords.append({
                "criterion_id": row.ad_group_criterion.criterion_id,
                "text": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "status": row.ad_group_criterion.status.name,
                "is_negative": row.ad_group_criterion.negative,
                "cpc_bid_micros": row.ad_group_criterion.cpc_bid_micros,
                "quality_score": row.ad_group_criterion.quality_info.quality_score,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": row.metrics.conversions,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "campaign_id": row.campaign.id,
                "cost_micros": row.metrics.cost_micros,
                "final_urls": list(row.ad_group_criterion.final_urls),
            })

        return keywords

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error:
            if "QUOTA_EXCEEDED" in str(error.error_code):
                raise QuotaExceededError("API quota exceeded - try again later")
            raise APIError(f"Failed to list keywords: {error.message}")
        raise APIError(f"Failed to list keywords: {str(ex)}")


def get_keyword(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: str,
    criterion_id: str,
) -> Dict:
    """Get keyword details and performance.

    Args:
        client: Authenticated GoogleAdsClient.
        customer_id: Customer ID.
        ad_group_id: Parent ad group ID.
        criterion_id: Keyword criterion ID.

    Returns:
        Dict with keyword details:
            - criterion_id
            - text
            - match_type
            - status
            - is_negative
            - cpc_bid_micros
            - quality_score
            - impressions
            - clicks
            - conversions
            - cost_micros
            - ad_group_id
            - ad_group_name
            - campaign_id
            - final_urls

    Raises:
        KeywordNotFoundError: If keyword not found.
        ValidationError: For invalid IDs.
        APIError: For API issues.

    Example:
        >>> get_keyword(client, "2425288235", "12345678901", "9876543210")
        {'criterion_id': '9876543210', 'text': 'aurora tour', ...}
    """
    _validate_ids(ad_group_id=ad_group_id, criterion_id=criterion_id)

    try:
        ga_service = client.get_service("GoogleAdsService")
        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.status,
                ad_group_criterion.negative,
                ad_group_criterion.cpc_bid_micros,
                ad_group_criterion.final_urls,
                ad_group_criterion.quality_info.quality_score,
                ad_group.id,
                ad_group.name,
                campaign.id,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM ad_group_criterion
            WHERE ad_group_criterion.type = 'KEYWORD'
            AND ad_group_criterion.criterion_id = {criterion_id}
            AND ad_group.id = {ad_group_id}
            LIMIT 1
        """

        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            return {
                "criterion_id": row.ad_group_criterion.criterion_id,
                "text": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "status": row.ad_group_criterion.status.name,
                "is_negative": row.ad_group_criterion.negative,
                "cpc_bid_micros": row.ad_group_criterion.cpc_bid_micros,
                "quality_score": row.ad_group_criterion.quality_info.quality_score,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": row.metrics.conversions,
                "cost_micros": row.metrics.cost_micros,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "campaign_id": row.campaign.id,
                "final_urls": list(row.ad_group_criterion.final_urls),
            }

        raise KeywordNotFoundError(
            f"Keyword {criterion_id} not found in ad group {ad_group_id}"
        )

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error:
            if "NOT_FOUND" in str(error.error_code):
                raise KeywordNotFoundError(
                    f"Keyword {criterion_id} not found in ad group {ad_group_id}"
                )
            if "QUOTA_EXCEEDED" in str(error.error_code):
                raise QuotaExceededError("API quota exceeded - try again later")
            raise APIError(f"Failed to get keyword: {error.message}")
        raise APIError(f"Failed to get keyword: {str(ex)}")


def bulk_add_keywords(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: str,
    keywords: List[Dict],
) -> List[Dict]:
    """Add multiple keywords to an ad group in bulk.

    Args:
        client: Authenticated GoogleAdsClient.
        customer_id: Customer ID.
        ad_group_id: Target ad group ID.
        keywords: List of dicts with keys:
            - text (required)
            - match_type (required, EXACT/PHRASE/BROAD)
            - cpc_bid_eur (optional)

    Returns:
        List of dicts:
            - status: 'success' or 'error'
            - criterion_id: Created criterion ID (if success)
            - text: Keyword text

    Raises:
        ValidationError: For invalid input.
        APIError: For API errors.

    Example:
        >>> kw_list = [
        ...     {"text": "aurora tours", "match_type": "PHRASE", "cpc_bid_eur": 1.5},
        ...     {"text": "husky safari", "match_type": "EXACT"},
        ... ]
        >>> bulk_add_keywords(client, "2425288235", "12345678901", kw_list)
    """
    _validate_ids(ad_group_id=ad_group_id)
    if not keywords:
        raise ValidationError("keywords list cannot be empty")

    try:
        ad_group_criterion_service = client.get_service("AdGroupCriterionService")
        operations = []

        for kw in keywords:
            if "text" not in kw or not kw["text"]:
                raise ValidationError(f"Keyword text is required: {kw}")
            if "match_type" not in kw:
                raise ValidationError(f"match_type is required for keyword: {kw}")

            match_type_normalized = _validate_match_type(kw["match_type"])

            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
            criterion.keyword.text = kw["text"]
            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type_normalized]

            if kw.get("cpc_bid_eur"):
                if kw["cpc_bid_eur"] <= 0:
                    raise ValidationError("cpc_bid_eur must be positive when provided")
                criterion.cpc_bid_micros = int(kw["cpc_bid_eur"] * 1_000_000)

            operations.append(operation)

        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations,
            partial_failure=True,
        )

        results: List[Dict] = []
        partial_error_message = (
            response.partial_failure_error.message if response.partial_failure_error else None
        )

        for i, result in enumerate(response.results):
            if result.resource_name:
                criterion_id = result.resource_name.split("/")[-1]
                results.append({
                    "status": "success",
                    "criterion_id": criterion_id,
                    "text": keywords[i]["text"],
                })
            else:
                error_msg = partial_error_message or "Failed to add keyword"
                results.append({
                    "status": "error",
                    "criterion_id": None,
                    "text": keywords[i].get("text"),
                    "error": error_msg,
                })

        return results

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error:
            if "QUOTA_EXCEEDED" in str(error.error_code):
                raise QuotaExceededError("API quota exceeded - try again later")
            if "NOT_FOUND" in str(error.error_code):
                raise CampaignNotFoundError(f"Ad group {ad_group_id} not found")
            raise APIError(f"Failed to add keywords: {error.message}")
        raise APIError(f"Failed to add keywords: {str(ex)}")


def remove_keyword(
    client: GoogleAdsClient,
    customer_id: str,
    ad_group_id: str,
    criterion_id: str,
) -> Dict:
    """Remove a keyword from an ad group.

    Args:
        client: Authenticated GoogleAdsClient.
        customer_id: Customer ID.
        ad_group_id: Ad group ID.
        criterion_id: Criterion ID to remove.

    Returns:
        Dict with:
            - criterion_id
            - status: 'success' or 'error'
            - message: Status message

    Raises:
        ValidationError: For invalid IDs.
        KeywordNotFoundError: If keyword does not exist.
        APIError: For API issues.

    Example:
        >>> remove_keyword(client, "2425288235", "12345678901", "9876543210")
        {'criterion_id': '9876543210', 'status': 'success', 'message': 'Removed'}
    """
    _validate_ids(ad_group_id=ad_group_id, criterion_id=criterion_id)

    try:
        ad_group_criterion_service = client.get_service("AdGroupCriterionService")
        operation = client.get_type("AdGroupCriterionOperation")

        resource_name = ad_group_criterion_service.ad_group_criterion_path(
            customer_id, ad_group_id, criterion_id
        )
        operation.remove = resource_name

        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=[operation],
        )

        if response.results and response.results[0].resource_name:
            return {
                "criterion_id": criterion_id,
                "status": "success",
                "message": "Removed",
            }

        raise APIError("Failed to remove keyword: No result returned")

    except GoogleAdsException as ex:
        error = ex.failure.errors[0] if ex.failure.errors else None
        if error:
            if "NOT_FOUND" in str(error.error_code):
                raise KeywordNotFoundError(
                    f"Keyword {criterion_id} not found in ad group {ad_group_id}"
                )
            if "QUOTA_EXCEEDED" in str(error.error_code):
                raise QuotaExceededError("API quota exceeded - try again later")
            raise APIError(f"Failed to remove keyword: {error.message}")
        raise APIError(f"Failed to remove keyword: {str(ex)}")
