"""
Experience cloning functionality for Bokun.

Clone existing experiences with modified fields for new locations/variants.
Uses Bokun API v2.0 ExperienceComponentsDto schema.
"""

import copy
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from .client import BokunClient


@dataclass
class CloneConfig:
    """
    Configuration for cloning an experience.

    Specify which fields to modify in the cloned product.
    """

    # Required: new title
    title: str

    # Location changes
    new_city: Optional[str] = None
    new_address_line1: Optional[str] = None
    new_postal_code: Optional[str] = None
    new_latitude: Optional[float] = None
    new_longitude: Optional[float] = None
    new_start_point_title: Optional[str] = None

    # Content changes
    new_description: Optional[str] = None
    new_excerpt: Optional[str] = None

    # Timing changes
    new_start_hour: Optional[int] = None
    new_start_minute: Optional[int] = None
    new_duration_hours: Optional[int] = None

    # Additional flags to add
    add_flags: List[str] = field(default_factory=list)

    # Keywords to add
    add_keywords: List[str] = field(default_factory=list)

    # Keep as unpublished (default: True for safety)
    keep_unpublished: bool = True


def _map_v1_to_v2_payload(
    source_data: Dict[str, Any],
    config: CloneConfig,
) -> Dict[str, Any]:
    """
    Map v1 API experience data to v2.0 ExperienceComponentsDto format.

    Args:
        source_data: Original experience data from v1 API
        config: Clone configuration with modifications

    Returns:
        Payload ready for POST /restapi/v2.0/experience
    """
    # Extract source values
    source_activity_type = source_data.get("activityType", "DAY_TOUR_OR_ACTIVITY")
    source_booking_type = source_data.get("bookingType", "DATE_AND_TIME")
    source_capacity_type = source_data.get("capacityType", "ON_REQUEST")
    source_time_zone = source_data.get("timeZone", "Europe/Helsinki")

    # Build v2.0 payload with required fields
    payload = {
        # Required: title
        "title": config.title,

        # Required: experience type
        "type": source_activity_type,

        # Required: booking type
        "bookingType": source_booking_type,

        # Required: capacity type
        "capacityType": source_capacity_type,

        # Time zone
        "timeZone": source_time_zone,
    }

    # Description
    if config.new_description:
        payload["description"] = config.new_description
    elif source_data.get("description"):
        payload["description"] = source_data["description"]

    # Short description / excerpt
    if config.new_excerpt:
        payload["shortDescription"] = config.new_excerpt
    elif source_data.get("excerpt"):
        payload["shortDescription"] = source_data["excerpt"]

    # Duration
    duration_data = {}
    if config.new_duration_hours is not None:
        duration_data["hours"] = config.new_duration_hours
        duration_data["minutes"] = 0
        duration_data["days"] = 0
        duration_data["weeks"] = 0
    elif source_data.get("durationHours") is not None:
        duration_data["hours"] = source_data.get("durationHours", 0)
        duration_data["minutes"] = source_data.get("durationMinutes", 0)
        duration_data["days"] = source_data.get("durationDays", 0)
        duration_data["weeks"] = source_data.get("durationWeeks", 0)

    if duration_data:
        payload["duration"] = duration_data

    # Difficulty level
    if source_data.get("difficultyLevel"):
        payload["difficultyLevel"] = source_data["difficultyLevel"]

    # Min age
    if source_data.get("minAge"):
        payload["minAge"] = source_data["minAge"]

    # Flags
    flags = list(source_data.get("flags", []))
    for flag in config.add_flags:
        if flag not in flags:
            flags.append(flag)
    if flags:
        payload["flags"] = flags

    # Keywords
    keywords = list(source_data.get("keywords", []))
    for keyword in config.add_keywords:
        if keyword not in keywords:
            keywords.append(keyword)
    if keywords:
        payload["keywords"] = keywords

    # Cutoff settings
    cutoff = {
        "type": source_data.get("cutoffType", "RELATIVE_TO_START_TIME"),
        "minutes": source_data.get("bookingCutoffMinutes", 0),
        "hours": source_data.get("bookingCutoffHours", 0),
        "days": source_data.get("bookingCutoffDays", 0),
        "weeks": source_data.get("bookingCutoffWeeks", 8),
    }
    payload["cutoff"] = cutoff

    # On-request deadline (if on-request capacity)
    if source_capacity_type == "ON_REQUEST":
        on_request_deadline = {
            "minutes": source_data.get("requestDeadlineMinutes", 0),
            "hours": source_data.get("requestDeadlineHours", 0),
            "days": source_data.get("requestDeadlineDays", 3),
            "weeks": source_data.get("requestDeadlineWeeks", 0),
        }
        payload["onRequestDeadline"] = on_request_deadline

    # Start times - v2.0 uses flat duration fields
    source_start_times = source_data.get("startTimes", [])
    if source_start_times:
        start_times = []
        for st in source_start_times:
            start_time = {
                "hour": config.new_start_hour if config.new_start_hour is not None else st.get("hour", 20),
                "minute": config.new_start_minute if config.new_start_minute is not None else st.get("minute", 0),
                # Flat duration fields (not nested object)
                "durationHours": config.new_duration_hours if config.new_duration_hours is not None else st.get("durationHours", 0),
                "durationMinutes": st.get("durationMinutes", 0),
                "durationDays": st.get("durationDays", 0),
                "durationWeeks": st.get("durationWeeks", 0),
            }
            if st.get("label"):
                start_time["label"] = st["label"]
            if st.get("externalLabel"):
                start_time["externalLabel"] = st["externalLabel"]
            start_times.append(start_time)
        payload["startTimes"] = start_times

    # Pricing categories (required) - reference existing vendor-level categories by ID
    source_pricing_categories = source_data.get("pricingCategories", [])
    pricing_category_ids = []
    default_category_id = None

    for pc in source_pricing_categories:
        cat_id = pc.get("id")
        if cat_id:
            pricing_category_ids.append(cat_id)
            if pc.get("defaultCategory"):
                default_category_id = cat_id

    if not default_category_id and pricing_category_ids:
        default_category_id = pricing_category_ids[0]

    if pricing_category_ids:
        payload["pricingCategories"] = {
            "ids": pricing_category_ids,
            "defaultId": default_category_id,
        }

    # Rates (required) - define rate configurations
    source_rates = source_data.get("rates", [])
    rates_list = []
    default_rate_idx = None

    default_rate_external_id = f"rate-default-{config.title.replace(' ', '-').lower()}"

    for idx, rate in enumerate(source_rates):
        rate_data = {
            "title": rate.get("title", "Standard"),
            "minPerBooking": rate.get("minPerBooking", 1),
            "pricedPerPerson": rate.get("pricedPerPerson", True),
            "allPricingCategories": True,  # Use all pricing categories
            "allStartTimes": True,  # Use all start times
            "pickupSelectionType": "UNAVAILABLE",
            "dropoffSelectionType": "UNAVAILABLE",
            "tieredPricingEnabled": rate.get("tieredPricingEnabled", False),
        }

        # Assign externalId to first rate for referencing
        if idx == 0:
            rate_data["externalId"] = default_rate_external_id

        # Cancellation policy ID
        cancel_policy = rate.get("cancellationPolicy") or source_data.get("cancellationPolicy")
        if cancel_policy and cancel_policy.get("id"):
            rate_data["cancellationPolicyId"] = cancel_policy["id"]

        rates_list.append(rate_data)

    if rates_list:
        payload["rates"] = {
            "rates": rates_list,
            # Reference first rate by its externalId
            "defaultRate": {"externalId": default_rate_external_id},
        }

    # Pricing (required) - price catalog configuration
    source_price_catalogs = source_data.get("activityPriceCatalogs", [])
    price_catalog_currencies = []

    for cat in source_price_catalogs:
        catalog_id = cat.get("catalogId") or cat.get("catalog", {}).get("id")
        currencies = []
        default_currency = "EUR"
        for curr in cat.get("currencies", []):
            currencies.append(curr.get("currency", "EUR"))
            if curr.get("default"):
                default_currency = curr.get("currency", "EUR")

        if catalog_id:
            price_catalog_currencies.append({
                "priceCatalogId": catalog_id,
                "currencies": currencies or ["EUR"],
                "defaultCurrency": default_currency,
            })

    payload["pricing"] = {
        "experiencePriceRules": [],  # Empty for now, prices set via UI
        "extraPriceRules": [],
        "pickupPriceRules": [],
        "dropoffPriceRules": [],
        "priceCatalogCurrencies": price_catalog_currencies if price_catalog_currencies else [
            {"priceCatalogId": 51493, "currencies": ["EUR"], "defaultCurrency": "EUR"}
        ],
    }

    # Combo settings (required) - empty for non-combo products
    payload["combo"] = {
        "isCombo": False,
    }

    # Main pax info (required) - ContactInformationDto uses "type" not "field"
    source_main_contact = source_data.get("mainContactFields", [])
    main_pax_info = []
    for contact in source_main_contact:
        field_type = contact.get("field", "FIRST_NAME")
        main_pax_info.append({
            "type": field_type,
            "required": contact.get("required", True),
            "requiredBeforeDeparture": contact.get("requiredBeforeDeparture", False),
        })

    if not main_pax_info:
        # Default required fields
        main_pax_info = [
            {"type": "FIRST_NAME", "required": True, "requiredBeforeDeparture": False},
            {"type": "LAST_NAME", "required": True, "requiredBeforeDeparture": False},
            {"type": "EMAIL", "required": True, "requiredBeforeDeparture": False},
        ]

    payload["mainPaxInfo"] = main_pax_info
    payload["otherPaxInfo"] = []  # Empty but required

    # Location (GooglePlaceDto) - valid fields: state, placeId, countryCode, lookupLang, id, latitude, longitude, city, name
    if config.new_city or config.new_latitude:
        city = config.new_city or source_data.get("googlePlace", {}).get("city", "Rovaniemi")
        location = {
            "countryCode": "FI",
            "city": city,
            "name": f"{city}, Finland",
        }
        if config.new_latitude and config.new_longitude:
            location["latitude"] = config.new_latitude
            location["longitude"] = config.new_longitude
        payload["location"] = location
    elif source_data.get("googlePlace"):
        gp = source_data["googlePlace"]
        location = {
            "countryCode": gp.get("countryCode", "FI"),
            "city": gp.get("city", ""),
            "name": gp.get("name", ""),
        }
        # Extract coordinates from geoLocationCenter
        geo = gp.get("geoLocationCenter", {})
        if geo:
            location["latitude"] = geo.get("lat")
            location["longitude"] = geo.get("lng")
        payload["location"] = location

    # Availability rules (required, but can be empty for draft)
    # For a new product, we start with empty rules
    payload["availabilityRules"] = []

    # Note: guidanceTypes omitted for initial creation due to complex structure
    # Can be updated via PUT after creation if needed

    # Box settings (required) - set isBox to false for non-boxed products
    payload["boxSettings"] = {
        "isBox": False,
    }

    # Ticket settings (required) - uses barcodeFormat not barcodeType
    payload["ticket"] = {
        "ticketPerPerson": source_data.get("ticketPerPerson", False),
        "barcodeFormat": source_data.get("barcodeType", "QR_CODE"),
    }

    # Private experience flag (required)
    payload["privateExperience"] = source_data.get("privateActivity", False)

    # Allow customized bookings (required)
    payload["allowCustomizedBookings"] = source_data.get("allowCustomizedBookings", False)

    # Meeting type settings (required) - uses "type" not "meetingType"
    # ExperienceMeetingPointDto has: title, id, address (nested)
    meeting_point_addresses = []
    if config.new_city and config.new_latitude and config.new_longitude:
        meeting_point_addresses.append({
            "title": config.new_start_point_title or f"Meeting Point - {config.new_city}",
            "address": {
                "addressLine1": config.new_address_line1 or "",
                "city": config.new_city,
                "postalCode": config.new_postal_code or "",
                "countryCode": "FI",
                "latitude": config.new_latitude,
                "longitude": config.new_longitude,
            }
        })
    elif source_data.get("startPoints"):
        for sp in source_data["startPoints"]:
            addr = sp.get("address", {})
            geo = addr.get("geoPoint", {})
            meeting_point_addresses.append({
                "title": sp.get("title", "Meeting Point"),
                "address": {
                    "addressLine1": addr.get("addressLine1", ""),
                    "city": addr.get("city", ""),
                    "postalCode": addr.get("postalCode", ""),
                    "countryCode": addr.get("countryCode", "FI"),
                    "latitude": geo.get("latitude"),
                    "longitude": geo.get("longitude"),
                }
            })

    # For MEET_ON_LOCATION, only send basic fields
    payload["meetingType"] = {
        "type": source_data.get("meetingType", "MEET_ON_LOCATION"),
        "meetingPointAddresses": meeting_point_addresses,
        "dropoffService": source_data.get("dropoffService", False),
    }

    # Activation / publishing status - uses "activated" not "published"
    payload["activation"] = {
        "activated": not config.keep_unpublished,
    }

    # Marketplace visibility
    payload["marketplaceVisibilityType"] = source_data.get("marketplaceVisibilityType", "PRIVATE")

    return payload


