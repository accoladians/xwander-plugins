"""Custom exceptions for xwander-ads plugin."""


class AdsError(Exception):
    """Base exception for Google Ads operations."""
    exit_code = 1

    def __init__(self, message: str, exit_code: int = None):
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class AuthenticationError(AdsError):
    """Authentication/authorization failed."""
    exit_code = 3


class AssetGroupNotFoundError(AdsError):
    """Asset group not found."""
    exit_code = 4


class CampaignNotFoundError(AdsError):
    """Campaign not found."""
    exit_code = 4


class DuplicateSignalError(AdsError):
    """Signal already exists."""
    exit_code = 5


class QuotaExceededError(AdsError):
    """API quota exceeded."""
    exit_code = 2


class InvalidResourceError(AdsError):
    """Invalid resource name or ID."""
    exit_code = 6


class BudgetError(AdsError):
    """Budget operation failed."""
    exit_code = 7


class ValidationError(AdsError):
    """Validation failed."""
    exit_code = 8


class APIError(AdsError):
    """Generic API error."""
    exit_code = 1


class GoogleAdsError(AdsError):
    """Google Ads API error."""
    exit_code = 1


class RecommendationNotFoundError(AdsError):
    """Recommendation not found."""
    exit_code = 4
