"""
Booking management for Bokun.
"""

from typing import Optional, List, Dict, Any
from datetime import date

from .client import BokunClient
from .models import Booking, BookingStatus


class BookingManager:
    """
    Manage Bokun bookings.

    Usage:
        async with BokunClient() as client:
            manager = BookingManager(client)
            booking = await manager.get("XWA-12345")
            print(f"{booking.customer_name}: {booking.product_title}")
    """

    def __init__(self, client: BokunClient):
        self.client = client

    async def get(self, confirmation_code: str) -> Booking:
        """Get booking by confirmation code."""
        data = await self.client.get_booking(confirmation_code)
        return Booking.from_api_response(data)

    async def get_raw(self, confirmation_code: str) -> Dict[str, Any]:
        """Get raw booking data."""
        return await self.client.get_booking(confirmation_code)

    async def search(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        customer_email: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> List[Booking]:
        """
        Search bookings.

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            customer_email: Filter by customer email
            statuses: Filter by status (CONFIRMED, PENDING, CANCELLED, ON_REQUEST)
            page: Page number (0-indexed)
            page_size: Results per page

        Returns:
            List of Booking objects
        """
        result = await self.client.search_bookings(
            date_from=date_from,
            date_to=date_to,
            customer_email=customer_email,
            statuses=statuses,
            page=page,
            page_size=page_size,
        )
        return [Booking.from_api_response(item) for item in result.get("items", [])]

    async def search_raw(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        customer_email: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Search bookings, return raw response."""
        return await self.client.search_bookings(
            date_from=date_from,
            date_to=date_to,
            customer_email=customer_email,
            statuses=statuses,
            page=page,
            page_size=page_size,
        )

    async def today(self) -> List[Booking]:
        """Get today's bookings."""
        today_str = date.today().isoformat()
        return await self.search(date_from=today_str, date_to=today_str)

    async def confirmed(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Booking]:
        """Get confirmed bookings."""
        return await self.search(
            date_from=date_from,
            date_to=date_to,
            statuses=["CONFIRMED"],
        )

    async def pending(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Booking]:
        """Get pending bookings."""
        return await self.search(
            date_from=date_from,
            date_to=date_to,
            statuses=["PENDING", "ON_REQUEST"],
        )

    async def by_customer(self, email: str) -> List[Booking]:
        """Get all bookings for a customer."""
        return await self.search(customer_email=email)

    async def count(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        statuses: Optional[List[str]] = None,
    ) -> int:
        """Count bookings matching criteria."""
        result = await self.client.search_bookings(
            date_from=date_from,
            date_to=date_to,
            statuses=statuses,
            page=0,
            page_size=1,
        )
        return result.get("totalHits", 0)
