"""Export query results to various formats (CSV, JSON, etc.).

Provides functions to export Google Ads query results to different
file formats for further analysis.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional


class CSVExporter:
    """Export query results to CSV format."""

    @staticmethod
    def export(
        data: List[Dict[str, Any]],
        output_file: str,
        columns: Optional[List[str]] = None
    ) -> str:
        """Export results to CSV file.

        Args:
            data: Query results
            output_file: Output file path
            columns: Column names to export (default: all)

        Returns:
            Path to output file
        """
        if not data:
            raise ValueError("No data to export")

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        # Write CSV
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

        return str(output_path)

    @staticmethod
    def to_string(
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> str:
        """Export results to CSV string.

        Args:
            data: Query results
            columns: Column names to export (default: all)

        Returns:
            CSV string
        """
        if not data:
            return "No data"

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        # Build CSV string
        lines = [",".join(columns)]
        for row in data:
            values = [str(row.get(col, '')) for col in columns]
            lines.append(",".join(values))

        return "\n".join(lines)


class JSONExporter:
    """Export query results to JSON format."""

    @staticmethod
    def export(
        data: List[Dict[str, Any]],
        output_file: str,
        indent: int = 2
    ) -> str:
        """Export results to JSON file.

        Args:
            data: Query results
            output_file: Output file path
            indent: JSON indentation (default: 2)

        Returns:
            Path to output file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str)

        return str(output_path)

    @staticmethod
    def to_string(data: List[Dict[str, Any]], indent: int = 2) -> str:
        """Export results to JSON string.

        Args:
            data: Query results
            indent: JSON indentation (default: 2)

        Returns:
            JSON string
        """
        return json.dumps(data, indent=indent, default=str)


class MarkdownExporter:
    """Export query results to Markdown format."""

    @staticmethod
    def export(
        data: List[Dict[str, Any]],
        output_file: str,
        columns: Optional[List[str]] = None,
        title: Optional[str] = None
    ) -> str:
        """Export results to Markdown file.

        Args:
            data: Query results
            output_file: Output file path
            columns: Column names to export (default: all)
            title: Table title (optional)

        Returns:
            Path to output file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = MarkdownExporter.to_string(data, columns, title)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_path)

    @staticmethod
    def to_string(
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: Optional[str] = None
    ) -> str:
        """Export results to Markdown string.

        Args:
            data: Query results
            columns: Column names to export (default: all)
            title: Table title (optional)

        Returns:
            Markdown string
        """
        if not data:
            return "No data"

        # Determine columns
        if columns is None:
            columns = list(data[0].keys())

        lines = []

        # Add title
        if title:
            lines.append(f"# {title}\n")

        # Add header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        lines.append(header)
        lines.append(separator)

        # Add rows
        for row in data:
            values = [str(row.get(col, '')) for col in columns]
            line = "| " + " | ".join(values) + " |"
            lines.append(line)

        # Add footer
        lines.append(f"\n*Total rows: {len(data)}*")

        return "\n".join(lines)


class BigQueryExporter:
    """Export query results to BigQuery (placeholder for future implementation)."""

    @staticmethod
    def export(
        data: List[Dict[str, Any]],
        project_id: str,
        dataset_id: str,
        table_id: str
    ) -> str:
        """Export results to BigQuery table.

        Args:
            data: Query results
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID

        Returns:
            Table reference

        Raises:
            NotImplementedError: BigQuery export not yet implemented
        """
        raise NotImplementedError(
            "BigQuery export will be implemented in a future version. "
            "For now, use CSV export and import manually to BigQuery."
        )


def export_results(
    data: List[Dict[str, Any]],
    output_file: str,
    format: str = 'csv',
    **kwargs
) -> str:
    """Export query results to file.

    Args:
        data: Query results
        output_file: Output file path
        format: Export format ('csv', 'json', 'markdown')
        **kwargs: Additional format-specific arguments

    Returns:
        Path to output file

    Raises:
        ValueError: If format is not supported
    """
    if format == 'csv':
        return CSVExporter.export(data, output_file, **kwargs)
    elif format == 'json':
        return JSONExporter.export(data, output_file, **kwargs)
    elif format == 'markdown' or format == 'md':
        return MarkdownExporter.export(data, output_file, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format}")


def export_to_string(
    data: List[Dict[str, Any]],
    format: str = 'csv',
    **kwargs
) -> str:
    """Export query results to string.

    Args:
        data: Query results
        format: Export format ('csv', 'json', 'markdown')
        **kwargs: Additional format-specific arguments

    Returns:
        Exported string

    Raises:
        ValueError: If format is not supported
    """
    if format == 'csv':
        return CSVExporter.to_string(data, **kwargs)
    elif format == 'json':
        return JSONExporter.to_string(data, **kwargs)
    elif format == 'markdown' or format == 'md':
        return MarkdownExporter.to_string(data, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format}")
