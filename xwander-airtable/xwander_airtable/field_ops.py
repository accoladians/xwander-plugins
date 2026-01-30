"""Field operations for Airtable - manage select options, field metadata.

Fills a key MCP gap: the Airtable MCP cannot add, rename, or delete
single/multi-select field options.

Usage:
    from xwander_airtable.field_ops import FieldOperations

    ops = FieldOperations(client)

    # Rename a select option (updates the field definition)
    ops.rename_option("app123", "Events", "Track", "Week Packages", "Holiday Packages")

    # Add a new option
    ops.add_option("app123", "Events", "Track", "New Track", color="cyanLight2")

    # Get field info
    info = ops.get_field_info("app123", "Events", "Track")
"""

from typing import Dict, Any, List, Optional, Tuple

from .exceptions import AirtableError, ValidationError, NotFoundError


# Valid colors for select options
VALID_COLORS = [
    "blueLight2", "cyanLight2", "tealLight2", "greenLight2",
    "yellowLight2", "orangeLight2", "redLight2", "pinkLight2",
    "purpleLight2", "grayLight2",
    "blueBright", "cyanBright", "tealBright", "greenBright",
    "yellowBright", "orangeBright", "redBright", "pinkBright",
    "purpleBright", "grayBright",
    "blueDark1", "cyanDark1", "tealDark1", "greenDark1",
    "yellowDark1", "orangeDark1", "redDark1", "pinkDark1",
    "purpleDark1", "grayDark1",
]

SELECT_TYPES = ("singleSelect", "multipleSelects")


