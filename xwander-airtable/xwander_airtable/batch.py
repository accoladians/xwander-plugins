"""Batch operations for Airtable with automatic chunking.

Airtable limits:
- 10 records per create/update request
- 10 record IDs per delete request

This module handles automatic batching with progress reporting.

Usage:
    from xwander_airtable.batch import BatchOperations

    ops = BatchOperations(client)

    # Batch create with progress
    results = ops.create_records("Events", records, progress=True)

    # Batch update
    results = ops.update_records("Events", updates)

    # Batch delete
    results = ops.delete_records("Events", record_ids)
"""

import time
from typing import List, Dict, Any, Optional, Callable, Iterator
from dataclasses import dataclass, field

from .exceptions import BatchError


@dataclass
class BatchResult:
    """Result of a batch operation."""

    successful: int = 0
    failed: int = 0
    total: int = 0
    created_ids: List[str] = field(default_factory=list)
    updated_ids: List[str] = field(default_factory=list)
    deleted_ids: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        """Return success rate as percentage."""
        if self.total == 0:
            return 100.0
        return (self.successful / self.total) * 100

    def __str__(self) -> str:
        return f"BatchResult(success={self.successful}/{self.total}, errors={self.failed})"


def chunk_list(lst: List[Any], chunk_size: int = 10) -> Iterator[List[Any]]:
    """Split a list into chunks of specified size."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]


class BatchOperations:
    """Batch operations with automatic chunking and progress reporting.

    Works with both sync and async clients.
    """

    BATCH_SIZE = 10  # Airtable's limit

    def __init__(
        self,
        api_call: Callable,
        batch_size: int = 10,
        delay_between_batches: float = 0.0,
    ):
        """Initialize batch operations.

        Args:
            api_call: Function to make API calls (client.request)
            batch_size: Records per batch (max 10)
            delay_between_batches: Seconds to wait between batches
        """
        self.api_call = api_call
        self.batch_size = min(batch_size, self.BATCH_SIZE)
        self.delay = delay_between_batches

    def create_records(
        self,
        base_id: str,
        table_id: str,
        records: List[Dict[str, Any]],
        typecast: bool = False,
        progress: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """Batch create records.

        Args:
            base_id: Airtable base ID
            table_id: Table ID or name
            records: List of field dictionaries
            typecast: Enable automatic field type conversion
            progress: Optional callback(current, total) for progress updates

        Returns:
            BatchResult with created record IDs
        """
        start_time = time.time()
        result = BatchResult(total=len(records))
        chunks = list(chunk_list(records, self.batch_size))

        for i, chunk in enumerate(chunks):
            try:
                # Build request payload
                payload = {"records": [{"fields": r} for r in chunk]}
                if typecast:
                    payload["typecast"] = True

                # Make API call
                response = self.api_call(
                    "POST",
                    f"/v0/{base_id}/{table_id}",
                    json=payload,
                )

                # Process response
                created = response.get("records", [])
                for rec in created:
                    result.created_ids.append(rec["id"])
                    result.successful += 1

            except Exception as e:
                # Record errors but continue
                for _ in chunk:
                    result.failed += 1
                    result.errors.append({
                        "batch": i,
                        "error": str(e),
                    })

            # Progress callback
            if progress:
                progress(
                    min((i + 1) * self.batch_size, len(records)),
                    len(records),
                )

            # Rate limit delay between batches
            if self.delay > 0 and i < len(chunks) - 1:
                time.sleep(self.delay)

        result.duration_seconds = time.time() - start_time
        return result

    def update_records(
        self,
        base_id: str,
        table_id: str,
        updates: List[Dict[str, Any]],
        typecast: bool = False,
        progress: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """Batch update records.

        Args:
            base_id: Airtable base ID
            table_id: Table ID or name
            updates: List of {"id": "recXXX", "fields": {...}}
            typecast: Enable automatic field type conversion
            progress: Optional callback(current, total)

        Returns:
            BatchResult with updated record IDs
        """
        start_time = time.time()
        result = BatchResult(total=len(updates))
        chunks = list(chunk_list(updates, self.batch_size))

        for i, chunk in enumerate(chunks):
            try:
                # Build request payload
                payload = {"records": chunk}
                if typecast:
                    payload["typecast"] = True

                # Make API call (PATCH for partial update)
                response = self.api_call(
                    "PATCH",
                    f"/v0/{base_id}/{table_id}",
                    json=payload,
                )

                # Process response
                updated = response.get("records", [])
                for rec in updated:
                    result.updated_ids.append(rec["id"])
                    result.successful += 1

            except Exception as e:
                for update in chunk:
                    result.failed += 1
                    result.errors.append({
                        "batch": i,
                        "record_id": update.get("id"),
                        "error": str(e),
                    })

            if progress:
                progress(
                    min((i + 1) * self.batch_size, len(updates)),
                    len(updates),
                )

            if self.delay > 0 and i < len(chunks) - 1:
                time.sleep(self.delay)

        result.duration_seconds = time.time() - start_time
        return result

    def delete_records(
        self,
        base_id: str,
        table_id: str,
        record_ids: List[str],
        progress: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """Batch delete records.

        Args:
            base_id: Airtable base ID
            table_id: Table ID or name
            record_ids: List of record IDs to delete
            progress: Optional callback(current, total)

        Returns:
            BatchResult with deleted record IDs
        """
        start_time = time.time()
        result = BatchResult(total=len(record_ids))
        chunks = list(chunk_list(record_ids, self.batch_size))

        for i, chunk in enumerate(chunks):
            try:
                # Build query params for delete
                params = "&".join([f"records[]={rid}" for rid in chunk])

                # Make API call
                response = self.api_call(
                    "DELETE",
                    f"/v0/{base_id}/{table_id}?{params}",
                )

                # Process response
                deleted = response.get("records", [])
                for rec in deleted:
                    if rec.get("deleted"):
                        result.deleted_ids.append(rec["id"])
                        result.successful += 1
                    else:
                        result.failed += 1

            except Exception as e:
                for rid in chunk:
                    result.failed += 1
                    result.errors.append({
                        "batch": i,
                        "record_id": rid,
                        "error": str(e),
                    })

            if progress:
                progress(
                    min((i + 1) * self.batch_size, len(record_ids)),
                    len(record_ids),
                )

            if self.delay > 0 and i < len(chunks) - 1:
                time.sleep(self.delay)

        result.duration_seconds = time.time() - start_time
        return result

    def upsert_records(
        self,
        base_id: str,
        table_id: str,
        records: List[Dict[str, Any]],
        fields_to_merge_on: List[str],
        typecast: bool = False,
        progress: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """Batch upsert (update or insert) records.

        Args:
            base_id: Airtable base ID
            table_id: Table ID or name
            records: List of field dictionaries
            fields_to_merge_on: Fields to use as unique key
            typecast: Enable automatic field type conversion
            progress: Optional callback(current, total)

        Returns:
            BatchResult with created/updated record IDs
        """
        start_time = time.time()
        result = BatchResult(total=len(records))
        chunks = list(chunk_list(records, self.batch_size))

        for i, chunk in enumerate(chunks):
            try:
                # Build request payload
                payload = {
                    "performUpsert": {
                        "fieldsToMergeOn": fields_to_merge_on,
                    },
                    "records": [{"fields": r} for r in chunk],
                }
                if typecast:
                    payload["typecast"] = True

                # Make API call (PATCH for upsert)
                response = self.api_call(
                    "PATCH",
                    f"/v0/{base_id}/{table_id}",
                    json=payload,
                )

                # Process response
                for rec in response.get("records", []):
                    if response.get("createdRecords", []):
                        result.created_ids.append(rec["id"])
                    else:
                        result.updated_ids.append(rec["id"])
                    result.successful += 1

            except Exception as e:
                for _ in chunk:
                    result.failed += 1
                    result.errors.append({
                        "batch": i,
                        "error": str(e),
                    })

            if progress:
                progress(
                    min((i + 1) * self.batch_size, len(records)),
                    len(records),
                )

            if self.delay > 0 and i < len(chunks) - 1:
                time.sleep(self.delay)

        result.duration_seconds = time.time() - start_time
        return result


def print_progress(current: int, total: int) -> None:
    """Simple progress printer for CLI usage."""
    pct = (current / total) * 100 if total > 0 else 100
    print(f"\r  Progress: {current}/{total} ({pct:.0f}%)", end="", flush=True)
    if current >= total:
        print()  # New line at end
