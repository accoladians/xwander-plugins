"""CLI entry point for xwander-airtable plugin.

Provides command-line interface for Airtable operations.
Registered as 'xw airtable' command via plugin.json.

Usage:
    xw airtable list-bases
    xw airtable list-records --base app123 --table Events --formula '{Status} = "Active"'
    xw airtable batch-create --base app123 --table Events --file records.json
    xw airtable schema --base app123
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from .client import AirtableClient
from .formula import Formula, FormulaBuilder
from .exceptions import AirtableError


def handle_list_bases(args):
    """Handle 'xw airtable list-bases' command."""
    client = AirtableClient()

    bases = client.list_bases()

    if args.format == "json":
        print(json.dumps(bases, indent=2))
    else:
        print(f"\n=== Airtable Bases ({len(bases)}) ===\n")
        for base in bases:
            print(f"  {base['id']}: {base['name']}")
            if base.get("permissionLevel"):
                print(f"    Permission: {base['permissionLevel']}")
        print()


def handle_schema(args):
    """Handle 'xw airtable schema' command."""
    client = AirtableClient()

    schema = client.get_schema(args.base, use_cache=not args.no_cache)

    if args.format == "json":
        print(json.dumps(schema, indent=2))
    else:
        tables = schema.get("tables", [])
        print(f"\n=== Base {args.base} Schema ({len(tables)} tables) ===\n")
        for table in tables:
            print(f"  {table['id']}: {table['name']}")
            if args.fields:
                fields = table.get("fields", [])
                for field in fields:
                    print(f"    - {field['name']} ({field['type']})")
        print()


def handle_list_records(args):
    """Handle 'xw airtable list-records' command."""
    client = AirtableClient()

    # Build formula if provided
    formula = None
    if args.formula:
        formula = args.formula

    # Build sort if provided
    sort = None
    if args.sort:
        sort = [{"field": args.sort, "direction": args.sort_dir}]

    records = client.list_records(
        base_id=args.base,
        table=args.table,
        formula=formula,
        view=args.view,
        max_records=args.limit,
        sort=sort,
    )

    if args.format == "json":
        print(json.dumps(records, indent=2))
    else:
        print(f"\n=== {args.table} Records ({len(records)}) ===\n")
        for rec in records:
            fields = rec.get("fields", {})
            name = fields.get("Name", fields.get("name", rec["id"]))
            print(f"  {rec['id']}: {name}")
            if args.verbose:
                for key, value in fields.items():
                    if key.lower() != "name":
                        val_str = str(value)[:50]
                        print(f"    {key}: {val_str}")
        print()


def handle_get_record(args):
    """Handle 'xw airtable get-record' command."""
    client = AirtableClient()

    record = client.get_record(args.base, args.table, args.record_id)

    if args.format == "json":
        print(json.dumps(record, indent=2))
    else:
        print(f"\n=== Record {record['id']} ===\n")
        for key, value in record.get("fields", {}).items():
            print(f"  {key}: {value}")
        print()


def handle_create_record(args):
    """Handle 'xw airtable create-record' command."""
    client = AirtableClient()

    # Parse fields from JSON string or file
    if args.fields:
        fields = json.loads(args.fields)
    elif args.file:
        with open(args.file, "r") as f:
            fields = json.load(f)
    else:
        print("Error: Either --fields or --file required")
        sys.exit(1)

    record = client.create_record(args.base, args.table, fields, typecast=args.typecast)

    print(f"\n✓ Created record: {record['id']}")
    if args.format == "json":
        print(json.dumps(record, indent=2))
    print()


def handle_batch_create(args):
    """Handle 'xw airtable batch-create' command."""
    client = AirtableClient()

    # Load records from file
    with open(args.file, "r") as f:
        records = json.load(f)

    if not isinstance(records, list):
        print("Error: File must contain a JSON array of records")
        sys.exit(1)

    print(f"\nCreating {len(records)} records in {args.table}...\n")

    result = client.batch_create(
        args.base,
        args.table,
        records,
        typecast=args.typecast,
        progress=True,
    )

    print(f"\n=== Batch Create Complete ===")
    print(f"  Success: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Duration: {result.duration_seconds:.1f}s")

    if result.errors:
        print(f"\n  Errors:")
        for err in result.errors[:5]:
            print(f"    - {err}")

    if args.format == "json":
        print(json.dumps({
            "created_ids": result.created_ids,
            "successful": result.successful,
            "failed": result.failed,
            "errors": result.errors,
        }, indent=2))
    print()


def handle_batch_delete(args):
    """Handle 'xw airtable batch-delete' command."""
    client = AirtableClient()

    # Get record IDs from args or file
    if args.ids:
        record_ids = args.ids.split(",")
    elif args.file:
        with open(args.file, "r") as f:
            record_ids = [line.strip() for line in f if line.strip()]
    else:
        print("Error: Either --ids or --file required")
        sys.exit(1)

    if not args.yes:
        print(f"\nAbout to delete {len(record_ids)} records from {args.table}")
        confirm = input("Continue? [y/N] ")
        if confirm.lower() != "y":
            print("Aborted")
            sys.exit(0)

    print(f"\nDeleting {len(record_ids)} records...\n")

    result = client.batch_delete(
        args.base,
        args.table,
        record_ids,
        progress=True,
    )

    print(f"\n=== Batch Delete Complete ===")
    print(f"  Deleted: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Duration: {result.duration_seconds:.1f}s")
    print()


def handle_formula_test(args):
    """Handle 'xw airtable formula' command - test formula building."""

    # Build formula from parts
    builder = FormulaBuilder()

    if args.equals:
        for eq in args.equals:
            field, value = eq.split("=", 1)
            builder.where(field.strip(), value.strip())

    if args.contains:
        for c in args.contains:
            field, text = c.split(":", 1)
            builder.contains(field.strip(), text.strip())

    if args.after:
        field, date = args.after.split(":", 1)
        builder.after(field.strip(), date.strip())

    if args.raw:
        builder.raw(args.raw)

    try:
        formula = builder.build()
        print(f"\nFormula: {formula.build()}")
        print(f"Encoded: {formula.encode()}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main(args=None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Airtable CLI - AI-first operations",
        prog="xw airtable",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # list-bases
    bases_parser = subparsers.add_parser("list-bases", help="List accessible bases")
    bases_parser.add_argument("--format", choices=["table", "json"], default="table")

    # schema
    schema_parser = subparsers.add_parser("schema", help="Get base schema")
    schema_parser.add_argument("--base", "-b", required=True, help="Base ID")
    schema_parser.add_argument("--fields", "-f", action="store_true", help="Show fields")
    schema_parser.add_argument("--no-cache", action="store_true", help="Skip cache")
    schema_parser.add_argument("--format", choices=["table", "json"], default="table")

    # list-records
    list_parser = subparsers.add_parser("list-records", help="List records")
    list_parser.add_argument("--base", "-b", required=True, help="Base ID")
    list_parser.add_argument("--table", "-t", required=True, help="Table name/ID")
    list_parser.add_argument("--formula", help="Filter formula")
    list_parser.add_argument("--view", help="View name/ID")
    list_parser.add_argument("--sort", help="Sort by field")
    list_parser.add_argument("--sort-dir", default="asc", choices=["asc", "desc"])
    list_parser.add_argument("--limit", type=int, default=100, help="Max records")
    list_parser.add_argument("--verbose", "-v", action="store_true")
    list_parser.add_argument("--format", choices=["table", "json"], default="table")

    # get-record
    get_parser = subparsers.add_parser("get-record", help="Get single record")
    get_parser.add_argument("--base", "-b", required=True, help="Base ID")
    get_parser.add_argument("--table", "-t", required=True, help="Table name/ID")
    get_parser.add_argument("--record-id", "-r", required=True, help="Record ID")
    get_parser.add_argument("--format", choices=["table", "json"], default="table")

    # create-record
    create_parser = subparsers.add_parser("create-record", help="Create single record")
    create_parser.add_argument("--base", "-b", required=True, help="Base ID")
    create_parser.add_argument("--table", "-t", required=True, help="Table name/ID")
    create_parser.add_argument("--fields", help="JSON string of fields")
    create_parser.add_argument("--file", help="JSON file with fields")
    create_parser.add_argument("--typecast", action="store_true", help="Enable typecast")
    create_parser.add_argument("--format", choices=["table", "json"], default="table")

    # batch-create
    batch_create_parser = subparsers.add_parser("batch-create", help="Batch create records")
    batch_create_parser.add_argument("--base", "-b", required=True, help="Base ID")
    batch_create_parser.add_argument("--table", "-t", required=True, help="Table name/ID")
    batch_create_parser.add_argument("--file", required=True, help="JSON file with records array")
    batch_create_parser.add_argument("--typecast", action="store_true")
    batch_create_parser.add_argument("--format", choices=["table", "json"], default="table")

    # batch-delete
    batch_delete_parser = subparsers.add_parser("batch-delete", help="Batch delete records")
    batch_delete_parser.add_argument("--base", "-b", required=True, help="Base ID")
    batch_delete_parser.add_argument("--table", "-t", required=True, help="Table name/ID")
    batch_delete_parser.add_argument("--ids", help="Comma-separated record IDs")
    batch_delete_parser.add_argument("--file", help="File with record IDs (one per line)")
    batch_delete_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    batch_delete_parser.add_argument("--format", choices=["table", "json"], default="table")

    # formula (test formula building)
    formula_parser = subparsers.add_parser("formula", help="Build and test formulas")
    formula_parser.add_argument("--equals", "-e", action="append", help="Field=Value equality")
    formula_parser.add_argument("--contains", "-c", action="append", help="Field:Text contains")
    formula_parser.add_argument("--after", help="Field:Date after date")
    formula_parser.add_argument("--raw", help="Raw formula expression")

    # Parse
    args = parser.parse_args(args=args)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "list-bases":
            handle_list_bases(args)
        elif args.command == "schema":
            handle_schema(args)
        elif args.command == "list-records":
            handle_list_records(args)
        elif args.command == "get-record":
            handle_get_record(args)
        elif args.command == "create-record":
            handle_create_record(args)
        elif args.command == "batch-create":
            handle_batch_create(args)
        elif args.command == "batch-delete":
            handle_batch_delete(args)
        elif args.command == "formula":
            handle_formula_test(args)

    except AirtableError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(130)


if __name__ == "__main__":
    main()
