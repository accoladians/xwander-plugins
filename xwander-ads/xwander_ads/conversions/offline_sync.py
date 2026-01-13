"""
HubSpot Offline Conversion Sync

Syncs closed-won deals from HubSpot CRM to Google Ads as offline conversions.
Supports:
- GCLID-based attribution
- Enhanced Conversions for Leads (ECL) with hashed user data
- Multiple pipeline support (booking, sales, ecommerce)
- Automatic deduplication
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from .enhanced import EnhancedConversionsManager
from ..exceptions import GoogleAdsError

logger = logging.getLogger(__name__)


# HubSpot API Configuration
HUBSPOT_API_BASE = "https://api.hubapi.com"

# HubSpot Pipeline Configurations
PIPELINES = {
    "booking": {
        "id": "96154939",
        "name": "Booking Pipeline",
        "stages": [
            "176142515",  # Confirmed - Book Services
            "176125595",  # Confirmed - Ready
            "176095821",  # Pre-Trip (<30 days)
            "1247887007",  # Final Check Done
            "176125600",  # Trip in Progress
            "176125601",  # Post-Trip
            "176323495",  # Closed
        ]
    },
    "sales": {
        "id": "default",
        "name": "Sales Pipeline",
        "stages": [
            "176179781",  # Confirmed / Won
            "106622356",  # Closed
        ]
    },
    "ecommerce": {
        "id": "75e28846-ad0d-4be2-a027-5e1da6590b98",
        "name": "Ecommerce Pipeline",
        "stages": [
            "shipped",  # Completed
        ]
    }
}


class HubSpotOfflineSync:
    """Sync HubSpot deals to Google Ads offline conversions"""

    def __init__(
        self,
        google_ads_client: GoogleAdsClient,
        hubspot_token: str,
        customer_id: str,
        conversion_action_id: str
    ):
        """
        Initialize the HubSpot offline sync.

        Args:
            google_ads_client: Authenticated GoogleAdsClient instance
            hubspot_token: HubSpot private app access token
            customer_id: Google Ads customer ID
            conversion_action_id: Conversion action ID for offline conversions
        """
        self.client = google_ads_client
        self.hubspot_token = hubspot_token
        self.customer_id = customer_id
        self.conversion_action_id = conversion_action_id
        self.conversion_action_resource = (
            f"customers/{customer_id}/conversionActions/{conversion_action_id}"
        )

        # Initialize enhanced conversions manager for hashing
        self.ec_manager = EnhancedConversionsManager(google_ads_client)

        # HubSpot API headers
        self.hubspot_headers = {
            "Authorization": f"Bearer {hubspot_token}",
            "Content-Type": "application/json"
        }

    # ============================================================================
    # HUBSPOT DATA RETRIEVAL
    # ============================================================================

    def get_closed_deals(
        self,
        days: int = 90,
        pipeline: str = "booking",
        source_filter: Optional[str] = "paid_search",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch closed-won deals from HubSpot.

        Args:
            days: Look back N days (max 90 for GCLID validity)
            pipeline: Pipeline to query (booking, sales, ecommerce, all)
            source_filter: Filter by analytics source (paid_search, all, None)
            limit: Max deals to return

        Returns:
            List of deal objects with properties

        Raises:
            requests.RequestException: If HubSpot API request fails
        """
        # Calculate date range
        since_date = datetime.now() - timedelta(days=days)
        since_timestamp = int(since_date.timestamp() * 1000)

        # Determine stages to query
        if pipeline == "all":
            stages = []
            for p in PIPELINES.values():
                stages.extend(p["stages"])
            pipeline_name = "All Pipelines"
        elif pipeline in PIPELINES:
            stages = PIPELINES[pipeline]["stages"]
            pipeline_name = PIPELINES[pipeline]["name"]
        else:
            raise ValueError(f"Unknown pipeline: {pipeline}")

        logger.info(f"Fetching deals from {pipeline_name} closed since {since_date.date()}")

        # Build filters
        filters = [
            {
                "propertyName": "dealstage",
                "operator": "IN",
                "values": stages
            },
            {
                "propertyName": "closedate",
                "operator": "GTE",
                "value": str(since_timestamp)
            }
        ]

        # Add pipeline filter if specific pipeline requested
        if pipeline != "all" and pipeline in PIPELINES:
            pipeline_id = PIPELINES[pipeline]["id"]
            if pipeline_id != "default":  # Don't filter for default pipeline
                filters.append({
                    "propertyName": "pipeline",
                    "operator": "EQ",
                    "value": pipeline_id
                })

        # Add source filter
        if source_filter == "paid_search":
            filters.append({
                "propertyName": "hs_analytics_source",
                "operator": "EQ",
                "value": "PAID_SEARCH"
            })
            logger.info("Filtering for PAID_SEARCH source only")

        # Search request
        search_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/search"

        payload = {
            "filterGroups": [{
                "filters": filters
            }],
            "properties": [
                "dealname",
                "amount",
                "closedate",
                "dealstage",
                "pipeline",
                "hs_object_id",
                "hubspot_owner_id",
                "hs_analytics_source",
                "evaneos_dossier_id"
            ],
            "limit": min(limit or 100, 100),
            "sorts": [{"propertyName": "closedate", "direction": "DESCENDING"}]
        }

        response = requests.post(search_url, headers=self.hubspot_headers, json=payload)
        response.raise_for_status()

        deals = response.json().get('results', [])
        logger.info(f"Found {len(deals)} closed deals in {pipeline_name}")

        return deals[:limit] if limit else deals

    def get_deal_contact(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get primary contact associated with a deal.

        Args:
            deal_id: HubSpot deal ID

        Returns:
            Contact object with properties or None if not found

        Raises:
            requests.RequestException: If HubSpot API request fails
        """
        # Get associated contacts
        assoc_url = f"{HUBSPOT_API_BASE}/crm/v4/objects/deals/{deal_id}/associations/contacts"

        response = requests.get(assoc_url, headers=self.hubspot_headers)
        if response.status_code != 200:
            logger.warning(f"No contacts for deal {deal_id}")
            return None

        associations = response.json().get('results', [])
        if not associations:
            return None

        # Get first contact
        contact_id = associations[0].get('toObjectId')

        # Fetch contact properties
        contact_url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{contact_id}"
        params = {
            "properties": (
                "email,phone,hs_google_click_id,gclid,hs_analytics_source,"
                "hs_analytics_source_data_1,hs_analytics_source_data_2,"
                "firstname,lastname,address,city,state,zip,country"
            )
        }

        response = requests.get(contact_url, headers=self.hubspot_headers, params=params)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch contact {contact_id}")
            return None

        return response.json()

    # ============================================================================
    # CONVERSION BUILDING & UPLOAD
    # ============================================================================

    def build_conversion(
        self,
        deal: Dict[str, Any],
        contact: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Build conversion object from HubSpot deal and contact.

        Args:
            deal: HubSpot deal object
            contact: HubSpot contact object

        Returns:
            Conversion dict ready for upload or None if insufficient data
        """
        props = deal.get('properties', {})
        contact_props = contact.get('properties', {}) if contact else {}

        # Get identifiers - check both native and custom GCLID properties
        gclid = contact_props.get('hs_google_click_id') or contact_props.get('gclid')
        email = contact_props.get('email')
        phone = contact_props.get('phone')

        # Must have at least GCLID or email for attribution
        if not gclid and not email:
            logger.debug(f"Skipping deal {props.get('hs_object_id')}: no GCLID or email")
            return None

        # Build conversion object
        conversion = {
            'deal_id': props.get('hs_object_id'),
            'deal_name': props.get('dealname', 'Unknown'),
            'amount': float(props.get('amount', 0) or 0),
            'closedate': props.get('closedate'),
            'gclid': gclid,
            'email': email,
            'phone': phone,
            'first_name': contact_props.get('firstname'),
            'last_name': contact_props.get('lastname'),
            'address': contact_props.get('address'),
            'city': contact_props.get('city'),
            'state': contact_props.get('state'),
            'postal_code': contact_props.get('zip'),
            'country_code': contact_props.get('country'),
            'source': contact_props.get('hs_analytics_source'),
            'campaign': contact_props.get('hs_analytics_source_data_1')
        }

        return conversion

    def prepare_click_conversion(
        self,
        conversion: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Prepare ClickConversion object for Google Ads API.

        Args:
            conversion: Conversion dict from build_conversion()

        Returns:
            ClickConversion protobuf object or None if invalid
        """
        # Parse close date
        try:
            closedate = conversion['closedate']
            if not closedate:
                logger.warning(f"No closedate for deal {conversion['deal_id']}")
                return None

            # Try ISO format first (e.g., "2025-11-04T10:41:39.612Z")
            if isinstance(closedate, str) and 'T' in closedate:
                closedate_clean = closedate.replace('Z', '+00:00')
                conversion_time = datetime.fromisoformat(closedate_clean)
            else:
                # Try milliseconds timestamp
                closedate_ms = int(closedate)
                conversion_time = datetime.fromtimestamp(closedate_ms / 1000)

            # Format: yyyy-mm-dd hh:mm:ss+|-hh:mm (Google Ads format)
            conversion_datetime = conversion_time.strftime('%Y-%m-%d %H:%M:%S+00:00')

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid closedate for deal {conversion['deal_id']}: {e}")
            return None

        # Build click conversion
        click_conversion = self.client.get_type("ClickConversion")
        click_conversion.conversion_action = self.conversion_action_resource
        click_conversion.conversion_date_time = conversion_datetime
        click_conversion.conversion_value = conversion['amount']
        click_conversion.currency_code = "EUR"
        click_conversion.order_id = f"hubspot_deal_{conversion['deal_id']}"

        # Primary attribution: GCLID
        if conversion['gclid']:
            click_conversion.gclid = conversion['gclid']

        # Enhanced Conversions for Leads: hashed user data
        hashed_data = self.ec_manager.hash_user_data(
            email=conversion.get('email'),
            phone=conversion.get('phone'),
            first_name=conversion.get('first_name'),
            last_name=conversion.get('last_name'),
            street_address=conversion.get('address'),
            city=conversion.get('city'),
            region=conversion.get('state'),
            postal_code=conversion.get('postal_code'),
            country_code=conversion.get('country_code')
        )

        # Add user identifiers if we have hashed data
        if hashed_data:
            user_identifier = self.client.get_type("UserIdentifier")

            if 'hashed_email' in hashed_data:
                user_identifier.hashed_email = hashed_data['hashed_email']

            if 'hashed_phone_number' in hashed_data:
                user_identifier.hashed_phone_number = hashed_data['hashed_phone_number']

            # Add name and address if available
            if 'hashed_first_name' in hashed_data:
                user_identifier.hashed_first_name = hashed_data['hashed_first_name']

            if 'hashed_last_name' in hashed_data:
                user_identifier.hashed_last_name = hashed_data['hashed_last_name']

            address_info = self.client.get_type("OfflineUserAddressInfo")
            address_fields_added = False

            if 'hashed_street_address' in hashed_data:
                address_info.hashed_street_address = hashed_data['hashed_street_address']
                address_fields_added = True

            if 'hashed_city' in hashed_data:
                address_info.hashed_city = hashed_data['hashed_city']
                address_fields_added = True

            if 'hashed_region' in hashed_data:
                address_info.hashed_region = hashed_data['hashed_region']
                address_fields_added = True

            if 'hashed_postal_code' in hashed_data:
                address_info.hashed_postal_code = hashed_data['hashed_postal_code']
                address_fields_added = True

            if 'hashed_country_code' in hashed_data:
                address_info.hashed_country_code = hashed_data['hashed_country_code']
                address_fields_added = True

            if address_fields_added:
                user_identifier.address_info = address_info

            click_conversion.user_identifiers.append(user_identifier)

        # Consent (required for EU)
        click_conversion.consent.ad_user_data = self.client.enums.ConsentStatusEnum.GRANTED
        click_conversion.consent.ad_personalization = self.client.enums.ConsentStatusEnum.GRANTED

        return click_conversion

    def upload_conversions(
        self,
        conversions: List[Any]
    ) -> Dict[str, Any]:
        """
        Upload conversions to Google Ads.

        Args:
            conversions: List of ClickConversion protobuf objects

        Returns:
            Dict with upload results (success count, failed count, errors)

        Raises:
            GoogleAdsError: If upload fails
        """
        if not conversions:
            return {'success': 0, 'failed': 0, 'errors': []}

        service = self.client.get_service("ConversionUploadService")

        request = self.client.get_type("UploadClickConversionsRequest")
        request.customer_id = self.customer_id
        request.conversions = conversions
        request.partial_failure = True

        try:
            response = service.upload_click_conversions(request=request)

            results = {
                'success': 0,
                'failed': 0,
                'errors': []
            }

            # Count successes
            for result in response.results:
                if result.gclid or result.user_identifiers:
                    results['success'] += 1
                else:
                    results['failed'] += 1

            # Check partial failures
            if response.partial_failure_error:
                results['errors'].append(str(response.partial_failure_error))

            logger.info(
                f"Upload complete: {results['success']} succeeded, "
                f"{results['failed']} failed"
            )

            return results

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            raise GoogleAdsError(f"Failed to upload conversions: {error_msg}")

    # ============================================================================
    # MAIN SYNC WORKFLOW
    # ============================================================================

    def sync(
        self,
        days: int = 90,
        pipeline: str = "booking",
        source_filter: Optional[str] = "paid_search",
        limit: Optional[int] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Sync HubSpot deals to Google Ads offline conversions.

        Args:
            days: Look back N days (max 90 for GCLID validity)
            pipeline: Pipeline to sync (booking, sales, ecommerce, all)
            source_filter: Filter by analytics source (paid_search, all, None)
            limit: Max deals to process
            dry_run: Preview only, don't upload

        Returns:
            Dict with sync results and statistics

        Example:
            >>> syncer = HubSpotOfflineSync(client, token, customer_id, conversion_id)
            >>> results = syncer.sync(days=30, pipeline="booking", dry_run=True)
            >>> print(f"Ready to sync: {results['conversions_ready']}")
        """
        # Fetch deals
        deals = self.get_closed_deals(
            days=days,
            pipeline=pipeline,
            source_filter=source_filter,
            limit=limit
        )

        if not deals:
            logger.info("No deals found in specified period")
            return {
                'deals_found': 0,
                'conversions_ready': 0,
                'skipped': 0,
                'uploaded': 0
            }

        # Process each deal
        conversions = []
        click_conversions = []
        skipped_no_contact = 0
        skipped_no_identifier = 0
        skipped_evaneos = 0

        for deal in deals:
            deal_id = deal['properties'].get('hs_object_id')
            evaneos_dossier = deal['properties'].get('evaneos_dossier_id')

            # Skip Evaneos deals (separate referral platform)
            if evaneos_dossier:
                skipped_evaneos += 1
                continue

            # Get associated contact
            contact = self.get_deal_contact(deal_id)

            if not contact:
                skipped_no_contact += 1
                continue

            # Skip Evaneos proxy emails
            contact_email = contact.get('properties', {}).get('email', '')
            if contact_email and 'evaneos' in contact_email.lower():
                skipped_evaneos += 1
                continue

            # Build conversion
            conv = self.build_conversion(deal, contact)

            if not conv:
                skipped_no_identifier += 1
                continue

            conversions.append(conv)

            # Prepare for upload
            click_conv = self.prepare_click_conversion(conv)
            if click_conv:
                click_conversions.append(click_conv)

        # Results summary
        results = {
            'deals_found': len(deals),
            'conversions_ready': len(conversions),
            'skipped_no_contact': skipped_no_contact,
            'skipped_no_identifier': skipped_no_identifier,
            'skipped_evaneos': skipped_evaneos,
            'total_value': sum(c['amount'] for c in conversions),
            'gclid_count': sum(1 for c in conversions if c['gclid']),
            'email_only_count': sum(1 for c in conversions if not c['gclid'] and c['email']),
            'uploaded': 0,
            'upload_results': None
        }

        # Upload if not dry run
        if not dry_run and click_conversions:
            upload_results = self.upload_conversions(click_conversions)
            results['uploaded'] = upload_results['success']
            results['upload_results'] = upload_results

        return results
