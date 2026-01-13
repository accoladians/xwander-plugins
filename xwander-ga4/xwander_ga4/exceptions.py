"""GA4 API Exceptions"""


class GA4Error(Exception):
    """Base exception for GA4 operations"""
    pass


class GA4ConfigError(GA4Error):
    """Configuration error - missing credentials or invalid settings"""
    pass


class GA4APIError(GA4Error):
    """GA4 API returned an error"""
    pass


class GA4ValidationError(GA4Error):
    """Invalid request parameters"""
    pass


class GA4AuthError(GA4Error):
    """Authentication/authorization error"""
    pass
