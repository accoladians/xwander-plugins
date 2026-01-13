"""Report generation and execution for Google Ads.

Provides functions to execute GAQL queries and format results
as tables, CSV, JSON, etc.
"""

from typing import List, Dict, Any, Optional
from enum import EnumMeta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import AdsError


def _is_default_value(value) -> bool:
    """Check if a protobuf field value is a default/empty value.

    Handles enums, primitives, and message types safely without
    instantiating enum types (which would cause EnumMeta errors).

    Args:
        value: The field value to check

    Returns:
        True if the value is a default/empty value
    """
    # Handle None
    if value is None:
        return True

    # Handle primitive types FIRST (before enum check to avoid int() on strings)
    if isinstance(value, bool):
        return value is False
    if isinstance(value, str):
        return value == ""
    if isinstance(value, bytes):
        return value == b""
    if isinstance(value, (int, float)) and not isinstance(type(value), EnumMeta):
        return value == 0

    # Handle repeated fields (lists)
    if isinstance(value, (list, tuple)):
        return len(value) == 0

    # Handle enum types (proto-plus enums have EnumMeta, protobuf has EnumTypeWrapper)
    # Check this AFTER primitives to avoid false positives
    value_type = type(value)
    if isinstance(value_type, EnumMeta):
        # Enum default is typically 0 (UNSPECIFIED or UNKNOWN)
        return int(value) == 0
    if isinstance(value_type, type) and value_type.__name__ == 'EnumTypeWrapper':
        return int(value) == 0

    # Handle protobuf messages - check if it has fields and all are default
    if hasattr(value, '_pb'):
        try:
            # For proto-plus wrapped messages, check underlying protobuf
            pb = value._pb
            return not pb.ByteSize()
        except Exception:
            pass

    # For raw protobuf messages
    if hasattr(value, 'ByteSize'):
        try:
            return not value.ByteSize()
        except Exception:
            pass

    # Safe fallback: try comparison, but catch enum errors
    try:
        return value == type(value)()
    except TypeError:
        # If we can't instantiate the type, assume non-default
        return False


def execute_query(
    client: GoogleAdsClient,
    customer_id: str,
    query: str
) -> List[Dict[str, Any]]:
    """Execute a GAQL query and return results as list of dicts.

    Args:
        client: Google Ads client
        customer_id: Customer ID (without hyphens)
        query: GAQL query string

    Returns:
        List of result dictionaries

    Raises:
        AdsError: If query execution fails
    """
    customer_id = customer_id.replace('-', '')

    try:
        service = client.get_service("GoogleAdsService")
        response = service.search(customer_id=customer_id, query=query)

        results = []
        for row in response:
            # Convert protobuf row to dict
            row_dict = _row_to_dict(row)
            results.append(row_dict)

        return results

    except GoogleAdsException as ex:
        errors = []
        for error in ex.failure.errors:
            errors.append(f"{error.error_code.name}: {error.message}")
        raise AdsError(
            f"Query execution failed:\n" + "\n".join(errors),
            exit_code=1
        )


def execute_query_stream(
    client: GoogleAdsClient,
    customer_id: str,
    query: str
):
    """Execute a GAQL query and yield results as they arrive.

    Args:
        client: Google Ads client
        customer_id: Customer ID (without hyphens)
        query: GAQL query string

    Yields:
        Result dictionaries

    Raises:
        AdsError: If query execution fails
    """
    customer_id = customer_id.replace('-', '')

    try:
        service = client.get_service("GoogleAdsService")
        response = service.search_stream(customer_id=customer_id, query=query)

        for batch in response:
            for row in batch.results:
                yield _row_to_dict(row)

    except GoogleAdsException as ex:
        errors = []
        for error in ex.failure.errors:
            errors.append(f"{error.error_code.name}: {error.message}")
        raise AdsError(
            f"Query execution failed:\n" + "\n".join(errors),
            exit_code=1
        )


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert protobuf row to dictionary.

    Args:
        row: GoogleAdsRow protobuf object

    Returns:
        Dictionary with flattened field values
    """
    result = {}

    # Iterate through all fields in the row
    for field in row._pb.DESCRIPTOR.fields:
        field_name = field.name
        if not hasattr(row, field_name):
            continue

        field_obj = getattr(row, field_name)

        # Skip empty/default values using enum-safe check
        if _is_default_value(field_obj):
            continue

        # Flatten nested objects
        _flatten_object(field_obj, field_name, result)

    return result


def _flatten_object(obj, prefix: str, result: Dict[str, Any]):
    """Recursively flatten protobuf object into dictionary.

    Args:
        obj: Protobuf object
        prefix: Field prefix for nested objects
        result: Dictionary to populate
    """
    # Handle None
    if obj is None:
        return

    # Handle repeated fields (lists/containers) - must check BEFORE _pb check
    # RepeatedScalarContainer and RepeatedCompositeContainer don't have DESCRIPTOR
    type_name = type(obj).__name__
    if 'Repeated' in type_name or isinstance(obj, (list, tuple)):
        if len(obj) > 0:
            # Convert repeated field to list of values
            values = []
            for item in obj:
                if hasattr(item, 'name'):  # enum
                    values.append(item.name if hasattr(item, 'name') else str(item))
                elif hasattr(item, '_pb'):  # nested message
                    nested = {}
                    _flatten_object(item, 'item', nested)
                    values.append(nested.get('item', str(item)))
                else:
                    values.append(item)
            result[prefix] = values
        return

    # Handle enum types FIRST (before primitives, since IntEnum passes isinstance int check)
    obj_type = type(obj)
    if isinstance(obj_type, EnumMeta) or (isinstance(obj_type, type) and obj_type.__name__ == 'EnumTypeWrapper'):
        # Skip UNSPECIFIED/UNKNOWN enums (value 0)
        if int(obj) != 0:
            result[prefix] = obj.name if hasattr(obj, 'name') else str(obj)
        return

    # Handle primitive types (after enum check)
    if isinstance(obj, (str, int, float, bool, bytes)):
        result[prefix] = obj
        return

    # Handle messages (nested objects) - check for _pb attribute
    if hasattr(obj, '_pb'):
        pb = obj._pb
        if hasattr(pb, 'DESCRIPTOR'):
            for field in pb.DESCRIPTOR.fields:
                field_name = field.name
                if not hasattr(obj, field_name):
                    continue

                value = getattr(obj, field_name)

                # Skip default/empty values using enum-safe check
                if _is_default_value(value):
                    continue

                full_name = f"{prefix}.{field_name}"
                _flatten_object(value, full_name, result)
        return

    # Handle enums with name attribute (fallback)
    if hasattr(obj, 'name') and hasattr(obj, 'value'):
        result[prefix] = obj.name
        return

    # Handle other types - convert to string as fallback
    result[prefix] = str(obj) if obj else obj


def format_micros(micros: int, currency: str = "EUR") -> str:
    """Format micros as currency.

    Args:
        micros: Value in micros (1/1,000,000)
        currency: Currency code (default: EUR)

    Returns:
        Formatted currency string
    """
    return f"{currency} {micros / 1_000_000:,.2f}"


def format_percentage(value: float) -> str:
    """Format decimal as percentage.

    Args:
        value: Decimal value (e.g., 0.0523 for 5.23%)

    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.2f}%"


