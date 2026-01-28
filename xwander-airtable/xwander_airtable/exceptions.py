"""Custom exceptions for Airtable operations.

Standardized error handling with exit codes matching the plugin convention:
- 0: Success
- 1: Generic error
- 2: Rate limit/quota
- 3: Authentication
- 4: Not found
- 5: Validation error
- 6: Batch error
"""

from typing import Optional, Dict, Any


class AirtableError(Exception):
    """Base exception for Airtable operations."""

    exit_code = 1

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class RateLimitError(AirtableError):
    """Raised when rate limit (5 req/sec per base) is exceeded."""

    exit_code = 2

    def __init__(
        self,
        message: str = "Rate limit exceeded (5 req/sec)",
        retry_after: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after or 30.0


class AuthenticationError(AirtableError):
    """Raised when authentication fails."""

    exit_code = 3

    def __init__(
        self,
        message: str = "Authentication failed. Check AIRTABLE_TOKEN.",
        **kwargs,
    ):
        super().__init__(message, **kwargs)


class NotFoundError(AirtableError):
    """Raised when a resource is not found."""

    exit_code = 4

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs,
    ):
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(AirtableError):
    """Raised when input validation fails."""

    exit_code = 5

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.field = field


class BatchError(AirtableError):
    """Raised when a batch operation partially fails."""

    exit_code = 6

    def __init__(
        self,
        message: str,
        successful: int = 0,
        failed: int = 0,
        errors: Optional[list] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.successful = successful
        self.failed = failed
        self.errors = errors or []


class FormulaError(AirtableError):
    """Raised when formula building/validation fails."""

    exit_code = 5

    def __init__(
        self,
        message: str,
        formula: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.formula = formula


def raise_for_status(response: Dict[str, Any], status_code: int) -> None:
    """Raise appropriate exception based on Airtable error response."""
    error = response.get("error", {})
    error_type = error.get("type", "UNKNOWN_ERROR")
    error_message = error.get("message", "Unknown error")

    if status_code == 401:
        raise AuthenticationError(error_message, status_code=status_code, response=response)

    if status_code == 404:
        raise NotFoundError("Resource", "unknown", status_code=status_code, response=response)

    if status_code == 422:
        raise ValidationError(error_message, status_code=status_code, response=response)

    if status_code == 429:
        raise RateLimitError(error_message, status_code=status_code, response=response)

    raise AirtableError(f"{error_type}: {error_message}", status_code=status_code, response=response)
