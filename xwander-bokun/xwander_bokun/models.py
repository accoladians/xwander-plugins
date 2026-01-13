"""
Data models for Bokun API responses.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


class BookingStatus(str, Enum):
    """Booking status."""
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    ON_REQUEST = "ON_REQUEST"


class DifficultyLevel(str, Enum):
    """Experience difficulty level."""
    EASY = "EASY"
    MODERATE = "MODERATE"
    CHALLENGING = "CHALLENGING"
    EXTREME = "EXTREME"


class CapacityType(str, Enum):
    """Capacity management type."""
    LIMITED = "LIMITED"
    UNLIMITED = "UNLIMITED"
    ON_REQUEST = "ON_REQUEST"


@dataclass
class GeoPoint:
    """Geographic coordinates."""
    latitude: float
    longitude: float

    def to_dict(self) -> Dict[str, float]:
        return {"latitude": self.latitude, "longitude": self.longitude}


@dataclass
class Address:
    """Physical address."""
    address_line1: str
    city: str
    postal_code: str
    country_code: str = "FI"
    address_line2: str = ""
    state: str = ""
    geo_point: Optional[GeoPoint] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "addressLine1": self.address_line1,
            "addressLine2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postalCode": self.postal_code,
            "countryCode": self.country_code,
        }
        if self.geo_point:
            result["geoPoint"] = self.geo_point.to_dict()
        return result


@dataclass
class StartPoint:
    """Experience start location."""
    title: str
    address: Address
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "address": self.address.to_dict(),
        }


@dataclass
class LocationCode:
    """Location code for categorization."""
    country: str
    location: str
    name: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "country": self.country,
            "location": self.location,
            "name": self.name,
        }


@dataclass
class GooglePlace:
    """Google Place reference."""
    country: str
    country_code: str
    city: str
    name: str
    geo_location_center: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "country": self.country,
            "countryCode": self.country_code,
            "city": self.city,
            "cityCode": self.city,
            "name": self.name,
        }
        if self.geo_location_center:
            result["geoLocationCenter"] = self.geo_location_center
        return result


@dataclass
class StartTime:
    """Experience start time slot."""
    hour: int
    minute: int
    duration_hours: int
    duration_minutes: int = 0
    id: Optional[int] = None
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hour": self.hour,
            "minute": self.minute,
            "durationType": "H",
            "duration": self.duration_hours,
            "durationHours": self.duration_hours,
            "durationMinutes": self.duration_minutes,
            "durationDays": 0,
            "durationWeeks": 0,
        }


@dataclass
class PricingCategory:
    """Pricing category (Adult, Child, etc.)."""
    title: str
    ticket_category: str = "ADULT"
    min_per_booking: int = 1
    max_per_booking: int = 0
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "ticketCategory": self.ticket_category,
            "minPerBooking": self.min_per_booking,
            "maxPerBooking": self.max_per_booking,
            "occupancy": 1,
            "pricedPerPerson": True,
        }


@dataclass
class CancellationPolicy:
    """Cancellation policy reference."""
    id: int
    title: str

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "title": self.title}


@dataclass
class Experience:
    """Bokun experience/product."""
    title: str
    description: str
    duration_hours: int
    duration_minutes: int = 0
    difficulty_level: DifficultyLevel = DifficultyLevel.EASY
    capacity_type: CapacityType = CapacityType.ON_REQUEST
    id: Optional[int] = None
    excerpt: str = ""
    flags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    start_points: List[StartPoint] = field(default_factory=list)
    start_times: List[StartTime] = field(default_factory=list)
    pricing_categories: List[PricingCategory] = field(default_factory=list)
    location_code: Optional[LocationCode] = None
    google_place: Optional[GooglePlace] = None
    cancellation_policy_id: Optional[int] = None
    published: bool = False
    base_language: str = "en_GB"
    time_zone: str = "Europe/Helsinki"

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Experience":
        """Create Experience from Bokun API response."""
        start_points = []
        for sp in data.get("startPoints", []):
            addr_data = sp.get("address", {})
            geo = addr_data.get("geoPoint")
            address = Address(
                address_line1=addr_data.get("addressLine1", ""),
                address_line2=addr_data.get("addressLine2", ""),
                city=addr_data.get("city", ""),
                state=addr_data.get("state", ""),
                postal_code=addr_data.get("postalCode", ""),
                country_code=addr_data.get("countryCode", "FI"),
                geo_point=GeoPoint(geo["latitude"], geo["longitude"]) if geo else None,
            )
            start_points.append(StartPoint(
                id=sp.get("id"),
                title=sp.get("title", ""),
                address=address,
            ))

        start_times = []
        for st in data.get("startTimes", []):
            start_times.append(StartTime(
                id=st.get("id"),
                hour=st.get("hour", 0),
                minute=st.get("minute", 0),
                duration_hours=st.get("durationHours", 0),
                duration_minutes=st.get("durationMinutes", 0),
                label=st.get("label"),
            ))

        pricing_categories = []
        for pc in data.get("pricingCategories", []):
            pricing_categories.append(PricingCategory(
                id=pc.get("id"),
                title=pc.get("title", ""),
                ticket_category=pc.get("ticketCategory", "ADULT"),
                min_per_booking=pc.get("minPerBooking", 1),
                max_per_booking=pc.get("maxPerBooking", 0),
            ))

        loc_code = data.get("locationCode")
        location_code = LocationCode(
            country=loc_code.get("country", "FI"),
            location=loc_code.get("location", ""),
            name=loc_code.get("name", ""),
        ) if loc_code else None

        gp = data.get("googlePlace")
        google_place = GooglePlace(
            country=gp.get("country", ""),
            country_code=gp.get("countryCode", "FI"),
            city=gp.get("city", ""),
            name=gp.get("name", ""),
            geo_location_center=gp.get("geoLocationCenter"),
        ) if gp else None

        cancel_policy = data.get("cancellationPolicy")

        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            excerpt=data.get("excerpt", ""),
            duration_hours=data.get("durationHours", 0),
            duration_minutes=data.get("durationMinutes", 0),
            difficulty_level=DifficultyLevel(data.get("difficultyLevel", "EASY")),
            capacity_type=CapacityType(data.get("capacityType", "ON_REQUEST")),
            flags=data.get("flags", []),
            keywords=data.get("keywords", []),
            start_points=start_points,
            start_times=start_times,
            pricing_categories=pricing_categories,
            location_code=location_code,
            google_place=google_place,
            cancellation_policy_id=cancel_policy.get("id") if cancel_policy else None,
            published=data.get("published", False),
            base_language=data.get("baseLanguage", "en_GB"),
            time_zone=data.get("timeZone", "Europe/Helsinki"),
        )

    def to_create_payload(self) -> Dict[str, Any]:
        """Convert to API create payload."""
        payload = {
            "title": self.title,
            "description": self.description,
            "excerpt": self.excerpt or self.title[:100],
            "durationType": "HOURS",
            "durationHours": self.duration_hours,
            "durationMinutes": self.duration_minutes,
            "difficultyLevel": self.difficulty_level.value,
            "capacityType": self.capacity_type.value,
            "activityType": "DAY_TOUR_OR_ACTIVITY",
            "bookingType": "DATE_AND_TIME",
            "scheduleType": "RECURRING",
            "meetingType": "MEET_ON_LOCATION",
            "baseLanguage": self.base_language,
            "timeZone": self.time_zone,
            "flags": self.flags,
            "keywords": self.keywords,
            "published": self.published,
        }

        if self.start_points:
            payload["startPoints"] = [sp.to_dict() for sp in self.start_points]

        if self.start_times:
            payload["startTimes"] = [st.to_dict() for st in self.start_times]

        if self.pricing_categories:
            payload["pricingCategories"] = [pc.to_dict() for pc in self.pricing_categories]

        if self.location_code:
            payload["locationCode"] = self.location_code.to_dict()

        if self.google_place:
            payload["googlePlace"] = self.google_place.to_dict()

        if self.cancellation_policy_id:
            payload["cancellationPolicy"] = {"id": self.cancellation_policy_id}

        return payload


@dataclass
class Booking:
    """Bokun booking."""
    confirmation_code: str
    status: BookingStatus
    id: Optional[int] = None
    customer_name: str = ""
    customer_email: str = ""
    start_date: Optional[str] = None
    product_title: str = ""
    total_amount: Decimal = Decimal("0")
    currency: str = "EUR"

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Booking":
        """Create Booking from API response."""
        customer = data.get("customer", {})
        total_price = data.get("totalPrice", {})
        product_bookings = data.get("productBookings", [])

        return cls(
            id=data.get("id"),
            confirmation_code=data.get("confirmationCode", ""),
            status=BookingStatus(data.get("status", "PENDING")),
            customer_name=f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
            customer_email=customer.get("email", ""),
            start_date=data.get("startDate"),
            product_title=product_bookings[0].get("productTitle", "") if product_bookings else "",
            total_amount=Decimal(str(total_price.get("amount", 0))),
            currency=total_price.get("currency", "EUR"),
        )
