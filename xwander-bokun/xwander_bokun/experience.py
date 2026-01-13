"""
Experience/Product management for Bokun.
"""

from typing import Optional, List, Dict, Any

from .client import BokunClient
from .models import Experience


class ExperienceManager:
    """
    Manage Bokun experiences (products/tours).

    Usage:
        async with BokunClient() as client:
            manager = ExperienceManager(client)
            exp = await manager.get(1107193)
            print(exp.title)
    """

    def __init__(self, client: BokunClient):
        self.client = client

    async def get(self, experience_id: int) -> Experience:
        """Get experience by ID."""
        data = await self.client.get_experience(experience_id)
        return Experience.from_api_response(data)

    async def get_raw(self, experience_id: int) -> Dict[str, Any]:
        """Get raw experience data (for cloning)."""
        return await self.client.get_experience(experience_id)

    async def search(
        self,
        query: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> List[Experience]:
        """Search experiences."""
        result = await self.client.search_experiences(query, page, page_size)
        return [Experience.from_api_response(item) for item in result.get("items", [])]

    async def create(self, experience: Experience) -> Dict[str, Any]:
        """Create new experience."""
        payload = experience.to_create_payload()
        return await self.client.create_experience(payload)

    async def create_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create experience from raw dictionary (for cloning)."""
        return await self.client.create_experience(data)

    async def update_title(self, experience_id: int, title: str) -> Dict[str, Any]:
        """Update experience title."""
        return await self.client.update_experience_components(
            experience_id,
            {"title": {"value": title}},
        )

    async def update_description(
        self,
        experience_id: int,
        description: str,
        excerpt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update experience description."""
        data: Dict[str, Any] = {"description": {"value": description}}
        if excerpt:
            data["excerpt"] = {"value": excerpt}
        return await self.client.update_experience_components(experience_id, data)

    async def update_duration(
        self,
        experience_id: int,
        hours: int,
        minutes: int = 0,
    ) -> Dict[str, Any]:
        """Update experience duration."""
        return await self.client.update_experience_components(
            experience_id,
            {
                "duration": {
                    "hours": hours,
                    "minutes": minutes,
                    "days": 0,
                    "weeks": 0,
                }
            },
        )

    async def update_flags(
        self,
        experience_id: int,
        flags: List[str],
    ) -> Dict[str, Any]:
        """Update experience flags."""
        return await self.client.update_experience_components(
            experience_id,
            {"flags": flags},
        )

    async def add_flag(self, experience_id: int, flag: str) -> Dict[str, Any]:
        """Add a flag to experience."""
        components = await self.client.get_experience_components(
            experience_id,
            ["FLAGS"],
        )
        current_flags = components.get("flags", [])
        if flag not in current_flags:
            current_flags.append(flag)
            return await self.update_flags(experience_id, current_flags)
        return {"flags": current_flags}

    async def get_components(
        self,
        experience_id: int,
        components: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get specific components."""
        return await self.client.get_experience_components(experience_id, components)

    async def publish(self, experience_id: int) -> Dict[str, Any]:
        """Publish experience."""
        return await self.client.update_experience_components(
            experience_id,
            {"published": True},
        )

    async def unpublish(self, experience_id: int) -> Dict[str, Any]:
        """Unpublish experience."""
        return await self.client.update_experience_components(
            experience_id,
            {"published": False},
        )