class FieldOperations:
    """Operations on Airtable field definitions.

    Provides methods to manage select field options and field metadata
    that the Airtable MCP server doesn't support.
    """

    def __init__(self, client):
        """Initialize with an AirtableClient instance.

        Args:
            client: AirtableClient instance (uses client.request and client.get_table_schema)
        """
        self.client = client

    def get_field_info(
        self, base_id: str, table: str, field_name: str
    ) -> Dict[str, Any]:
        """Get field definition including options for select fields.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field_name: Field name

        Returns:
            Field definition dict with id, name, type, options

        Raises:
            NotFoundError: If field not found
        """
        table_schema = self.client.get_table_schema(base_id, table)
        if not table_schema:
            raise NotFoundError("Table", table)

        for field in table_schema.get("fields", []):
            if field["name"] == field_name or field["id"] == field_name:
                return field

        raise NotFoundError("Field", field_name)

    def _get_select_field(
        self, base_id: str, table: str, field_name: str
    ) -> Tuple[Dict[str, Any], str]:
        """Get a select field and its table ID.

        Returns:
            Tuple of (field_definition, table_id)

        Raises:
            ValidationError: If field is not a select type
        """
        table_schema = self.client.get_table_schema(base_id, table)
        if not table_schema:
            raise NotFoundError("Table", table)

        table_id = table_schema["id"]

        for field in table_schema.get("fields", []):
            if field["name"] == field_name or field["id"] == field_name:
                if field["type"] not in SELECT_TYPES:
                    raise ValidationError(
                        f"Field '{field_name}' is type '{field['type']}', "
                        f"not a select field. Option operations only work on "
                        f"singleSelect and multipleSelects fields."
                    )
                return field, table_id

        raise NotFoundError("Field", field_name)

    def get_options(
        self, base_id: str, table: str, field_name: str
    ) -> List[Dict[str, str]]:
        """Get all options for a select field.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field_name: Select field name

        Returns:
            List of option dicts with id, name, color
        """
        field_def, _ = self._get_select_field(base_id, table, field_name)
        return field_def.get("options", {}).get("choices", [])

    def rename_option(
        self,
        base_id: str,
        table: str,
        field_name: str,
        old_name: str,
        new_name: str,
    ) -> Dict[str, Any]:
        """Rename a select field option.

        This updates the field definition so ALL records with the old value
        automatically get the new value. No record-level updates needed.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field_name: Select field name
            old_name: Current option name
            new_name: New option name

        Returns:
            Updated field definition

        Raises:
            NotFoundError: If option not found
            ValidationError: If new name already exists
        """
        field_def, table_id = self._get_select_field(base_id, table, field_name)
        choices = field_def.get("options", {}).get("choices", [])

        # Validate
        found = False
        for choice in choices:
            if choice["name"] == new_name:
                raise ValidationError(
                    f"Option '{new_name}' already exists in field '{field_name}'"
                )
            if choice["name"] == old_name:
                found = True

        if not found:
            raise NotFoundError("Option", old_name)

        # Build updated choices - rename the target, keep others as-is
        updated_choices = []
        for choice in choices:
            entry = {"id": choice["id"]}
            if choice["name"] == old_name:
                entry["name"] = new_name
            else:
                entry["name"] = choice["name"]
            updated_choices.append(entry)

        return self._update_field_options(
            base_id, table_id, field_def["id"], updated_choices
        )

    def add_option(
        self,
        base_id: str,
        table: str,
        field_name: str,
        option_name: str,
        color: str = "blueLight2",
    ) -> Dict[str, Any]:
        """Add a new option to a select field.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field_name: Select field name
            option_name: New option name
            color: Option color (default: blueLight2)

        Returns:
            Updated field definition

        Raises:
            ValidationError: If option already exists or invalid color
        """
        if color not in VALID_COLORS:
            raise ValidationError(
                f"Invalid color '{color}'. Valid: {', '.join(VALID_COLORS[:10])}..."
            )

        field_def, table_id = self._get_select_field(base_id, table, field_name)
        choices = field_def.get("options", {}).get("choices", [])

        # Check for duplicates
        for choice in choices:
            if choice["name"] == option_name:
                raise ValidationError(
                    f"Option '{option_name}' already exists in field '{field_name}'"
                )

        # Build choices: keep existing (by id+name), add new
        updated_choices = [
            {"id": c["id"], "name": c["name"]} for c in choices
        ]
        updated_choices.append({"name": option_name, "color": color})

        return self._update_field_options(
            base_id, table_id, field_def["id"], updated_choices
        )

    def delete_option(
        self,
        base_id: str,
        table: str,
        field_name: str,
        option_name: str,
    ) -> Dict[str, Any]:
        """Delete an option from a select field.

        WARNING: Records with this option will have the field cleared.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field_name: Select field name
            option_name: Option to delete

        Returns:
            Updated field definition
        """
        field_def, table_id = self._get_select_field(base_id, table, field_name)
        choices = field_def.get("options", {}).get("choices", [])

        found = False
        updated_choices = []
        for choice in choices:
            if choice["name"] == option_name:
                found = True
                continue  # Skip = delete
            updated_choices.append({"id": choice["id"], "name": choice["name"]})

        if not found:
            raise NotFoundError("Option", option_name)

        return self._update_field_options(
            base_id, table_id, field_def["id"], updated_choices
        )

    def reorder_options(
        self,
        base_id: str,
        table: str,
        field_name: str,
        order: List[str],
    ) -> Dict[str, Any]:
        """Reorder select field options.

        Args:
            base_id: Airtable base ID
            table: Table name or ID
            field_name: Select field name
            order: List of option names in desired order

        Returns:
            Updated field definition
        """
        field_def, table_id = self._get_select_field(base_id, table, field_name)
        choices = field_def.get("options", {}).get("choices", [])
        choice_map = {c["name"]: c for c in choices}

        updated_choices = []
        for name in order:
            if name not in choice_map:
                raise NotFoundError("Option", name)
            c = choice_map[name]
            updated_choices.append({"id": c["id"], "name": c["name"]})

        # Add any options not in the order list at the end
        for c in choices:
            if c["name"] not in order:
                updated_choices.append({"id": c["id"], "name": c["name"]})

        return self._update_field_options(
            base_id, table_id, field_def["id"], updated_choices
        )

    def _update_field_options(
        self,
        base_id: str,
        table_id: str,
        field_id: str,
        choices: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Update field options via the Airtable Meta API.

        Args:
            base_id: Base ID
            table_id: Table ID (not name)
            field_id: Field ID
            choices: Updated choices list

        Returns:
            Updated field definition
        """
        # Invalidate schema cache since we're changing the schema
        self.client.invalidate_cache(base_id)

        path = f"/v0/meta/bases/{base_id}/tables/{table_id}/fields/{field_id}"
        return self.client.request(
            "PATCH",
            path,
            json={"options": {"choices": choices}},
        )