class TableFormatter:
    """Format query results as ASCII table."""

    @staticmethod
    def format(
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        currency: str = "EUR"
    ) -> str:
        """Format results as ASCII table.

        Args:
            data: Query results
            columns: Column names to display (default: all)
            currency: Currency code for micros formatting

        Returns:
            Formatted table string
        """
        if not data:
            return "No results found."

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        # Calculate column widths
        widths = {}
        for col in columns:
            widths[col] = max(
                len(str(col)),
                max(len(str(row.get(col, ''))) for row in data)
            )

        # Build header
        header_parts = [str(col).ljust(widths[col]) for col in columns]
        header = " | ".join(header_parts)
        separator = "-+-".join(["-" * widths[col] for col in columns])

        # Build rows
        lines = [header, separator]
        for row in data:
            row_parts = [str(row.get(col, '')).ljust(widths[col]) for col in columns]
            lines.append(" | ".join(row_parts))

        lines.append(separator)
        lines.append(f"\nTotal rows: {len(data)}")

        return "\n".join(lines)

    @staticmethod
    def format_performance(data: List[Dict[str, Any]], currency: str = "EUR") -> str:
        """Format campaign performance data with proper formatting.

        Args:
            data: Query results
            currency: Currency code

        Returns:
            Formatted table string
        """
        if not data:
            return "No campaigns found."

        # Prepare formatted rows
        rows = []
        for row in data:
            formatted = {
                'campaign.name': row.get('campaign.name', '')[:40],
                'campaign.status': row.get('campaign.status', ''),
                'metrics.impressions': f"{row.get('metrics.impressions', 0):,}",
                'metrics.clicks': f"{row.get('metrics.clicks', 0):,}",
                'metrics.ctr': format_percentage(row.get('metrics.ctr', 0)),
                'metrics.cost': format_micros(row.get('metrics.cost_micros', 0), currency),
                'metrics.conversions': f"{row.get('metrics.conversions', 0):.1f}",
            }

            # Add cost per conversion if available
            cost_per_conv = row.get('metrics.cost_per_conversion', 0)
            if cost_per_conv > 0:
                formatted['metrics.cost_per_conversion'] = format_micros(
                    int(cost_per_conv),
                    currency
                )
            else:
                formatted['metrics.cost_per_conversion'] = '-'

            rows.append(formatted)

        # Build table
        header = (
            f"{'Campaign':<40} {'Status':<10} {'Impr':>10} {'Clicks':>8} "
            f"{'CTR':>8} {'Cost':>12} {'Conv':>8} {'CPA':>12}"
        )
        separator = "=" * len(header)

        lines = [separator, header, separator]

        for row in rows:
            line = (
                f"{row['campaign.name']:<40} {row['campaign.status']:<10} "
                f"{row['metrics.impressions']:>10} {row['metrics.clicks']:>8} "
                f"{row['metrics.ctr']:>8} {row['metrics.cost']:>12} "
                f"{row['metrics.conversions']:>8} {row['metrics.cost_per_conversion']:>12}"
            )
            lines.append(line)

        lines.append(separator)

        # Add summary
        total_impressions = sum(d.get('metrics.impressions', 0) for d in data)
        total_clicks = sum(d.get('metrics.clicks', 0) for d in data)
        total_cost = sum(d.get('metrics.cost_micros', 0) for d in data)
        total_conversions = sum(d.get('metrics.conversions', 0) for d in data)

        lines.append(f"\nTotal Campaigns: {len(data)}")
        lines.append(f"Total Impressions: {total_impressions:,}")
        lines.append(f"Total Clicks: {total_clicks:,}")
        lines.append(f"Total Cost: {format_micros(total_cost, currency)}")
        lines.append(f"Total Conversions: {total_conversions:.1f}")

        return "\n".join(lines)
