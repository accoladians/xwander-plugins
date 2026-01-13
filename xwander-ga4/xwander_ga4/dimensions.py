"""GA4 Custom Dimensions and Metrics management"""

from typing import Any, Dict, List
from .client import GA4AdminClient
from .exceptions import GA4ValidationError


class DimensionManager:
    """Manage GA4 custom dimensions"""

    def __init__(self, admin_client: GA4AdminClient):
        """
        Initialize DimensionManager

        Args:
            admin_client: GA4AdminClient instance for API access
        """
        self.admin = admin_client

    def create(
        self,
        display_name: str,
        parameter_name: str,
        scope: str = "EVENT",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create custom dimension

        Args:
            display_name: User-friendly name (e.g., 'Product Type')
            parameter_name: Event parameter name (e.g., 'product_type')
            scope: 'EVENT', 'USER', or 'ITEM'
            description: Optional description

        Returns:
            Created dimension details
        """
        return self.admin.create_custom_dimension(
            display_name=display_name,
            parameter_name=parameter_name,
            scope=scope,
            description=description,
        )

    def list(self) -> List[Dict[str, Any]]:
        """List all custom dimensions"""
        return self.admin.list_custom_dimensions()

    def by_scope(self, scope: str) -> List[Dict[str, Any]]:
        """Get custom dimensions for a scope"""
        dimensions = self.list()
        return [d for d in dimensions if d["scope"] == scope]

    def get_by_name(self, parameter_name: str) -> Dict[str, Any]:
        """Get dimension by parameter name"""
        dimensions = self.list()
        for dim in dimensions:
            if dim["parameter_name"] == parameter_name:
                return dim
        return None

    @staticmethod
    def validate_parameter_name(name: str) -> None:
        """Validate parameter name format"""
        if not name or len(name) > 40:
            raise GA4ValidationError("Parameter name must be 1-40 characters")
        if not all(c.isalnum() or c == "_" for c in name):
            raise GA4ValidationError("Parameter name must be alphanumeric + underscore")
        if name[0].isdigit():
            raise GA4ValidationError("Parameter name cannot start with digit")

    @staticmethod
    def validate_display_name(name: str) -> None:
        """Validate display name"""
        if not name or len(name) > 100:
            raise GA4ValidationError("Display name must be 1-100 characters")
