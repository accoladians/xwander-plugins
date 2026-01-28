"""Main Airtable client with integrated rate limiting, caching, and batch operations.

This is the primary interface for Airtable operations.

Usage:
    from xwander_airtable import AirtableClient

    # Initialize with token from environment
    client = AirtableClient()

    # Or with explicit token
    client = AirtableClient(token="pat...")

    # List records with formula
    from xwander_airtable.formula import Formula
    records = client.list_records(
        base_id="app123",
        table="Events",
        formula=Formula.equals("Status", "Active"),
        max_records=100,
    )

    # Batch create
    result = client.batch_create(
        "app123", "Events",
        [{"Name": "Event 1"}, {"Name": "Event 2"}],
        progress=True,
    )

    # Get cached schema
    schema = client.get_schema("app123")
"""

import os
import httpx
from typing import Dict, Any, List, Optional, Union, Callable
from urllib.parse import urljoin

from .formula import Formula
from .rate_limiter import RateLimiter
from .batch import BatchOperations, BatchResult, print_progress
from .exceptions import (
    AirtableError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    raise_for_status,
)


class SchemaCache:
    """Simple in-memory schema cache."""

    def __init__(self, ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self.ttl = ttl

    def get(self, base_id: str) -> Optional[Dict[str, Any]]:
        """Get cached schema if not expired."""
        import time
        if base_id in self._cache:
            if time.time() - self._timestamps[base_id] < self.ttl:
                return self._cache[base_id]
            # Expired
            del self._cache[base_id]
            del self._timestamps[base_id]
        return None

    def set(self, base_id: str, schema: Dict[str, Any]) -> None:
        """Cache schema for base."""
        import time
        self._cache[base_id] = schema
        self._timestamps[base_id] = time.time()

    def invalidate(self, base_id: Optional[str] = None) -> None:
        """Invalidate cache for base or all bases."""
        if base_id:
            self._cache.pop(base_id, None)
            self._timestamps.pop(base_id, None)
        else:
            self._cache.clear()
            self._timestamps.clear()


class AirtableClient:
    """Main Airtable client with all features integrated.

    Features:
    - Automatic rate limiting (5 req/sec per base)
    - Schema caching to reduce API calls
    - Batch operations for create/update/delete
    - Formula builder integration
    - Proper error handling with typed exceptions
    """

    BASE_URL = "https://api.airtable.com"

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        cache_ttl: int = 300,
    ):
        """Initialize the Airtable client.

        Args:
            token: Airtable personal access token. Defaults to AIRTABLE_TOKEN env var.
            base_url: API base URL (for testing)
            timeout: Request timeout in seconds
            cache_ttl: Schema cache TTL in seconds
        """
        self.token = token or os.environ.get("AIRTABLE_TOKEN")
        if not self.token:
            raise AuthenticationError(
                "No Airtable token provided. Set AIRTABLE_TOKEN environment variable "
                "or pass token parameter."
            )

        self.base_url = base_url
        self.timeout = timeout
        self._schema_cache = SchemaCache(ttl=cache_ttl)
        self._http_client = httpx.Client(
            base_url=base_url,
            headers=self._build_headers(),
            timeout=timeout,
        )

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get_limiter(self, base_id: str) -> RateLimiter:
        """Get rate limiter for base."""
        return RateLimiter.get_limiter(base_id)

    def request(
        self,
        method: str,
        path: str,
        base_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a rate-limited API request.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path (e.g., "/v0/app123/Events")
            base_id: Base ID for rate limiting (extracted from path if not provided)
            **kwargs: Additional arguments for httpx

        Returns:
            Response JSON

        Raises:
            AirtableError: On API errors
        """
        # Extract base_id from path if not provided
        if not base_id and path.startswith("/v0/"):
            parts = path.split("/")
            if len(parts) >= 3:
                base_id = parts[2]

        # Apply rate limiting
        if base_id:
            limiter = self._get_limiter(base_id)
            limiter.acquire()

        # Make request
        response = self._http_client.request(method, path, **kwargs)

        # Handle errors
        if response.status_code >= 400:
            try:
                error_data = response.json()
            except Exception:
                error_data = {"error": {"message": response.text}}
            raise_for_status(error_data, response.status_code)

        return response.json()

    # ============ Base/Table Operations ============

    def list_bases(self) -> List[Dict[str, Any]]:
        """List all accessible bases."""
        response = self.request("GET", "/v0/meta/bases")
        return response.get("bases", [])

    def get_schema(self, base_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get base schema (tables and fields).

        Args:
            base_id: Airtable base ID
            use_cache: Whether to use cached schema

        Returns:
            Schema dict with "tables" list
        """
        if use_cache:
            cached = self._schema_cache.get(base_id)
            if cached:
                return cached

        schema = self.request("GET", f"/v0/meta/bases/{base_id}/tables")
        self._schema_cache.set(base_id, schema)
        return schema

    def get_table_schema(
        self, base_id: str, table_name: str, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get schema for a specific table.

        Args:
            base_id: Airtable base ID
            table_name: Table name or ID
            use_cache: Whether to use cached schema

        Returns:
            Table schema dict or None if not found
        """
        schema = self.get_schema(base_id, use_cache)
        for table in schema.get("tables", []):
            if table["name"] == table_name or table["id"] == table_name:
                return table
        return None

    def invalidate_cache(self, base_id: Optional[str] = None) -> None:
        """Invalidate schema cache."""
        self._schema_cache.invalidate(base_id)

    # ============ Record Operations ============

    def list_records(
        self,
        base_id: str,
        table: str,
        formula: Optional[Union[Formula, str]] = None,
        fields: Optional[List[str]] = None,
        sort: Optional[List[Dict[str, str]]] = None,
        view: Optional[str] = None,
        max_records: Optional[int] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """List records from a table with automatic pagination.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            formula: Filter formula (Formula object or string)
            fields: List of field names to return
            sort: List of {"field": "Name", "direction": "asc"|"desc"}
            view: View name or ID
            max_records: Maximum records to return (None = all)
            page_size: Records per page (max 100)

        Returns:
            List of record dicts with "id" and "fields"
        """
        params: Dict[str, Any] = {"pageSize": min(page_size, 100)}

        if formula:
            params["filterByFormula"] = str(formula) if isinstance(formula, Formula) else formula

        if fields:
            params["fields[]"] = fields

        if sort:
            for i, s in enumerate(sort):
                params[f"sort[{i}][field]"] = s["field"]
                params[f"sort[{i}][direction]"] = s.get("direction", "asc")

        if view:
            params["view"] = view

        records = []
        offset = None

        while True:
            if offset:
                params["offset"] = offset

            response = self.request(
                "GET",
                f"/v0/{base_id}/{table}",
                params=params,
            )

            batch = response.get("records", [])
            records.extend(batch)

            # Check if we've reached max_records
            if max_records and len(records) >= max_records:
                records = records[:max_records]
                break

            # Check for more pages
            offset = response.get("offset")
            if not offset:
                break

        return records

    def get_record(self, base_id: str, table: str, record_id: str) -> Dict[str, Any]:
        """Get a single record by ID.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            record_id: Record ID

        Returns:
            Record dict with "id" and "fields"

        Raises:
            NotFoundError: If record not found
        """
        return self.request("GET", f"/v0/{base_id}/{table}/{record_id}")

    def create_record(
        self,
        base_id: str,
        table: str,
        fields: Dict[str, Any],
        typecast: bool = False,
    ) -> Dict[str, Any]:
        """Create a single record.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            fields: Field values
            typecast: Enable automatic type conversion

        Returns:
            Created record with ID
        """
        payload = {"fields": fields}
        if typecast:
            payload["typecast"] = True

        return self.request("POST", f"/v0/{base_id}/{table}", json=payload)

    def update_record(
        self,
        base_id: str,
        table: str,
        record_id: str,
        fields: Dict[str, Any],
        typecast: bool = False,
    ) -> Dict[str, Any]:
        """Update a single record (partial update).

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            record_id: Record ID
            fields: Fields to update
            typecast: Enable automatic type conversion

        Returns:
            Updated record
        """
        payload = {"fields": fields}
        if typecast:
            payload["typecast"] = True

        return self.request("PATCH", f"/v0/{base_id}/{table}/{record_id}", json=payload)

    def delete_record(self, base_id: str, table: str, record_id: str) -> bool:
        """Delete a single record.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            record_id: Record ID

        Returns:
            True if deleted
        """
        response = self.request("DELETE", f"/v0/{base_id}/{table}/{record_id}")
        return response.get("deleted", False)

    # ============ Batch Operations ============

    def batch_create(
        self,
        base_id: str,
        table: str,
        records: List[Dict[str, Any]],
        typecast: bool = False,
        progress: Union[bool, Callable[[int, int], None]] = False,
    ) -> BatchResult:
        """Batch create records with automatic chunking.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            records: List of field dicts
            typecast: Enable automatic type conversion
            progress: True for default progress, or callback(current, total)

        Returns:
            BatchResult with created record IDs
        """
        progress_fn = None
        if progress is True:
            progress_fn = print_progress
        elif callable(progress):
            progress_fn = progress

        ops = BatchOperations(self.request)
        return ops.create_records(base_id, table, records, typecast, progress_fn)

    def batch_update(
        self,
        base_id: str,
        table: str,
        updates: List[Dict[str, Any]],
        typecast: bool = False,
        progress: Union[bool, Callable[[int, int], None]] = False,
    ) -> BatchResult:
        """Batch update records.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            updates: List of {"id": "recXXX", "fields": {...}}
            typecast: Enable automatic type conversion
            progress: True for default progress, or callback

        Returns:
            BatchResult with updated record IDs
        """
        progress_fn = None
        if progress is True:
            progress_fn = print_progress
        elif callable(progress):
            progress_fn = progress

        ops = BatchOperations(self.request)
        return ops.update_records(base_id, table, updates, typecast, progress_fn)

    def batch_delete(
        self,
        base_id: str,
        table: str,
        record_ids: List[str],
        progress: Union[bool, Callable[[int, int], None]] = False,
    ) -> BatchResult:
        """Batch delete records.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            record_ids: List of record IDs
            progress: True for default progress, or callback

        Returns:
            BatchResult with deleted record IDs
        """
        progress_fn = None
        if progress is True:
            progress_fn = print_progress
        elif callable(progress):
            progress_fn = progress

        ops = BatchOperations(self.request)
        return ops.delete_records(base_id, table, record_ids, progress_fn)

    def batch_upsert(
        self,
        base_id: str,
        table: str,
        records: List[Dict[str, Any]],
        merge_on: List[str],
        typecast: bool = False,
        progress: Union[bool, Callable[[int, int], None]] = False,
    ) -> BatchResult:
        """Batch upsert (update or insert) records.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            records: List of field dicts
            merge_on: Fields to use as unique key for matching
            typecast: Enable automatic type conversion
            progress: True for default progress, or callback

        Returns:
            BatchResult with created/updated record IDs
        """
        progress_fn = None
        if progress is True:
            progress_fn = print_progress
        elif callable(progress):
            progress_fn = progress

        ops = BatchOperations(self.request)
        return ops.upsert_records(base_id, table, records, merge_on, typecast, progress_fn)

    # ============ Context Manager ============

    def __enter__(self) -> "AirtableClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()
