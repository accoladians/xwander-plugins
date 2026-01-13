"""Reporting module for Google Ads queries and reports.

This module provides:
- GAQL query builder (fluent API)
- Pre-built query templates
- Query execution and result formatting
- Export to CSV, JSON, Markdown, BigQuery
"""

from .gaql import GAQLBuilder, validate_query, format_query
from .templates import QueryTemplates, templates
from .reports import (
    execute_query,
    execute_query_stream,
    format_micros,
    format_percentage,
    TableFormatter,
)
from .export import (
    export_results,
    export_to_string,
    CSVExporter,
    JSONExporter,
    MarkdownExporter,
    BigQueryExporter,
)

__all__ = [
    # GAQL builder
    'GAQLBuilder',
    'validate_query',
    'format_query',
    # Templates
    'QueryTemplates',
    'templates',
    # Reports
    'execute_query',
    'execute_query_stream',
    'format_micros',
    'format_percentage',
    'TableFormatter',
    # Export
    'export_results',
    'export_to_string',
    'CSVExporter',
    'JSONExporter',
    'MarkdownExporter',
    'BigQueryExporter',
]
