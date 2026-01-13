"""
Custom exceptions for xwander-gtm plugin.

Exit codes:
    0: Success
    1: General error
    2: Rate limit error
    3: Authentication error
    4: Workspace conflict error
    5: Publishing error
"""


class GTMError(Exception):
    """Base exception for GTM operations"""
    exit_code = 1

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(GTMError):
    """Authentication failed"""
    exit_code = 3


class WorkspaceConflictError(GTMError):
    """Workspace has unresolved conflicts"""
    exit_code = 4


class PublishingError(GTMError):
    """Failed to publish version"""
    exit_code = 5


class RateLimitError(GTMError):
    """API rate limit exceeded"""
    exit_code = 2


class ValidationError(GTMError):
    """Validation failed (e.g., missing required fields)"""
    exit_code = 1


class ResourceNotFoundError(GTMError):
    """Requested resource not found"""
    exit_code = 1


class DuplicateResourceError(GTMError):
    """Resource already exists"""
    exit_code = 1
