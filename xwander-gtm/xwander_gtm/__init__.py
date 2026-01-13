"""
xwander-gtm: Google Tag Manager operations plugin.

This plugin provides modular GTM API operations for the xwander platform.
"""

from .client import GTMClient
from .workspace import WorkspaceManager
from .publishing import Publisher
from .tags import TagManager
from .triggers import TriggerManager
from .variables import VariableManager
from .exceptions import (
    GTMError,
    AuthenticationError,
    WorkspaceConflictError,
    PublishingError,
    RateLimitError,
    ValidationError,
    ResourceNotFoundError,
    DuplicateResourceError
)

__version__ = "1.1.0"
__all__ = [
    'GTMClient',
    'WorkspaceManager',
    'Publisher',
    'TagManager',
    'TriggerManager',
    'VariableManager',
    'GTMError',
    'AuthenticationError',
    'WorkspaceConflictError',
    'PublishingError',
    'RateLimitError',
    'ValidationError',
    'ResourceNotFoundError',
    'DuplicateResourceError'
]
