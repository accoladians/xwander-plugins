"""
Enhanced Conversions Manager

Handles Enhanced Conversions for Web (ECW) and Enhanced Conversions for Leads (ECL).
Provides SHA256 hashing for user data and validation of enhanced conversion setup.
"""

import hashlib
import logging
import re
from typing import Dict, List, Optional, Any
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..exceptions import GoogleAdsError

logger = logging.getLogger(__name__)


class EnhancedConversionsManager:
    """Manage Enhanced Conversions for Web and Leads"""

    def __init__(self, client: GoogleAdsClient):
        """
        Initialize the enhanced conversions manager.

        Args:
            client: Authenticated GoogleAdsClient instance
        """
        self.client = client
        self._ga_service = client.get_service("GoogleAdsService")

    # ============================================================================
    # USER DATA NORMALIZATION & HASHING (SHA-256)
    # ============================================================================

    @staticmethod
    def normalize_email(email: str) -> Optional[str]:
        """
        Normalize email for hashing.

        Rules:
        - Convert to lowercase
        - Trim whitespace
        - Remove dots in Gmail addresses (gmail.com only)

        Args:
            email: Raw email address

        Returns:
            Normalized email or None if invalid
        """
        if not email:
            return None

        # Lowercase and trim
        email = email.lower().strip()

        # Validate basic email format
        if '@' not in email or '.' not in email:
            logger.warning(f"Invalid email format: {email}")
            return None

        # Gmail-specific: remove dots before @
        if email.endswith('@gmail.com'):
            local, domain = email.split('@')
            local = local.replace('.', '')
            email = f"{local}@{domain}"

        return email

    @staticmethod
    def normalize_phone(phone: str, default_country: str = '+358') -> Optional[str]:
        """
        Normalize phone number to E.164 format.

        Rules:
        - Remove all non-digits except leading +
        - Ensure leading + for E.164
        - Default to Finnish (+358) if no country code

        Args:
            phone: Raw phone number
            default_country: Default country code (default: +358 for Finland)

        Returns:
            E.164 formatted phone number or None if invalid

        Examples:
            >>> normalize_phone("040 123 4567")
            '+358401234567'
            >>> normalize_phone("+1 (555) 123-4567")
            '+15551234567'
        """
        if not phone:
            return None

        # Remove all non-digits except leading +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Must have at least some digits
        if not any(c.isdigit() for c in cleaned):
            logger.warning(f"Invalid phone number: {phone}")
            return None

        # Ensure leading + for E.164
        if not cleaned.startswith('+'):
            # Remove leading 1 for US numbers if default is +1
            if default_country == '+1' and cleaned.startswith('1'):
                cleaned = '+' + cleaned
            # Assume default country if starts with 0
            elif cleaned.startswith('0'):
                cleaned = default_country + cleaned[1:]
            else:
                cleaned = default_country + cleaned

        # Basic validation: E.164 should be 7-15 digits
        digit_count = sum(1 for c in cleaned if c.isdigit())
        if digit_count < 7 or digit_count > 15:
            logger.warning(f"Invalid phone number length: {phone} ({digit_count} digits)")
            return None

        return cleaned

    @staticmethod
    def normalize_name(name: str) -> Optional[str]:
        """
        Normalize first/last name for hashing.

        Rules:
        - Convert to lowercase
        - Trim whitespace
        - Remove special characters

        Args:
            name: Raw name

        Returns:
            Normalized name or None if invalid
        """
        if not name:
            return None

        # Lowercase and trim
        name = name.lower().strip()

        # Remove special characters (keep letters, spaces, hyphens)
        name = re.sub(r'[^a-z\s\-]', '', name)

        # Remove extra whitespace
        name = ' '.join(name.split())

        return name if name else None

    @staticmethod
    def sha256_hash(value: str) -> Optional[str]:
        """
        Generate SHA-256 hash for Enhanced Conversions.

        Args:
            value: Normalized value to hash

        Returns:
            Lowercase hexadecimal SHA-256 hash or None if value is empty
        """
        if not value:
            return None

        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    def hash_user_data(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        street_address: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        postal_code: Optional[str] = None,
        country_code: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Normalize and hash user data for Enhanced Conversions.

        Args:
            email: Email address
            phone: Phone number
            first_name: First name
            last_name: Last name
            street_address: Street address
            city: City
            region: State/region
            postal_code: ZIP/postal code
            country_code: 2-letter country code (ISO 3166-1 alpha-2)

        Returns:
            Dict with hashed user identifiers

        Example:
            >>> hash_user_data(
            ...     email="john.doe@example.com",
            ...     phone="040 123 4567",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )
            {
                'hashed_email': 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3',
                'hashed_phone_number': 'b3d8...',
                'hashed_first_name': 'f6e3...',
                'hashed_last_name': '2e6f...'
            }
        """
        hashed_data = {}

        # Email
        if email:
            normalized_email = self.normalize_email(email)
            if normalized_email:
                hashed_data['hashed_email'] = self.sha256_hash(normalized_email)

        # Phone
        if phone:
            normalized_phone = self.normalize_phone(phone)
            if normalized_phone:
                hashed_data['hashed_phone_number'] = self.sha256_hash(normalized_phone)

        # First name
        if first_name:
            normalized_first = self.normalize_name(first_name)
            if normalized_first:
                hashed_data['hashed_first_name'] = self.sha256_hash(normalized_first)

        # Last name
        if last_name:
            normalized_last = self.normalize_name(last_name)
            if normalized_last:
                hashed_data['hashed_last_name'] = self.sha256_hash(normalized_last)

        # Address fields
        if street_address:
            normalized_street = self.normalize_name(street_address)  # Same rules
            if normalized_street:
                hashed_data['hashed_street_address'] = self.sha256_hash(normalized_street)

        if city:
            normalized_city = self.normalize_name(city)
            if normalized_city:
                hashed_data['hashed_city'] = self.sha256_hash(normalized_city)

        if region:
            normalized_region = self.normalize_name(region)
            if normalized_region:
                hashed_data['hashed_region'] = self.sha256_hash(normalized_region)

        if postal_code:
            # Postal code: remove spaces, lowercase
            normalized_postal = postal_code.lower().replace(' ', '')
            hashed_data['hashed_postal_code'] = self.sha256_hash(normalized_postal)

        if country_code:
            # Country code: uppercase 2-letter code
            normalized_country = country_code.upper().strip()
            if len(normalized_country) == 2:
                hashed_data['hashed_country_code'] = self.sha256_hash(normalized_country.lower())

        return hashed_data

    # ============================================================================
    # ENHANCED CONVERSIONS STATUS CHECKING
    # ============================================================================

    def check_enhanced_conversions_status(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Check Enhanced Conversions configuration status.

        Args:
            customer_id: Google Ads customer ID

        Returns:
            Dict with ECW and ECL status information

        Raises:
            GoogleAdsError: If API request fails
        """
        query = """
            SELECT
                customer.id,
                customer.descriptive_name,
                customer.enhanced_conversions_for_leads_enabled
            FROM customer
            WHERE customer.id = customer.id
        """

        try:
            response = self._ga_service.search(customer_id=customer_id, query=query)

            customer_row = next(iter(response), None)
            if not customer_row:
                raise GoogleAdsError(f"Customer {customer_id} not found")

            customer = customer_row.customer

            return {
                'customer_id': customer.id,
                'customer_name': customer.descriptive_name,
                'ecl_enabled': customer.enhanced_conversions_for_leads_enabled,
                'ecw_status': 'Check via conversion action settings',
                'note': 'ECW is configured per conversion action, not at account level'
            }

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            raise GoogleAdsError(f"Failed to check enhanced conversions status: {error_msg}")

    def get_conversion_enhanced_status(
        self,
        customer_id: str,
        conversion_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get Enhanced Conversions configuration for conversion actions.

        Args:
            customer_id: Google Ads customer ID
            conversion_id: Optional specific conversion action ID

        Returns:
            List of dicts with conversion action EC status

        Raises:
            GoogleAdsError: If API request fails
        """
        where_clause = ""
        if conversion_id:
            where_clause = f"WHERE conversion_action.id = {conversion_id}"

        # Note: Enhanced conversions settings are not directly queryable
        # This returns conversion actions that support enhanced conversions
        query = f"""
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.type,
                conversion_action.status
            FROM conversion_action
            {where_clause}
        """

        try:
            response = self._ga_service.search(customer_id=customer_id, query=query)

            results = []
            for row in response:
                conv = row.conversion_action

                # Enhanced conversions are supported for WEBPAGE and UPLOAD_CLICKS types
                ec_supported = conv.type_.name in ['WEBPAGE', 'UPLOAD_CLICKS']

                results.append({
                    'id': conv.id,
                    'name': conv.name,
                    'type': conv.type_.name,
                    'status': conv.status.name,
                    'ec_supported': ec_supported,
                    'note': 'Configure ECW via GTM or API; ECL via offline uploads'
                })

            return results

        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            raise GoogleAdsError(f"Failed to get conversion EC status: {error_msg}")

    # ============================================================================
    # VALIDATION HELPERS
    # ============================================================================

    def validate_user_data(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        **other_fields
    ) -> Dict[str, Any]:
        """
        Validate user data for Enhanced Conversions.

        Args:
            email: Email address
            phone: Phone number
            **other_fields: Additional user data fields

        Returns:
            Dict with validation results and warnings

        Note:
            Enhanced Conversions requires at least email OR phone number.
            More data = better matching accuracy.
        """
        issues = []
        warnings = []

        # Check minimum requirement
        if not email and not phone:
            issues.append("Missing required field: email or phone number required")

        # Validate email
        if email:
            normalized_email = self.normalize_email(email)
            if not normalized_email:
                issues.append(f"Invalid email format: {email}")

        # Validate phone
        if phone:
            normalized_phone = self.normalize_phone(phone)
            if not normalized_phone:
                issues.append(f"Invalid phone number: {phone}")

        # Additional data improves matching
        has_name = other_fields.get('first_name') or other_fields.get('last_name')
        has_address = (
            other_fields.get('street_address') or
            other_fields.get('city') or
            other_fields.get('postal_code')
        )

        if not has_name:
            warnings.append("Name data missing - including name improves match rates")

        if not has_address:
            warnings.append("Address data missing - including address improves match rates")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendation': (
                'Include email + phone + name + address for best match rates (70-80%)'
            )
        }
