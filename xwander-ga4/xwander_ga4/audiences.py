"""GA4 Audience management"""

from typing import Any, Dict, List
from .client import GA4AdminClient


class AudienceManager:
    """Manage GA4 audiences"""

    def __init__(self, admin_client: GA4AdminClient):
        """
        Initialize AudienceManager

        Args:
            admin_client: GA4AdminClient instance for API access
        """
        self.admin = admin_client

    def list(self) -> List[Dict[str, Any]]:
        """List all audiences"""
        return self.admin.list_audiences()

    def filter_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """Filter audiences by name pattern"""
        audiences = self.list()
        return [a for a in audiences if name_pattern.lower() in a["name"].lower()]

    def get_by_name(self, name: str) -> Dict[str, Any]:
        """Get audience by exact name"""
        audiences = self.list()
        for audience in audiences:
            if audience["name"] == name:
                return audience
        return None

    def sorted_by_size(self) -> List[Dict[str, Any]]:
        """List audiences sorted by member count (largest first)"""
        audiences = self.list()
        return sorted(audiences, key=lambda a: a.get("member_count", 0), reverse=True)