async def clone_experience(
    client: BokunClient,
    source_id: int,
    config: CloneConfig,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Clone an experience with modifications.

    Args:
        client: Initialized BokunClient
        source_id: ID of experience to clone
        config: Clone configuration
        dry_run: If True, return payload without creating

    Returns:
        Created experience data (or payload if dry_run)

    Example:
        async with BokunClient() as client:
            config = CloneConfig(
                title="Aurora Camp Rovaniemi",
                new_city="Rovaniemi",
                new_address_line1="Koskikatu 25",
                new_latitude=66.5039,
                new_longitude=25.7294,
            )
            result = await clone_experience(client, 1107193, config)
            print(f"Created: {result.get('id')}")
    """
    # Get source experience (v1 API)
    source_data = await client.get_experience(source_id)

    # Map to v2.0 payload
    payload = _map_v1_to_v2_payload(source_data, config)

    if dry_run:
        return {"dry_run": True, "payload": payload}

    # Create the cloned experience via v2.0 API
    result = await client.create_experience(payload)

    return result


async def clone_for_rovaniemi(
    client: BokunClient,
    source_id: int,
    title: str,
    description: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to clone an Ivalo experience for Rovaniemi.

    Args:
        client: Initialized BokunClient
        source_id: ID of Ivalo experience to clone
        title: New title for Rovaniemi version
        description: Optional new description
        dry_run: If True, return payload without creating

    Returns:
        Created experience data
    """
    config = CloneConfig(
        title=title,
        new_city="Rovaniemi",
        new_address_line1="Koskikatu 25",  # Example Rovaniemi address
        new_postal_code="96200",
        new_latitude=66.5039,  # Rovaniemi center
        new_longitude=25.7294,
        new_start_point_title="Xwander Nordic - Rovaniemi",
        new_description=description,
        add_flags=["NORTHERN_LIGHTS"],
        add_keywords=["rovaniemi", "aurora", "northern lights"],
        keep_unpublished=True,
    )

    return await clone_experience(client, source_id, config, dry_run)
