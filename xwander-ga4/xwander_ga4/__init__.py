"""Xwander GA4 Plugin - Google Analytics 4 API wrapper"""

__version__ = "1.1.0"

from .client import GA4DataClient, GA4AdminClient
from .reports import ReportBuilder, ReportFormatter
from .dimensions import DimensionManager
from .audiences import AudienceManager
from .exceptions import (
    GA4Error,
    GA4ConfigError,
    GA4APIError,
    GA4ValidationError,
    GA4AuthError,
)

__all__ = [
    "GA4DataClient",
    "GA4AdminClient",
    "ReportBuilder",
    "ReportFormatter",
    "DimensionManager",
    "AudienceManager",
    "GA4Error",
    "GA4ConfigError",
    "GA4APIError",
    "GA4ValidationError",
    "GA4AuthError",
]
