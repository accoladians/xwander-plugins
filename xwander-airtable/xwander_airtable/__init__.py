"""Xwander Airtable Toolkit - AI-first Airtable operations for Claude Code.

Complements the Airtable MCP server with:
- Rate limiting (5 req/sec per base)
- Formula builder for filterByFormula
- Batch operations (auto-batching in 10s)
- Schema caching to reduce API calls
- Field option management (add/rename/delete select options)
- Bulk transforms (rename values, set by formula, copy fields)
- typecast=True by default for LLM-friendly writes

Usage:
    from xwander_airtable import AirtableClient

    client = AirtableClient()

    # Formula builder
    from xwander_airtable.formula import F
    records = client.list_records("app123", "Events",
        formula=F.equals("Track", "Academy"))

    # Batch operations
    client.batch_create("app123", "Events", records, progress=True)

    # Field option management
    client.fields.rename_option("app123", "Events", "Track",
        "Week Packages", "Holiday Packages")

    # Bulk transforms
    result = client.transforms.rename_values("app123", "Events", "Track",
        "Week Packages", "Holiday Packages")
"""

__version__ = "1.1.0"
__author__ = "Xwander Growth Team"

from .client import AirtableClient
from .formula import Formula, FormulaBuilder
from .field_ops import FieldOperations
from .transforms import Transforms, TransformResult
from .exceptions import (
    AirtableError,
    RateLimitError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
)

__all__ = [
    "AirtableClient",
    "Formula",
    "FormulaBuilder",
    "FieldOperations",
    "Transforms",
    "TransformResult",
    "AirtableError",
    "RateLimitError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
]
