"""Xwander Airtable Toolkit - AI-first Airtable operations for Claude Code.

Complements the Airtable MCP server with:
- Rate limiting (5 req/sec per base)
- Formula builder for filterByFormula
- Batch operations (auto-batching in 10s)
- Schema caching to reduce API calls
- Field type helpers
- Sync utilities

Usage:
    from xwander_airtable import AirtableClient

    client = AirtableClient()

    # Formula builder
    from xwander_airtable.formula import Formula
    f = Formula.equals("Status", "Active").and_(Formula.greater_than("Count", 10))

    # Batch operations
    client.batch_create("Events", records, progress=True)
"""

__version__ = "1.0.0"
__author__ = "Xwander Growth Team"

from .client import AirtableClient
from .formula import Formula, FormulaBuilder
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
    "AirtableError",
    "RateLimitError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
]
