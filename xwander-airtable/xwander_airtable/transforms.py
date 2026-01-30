"""Bulk transform operations for Airtable records.

High-level operations that combine schema introspection with
batch record updates for common tasks.

Usage:
    from xwander_airtable.transforms import Transforms

    t = Transforms(client)

    # Rename field values (auto-detects if field-level or record-level)
    result = t.rename_values("app123", "Events", "Track",
                             "Week Packages", "Holiday Packages")

    # Bulk set field value by formula
    result = t.set_values_where("app123", "Events",
                                field="Status", value="Done",
                                formula='{Track} = "Academy"')

    # Copy field values
    result = t.copy_field("app123", "Events",
                          from_field="Name", to_field="Display Name")
"""

from typing import Dict, Any, List, Optional, Union, Callable

from .formula import Formula, F
from .batch import BatchResult
from .field_ops import FieldOperations, SELECT_TYPES
from .exceptions import ValidationError


class TransformResult:
    """Result of a transform operation."""

    def __init__(
        self,
        method: str,
        records_affected: int = 0,
        batch_result: Optional[BatchResult] = None,
        field_updated: bool = False,
    ):
        self.method = method  # "field_rename" or "record_update"
        self.records_affected = records_affected
        self.batch_result = batch_result
        self.field_updated = field_updated

    def __str__(self) -> str:
        if self.method == "field_rename":
            return f"TransformResult(method=field_rename, affected={self.records_affected})"
        br = self.batch_result
        return (
            f"TransformResult(method=record_update, "
            f"success={br.successful}/{br.total}, "
            f"duration={br.duration_seconds:.1f}s)"
        )


class Transforms:
    """High-level transform operations on Airtable data.

    Combines schema awareness with batch operations to provide
    smart bulk transforms that choose the optimal strategy.
    """

    def __init__(self, client):
        """Initialize with an AirtableClient.

        Args:
            client: AirtableClient instance
        """
        self.client = client
        self.field_ops = FieldOperations(client)

    def rename_values(
        self,
        base_id: str,
        table: str,
        field_name: str,
        old_value: str,
        new_value: str,
        progress: Union[bool, Callable] = False,
    ) -> TransformResult:
        """Rename field values - auto-detects the optimal strategy.

        For select fields: renames the option at field level (instant, 1 API call).
        For text fields: batch updates all matching records.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field_name: Field name
            old_value: Current value to find
            new_value: New value to set
            progress: Show progress (for record-level updates)

        Returns:
            TransformResult with method used and records affected
        """
        # Check field type
        field_info = self.field_ops.get_field_info(base_id, table, field_name)

        if field_info["type"] in SELECT_TYPES:
            # Field-level rename (instant, affects all records)
            self.field_ops.rename_option(
                base_id, table, field_name, old_value, new_value
            )
            # Count affected records
            records = self.client.list_records(
                base_id, table,
                formula=F.equals(field_name, new_value),
                fields=[field_name],
            )
            return TransformResult(
                method="field_rename",
                records_affected=len(records),
                field_updated=True,
            )
        else:
            # Record-level update (batch)
            return self._batch_rename(
                base_id, table, field_name, old_value, new_value, progress
            )

    def _batch_rename(
        self,
        base_id: str,
        table: str,
        field_name: str,
        old_value: str,
        new_value: str,
        progress: Union[bool, Callable] = False,
    ) -> TransformResult:
        """Rename via record-level batch updates for non-select fields."""
        # Find all records with old value
        records = self.client.list_records(
            base_id, table,
            formula=F.equals(field_name, old_value),
            fields=[field_name],
        )

        if not records:
            return TransformResult(method="record_update", records_affected=0)

        # Build updates
        updates = [
            {"id": rec["id"], "fields": {field_name: new_value}}
            for rec in records
        ]

        # Execute batch update
        result = self.client.batch_update(
            base_id, table, updates, typecast=True, progress=progress
        )

        return TransformResult(
            method="record_update",
            records_affected=result.successful,
            batch_result=result,
        )

    def set_values_where(
        self,
        base_id: str,
        table: str,
        field: str,
        value: Any,
        formula: Union[Formula, str],
        typecast: bool = True,
        progress: Union[bool, Callable] = False,
    ) -> TransformResult:
        """Set a field value on all records matching a formula.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field: Field name to update
            value: New value
            formula: Filter formula
            typecast: Enable type conversion (default True)
            progress: Show progress

        Returns:
            TransformResult
        """
        # Find matching records
        records = self.client.list_records(
            base_id, table,
            formula=formula,
            fields=[field],
        )

        if not records:
            return TransformResult(method="record_update", records_affected=0)

        # Build updates
        updates = [
            {"id": rec["id"], "fields": {field: value}}
            for rec in records
        ]

        result = self.client.batch_update(
            base_id, table, updates, typecast=typecast, progress=progress
        )

        return TransformResult(
            method="record_update",
            records_affected=result.successful,
            batch_result=result,
        )

    def copy_field(
        self,
        base_id: str,
        table: str,
        from_field: str,
        to_field: str,
        formula: Optional[Union[Formula, str]] = None,
        transform_fn: Optional[Callable[[Any], Any]] = None,
        typecast: bool = True,
        progress: Union[bool, Callable] = False,
    ) -> TransformResult:
        """Copy values from one field to another.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            from_field: Source field name
            to_field: Destination field name
            formula: Optional filter formula
            transform_fn: Optional function to transform values
            typecast: Enable type conversion
            progress: Show progress

        Returns:
            TransformResult
        """
        records = self.client.list_records(
            base_id, table,
            formula=formula,
            fields=[from_field, to_field],
        )

        if not records:
            return TransformResult(method="record_update", records_affected=0)

        updates = []
        for rec in records:
            value = rec.get("fields", {}).get(from_field)
            if value is not None:
                if transform_fn:
                    value = transform_fn(value)
                updates.append({"id": rec["id"], "fields": {to_field: value}})

        if not updates:
            return TransformResult(method="record_update", records_affected=0)

        result = self.client.batch_update(
            base_id, table, updates, typecast=typecast, progress=progress
        )

        return TransformResult(
            method="record_update",
            records_affected=result.successful,
            batch_result=result,
        )

    def clear_field_where(
        self,
        base_id: str,
        table: str,
        field: str,
        formula: Union[Formula, str],
        progress: Union[bool, Callable] = False,
    ) -> TransformResult:
        """Clear a field value on all records matching a formula.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field: Field name to clear
            formula: Filter formula
            progress: Show progress

        Returns:
            TransformResult
        """
        return self.set_values_where(
            base_id, table, field, None, formula, progress=progress
        )
