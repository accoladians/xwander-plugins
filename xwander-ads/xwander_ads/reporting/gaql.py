"""GAQL (Google Ads Query Language) query builder.

Provides a fluent API for building GAQL queries with validation.

Example:
    >>> query = GAQLBuilder() \\
    ...     .select('campaign.name', 'metrics.clicks', 'metrics.cost_micros') \\
    ...     .from_resource('campaign') \\
    ...     .where('campaign.status = ENABLED') \\
    ...     .during('LAST_30_DAYS') \\
    ...     .order_by('metrics.cost_micros', desc=True) \\
    ...     .limit(50) \\
    ...     .build()
"""

from typing import List, Optional, Union


class GAQLBuilder:
    """Fluent builder for GAQL queries."""

    def __init__(self):
        self._select_fields: List[str] = []
        self._from_resource: Optional[str] = None
        self._where_conditions: List[str] = []
        self._order_by_fields: List[tuple] = []  # (field, is_desc)
        self._limit: Optional[int] = None
        self._parameters: dict = {}

    def select(self, *fields: str) -> 'GAQLBuilder':
        """Add fields to SELECT clause.

        Args:
            *fields: Field names (e.g., 'campaign.name', 'metrics.clicks')

        Returns:
            Self for chaining
        """
        self._select_fields.extend(fields)
        return self

    def from_resource(self, resource: str) -> 'GAQLBuilder':
        """Set FROM resource.

        Args:
            resource: Resource name (e.g., 'campaign', 'ad_group', 'keyword_view')

        Returns:
            Self for chaining
        """
        self._from_resource = resource
        return self

    def where(self, condition: str) -> 'GAQLBuilder':
        """Add WHERE condition.

        Args:
            condition: Condition string (e.g., 'campaign.status = ENABLED')

        Returns:
            Self for chaining
        """
        self._where_conditions.append(condition)
        return self

    def during(self, date_range: str) -> 'GAQLBuilder':
        """Add date range condition (shortcut for segments.date).

        Args:
            date_range: Date range string (e.g., 'LAST_7_DAYS', 'LAST_30_DAYS')

        Returns:
            Self for chaining
        """
        self._where_conditions.append(f"segments.date DURING {date_range}")
        return self

    def date_between(self, start_date: str, end_date: str) -> 'GAQLBuilder':
        """Add date range between two dates.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Self for chaining
        """
        self._where_conditions.append(
            f"segments.date BETWEEN '{start_date}' AND '{end_date}'"
        )
        return self

    def order_by(self, field: str, desc: bool = False) -> 'GAQLBuilder':
        """Add ORDER BY clause.

        Args:
            field: Field to order by
            desc: True for descending order (default: False)

        Returns:
            Self for chaining
        """
        self._order_by_fields.append((field, desc))
        return self

    def limit(self, limit: int) -> 'GAQLBuilder':
        """Set LIMIT clause.

        Args:
            limit: Maximum number of rows to return

        Returns:
            Self for chaining
        """
        self._limit = limit
        return self

    def parameters(self, **params) -> 'GAQLBuilder':
        """Set query parameters (not part of GAQL, for Python usage).

        Args:
            **params: Key-value parameters

        Returns:
            Self for chaining
        """
        self._parameters.update(params)
        return self

    def build(self) -> str:
        """Build the GAQL query string.

        Returns:
            Complete GAQL query

        Raises:
            ValueError: If required clauses are missing
        """
        if not self._select_fields:
            raise ValueError("SELECT clause is required")
        if not self._from_resource:
            raise ValueError("FROM clause is required")

        # Build query parts
        parts = []

        # SELECT
        select_clause = "SELECT " + ", ".join(self._select_fields)
        parts.append(select_clause)

        # FROM
        from_clause = f"FROM {self._from_resource}"
        parts.append(from_clause)

        # WHERE
        if self._where_conditions:
            where_clause = "WHERE " + " AND ".join(self._where_conditions)
            parts.append(where_clause)

        # ORDER BY
        if self._order_by_fields:
            order_parts = []
            for field, is_desc in self._order_by_fields:
                order_parts.append(f"{field} {'DESC' if is_desc else 'ASC'}")
            order_clause = "ORDER BY " + ", ".join(order_parts)
            parts.append(order_clause)

        # LIMIT
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")

        return " ".join(parts)

    def __str__(self) -> str:
        """String representation."""
        return self.build()


def validate_query(query: str) -> bool:
    """Validate a GAQL query string.

    Args:
        query: GAQL query string

    Returns:
        True if query appears valid

    Raises:
        ValueError: If query is invalid
    """
    query = query.strip().upper()

    if not query.startswith('SELECT'):
        raise ValueError("Query must start with SELECT")

    if 'FROM' not in query:
        raise ValueError("Query must contain FROM clause")

    # Check for common issues
    if query.count('SELECT') > 1:
        raise ValueError("Multiple SELECT clauses not allowed")

    if query.count('FROM') > 1:
        raise ValueError("Multiple FROM clauses not allowed")

    return True


def format_query(query: str, indent: str = "  ") -> str:
    """Format a GAQL query for readability.

    Args:
        query: GAQL query string
        indent: Indentation string (default: 2 spaces)

    Returns:
        Formatted query with proper indentation
    """
    # Remove extra whitespace
    query = " ".join(query.split())

    # Add line breaks after major clauses
    query = query.replace(" SELECT ", "\nSELECT\n" + indent)
    query = query.replace(" FROM ", "\nFROM ")
    query = query.replace(" WHERE ", "\nWHERE\n" + indent)
    query = query.replace(" ORDER BY ", "\nORDER BY ")
    query = query.replace(" LIMIT ", "\nLIMIT ")

    # Add line breaks after commas in SELECT
    lines = query.split('\n')
    formatted = []
    for line in lines:
        if line.strip().startswith('SELECT'):
            formatted.append(line)
        elif any(line.strip().startswith(kw) for kw in ['FROM', 'WHERE', 'ORDER BY', 'LIMIT']):
            formatted.append(line)
        elif ',' in line:
            # Split comma-separated fields
            parts = [p.strip() for p in line.split(',')]
            formatted.extend([indent + p + ',' if i < len(parts) - 1 else indent + p
                            for i, p in enumerate(parts)])
        else:
            formatted.append(line)

    return '\n'.join(formatted).strip()
