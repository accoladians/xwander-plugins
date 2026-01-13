"""
Tests for Enhanced Conversions Manager

Tests user data normalization, SHA-256 hashing, and validation.
"""

import pytest
from unittest.mock import Mock, MagicMock

from xwander_ads.conversions.enhanced import EnhancedConversionsManager


class TestUserDataNormalization:
    """Test user data normalization functions"""

    @pytest.fixture
    def ec_manager(self):
        """Create EnhancedConversionsManager with mocked client"""
        mock_client = Mock()
        return EnhancedConversionsManager(mock_client)

    def test_normalize_email_basic(self, ec_manager):
        """Test basic email normalization"""
        assert ec_manager.normalize_email("TEST@EXAMPLE.COM") == "test@example.com"
        assert ec_manager.normalize_email("  user@domain.com  ") == "user@domain.com"

    def test_normalize_email_gmail_dots(self, ec_manager):
        """Test Gmail dot removal"""
        assert ec_manager.normalize_email("john.doe@gmail.com") == "johndoe@gmail.com"
        assert ec_manager.normalize_email("a.b.c@gmail.com") == "abc@gmail.com"

        # Non-Gmail should keep dots
        assert ec_manager.normalize_email("john.doe@example.com") == "john.doe@example.com"

    def test_normalize_email_invalid(self, ec_manager):
        """Test invalid email handling"""
        assert ec_manager.normalize_email(None) is None
        assert ec_manager.normalize_email("") is None
        assert ec_manager.normalize_email("notanemail") is None
        assert ec_manager.normalize_email("missing@domain") is None

    def test_normalize_phone_finnish(self, ec_manager):
        """Test Finnish phone normalization"""
        # Finnish mobile starting with 0
        assert ec_manager.normalize_phone("040 123 4567") == "+358401234567"
        assert ec_manager.normalize_phone("0401234567") == "+358401234567"

        # Already has country code
        assert ec_manager.normalize_phone("+358 40 123 4567") == "+358401234567"

    def test_normalize_phone_international(self, ec_manager):
        """Test international phone normalization"""
        # US number with + prefix
        assert ec_manager.normalize_phone("+1 (555) 123-4567") == "+15551234567"

        # US number without + (will default to Finnish +358)
        # To override default, pass default_country parameter
        assert ec_manager.normalize_phone("1-555-123-4567", default_country="+1") == "+15551234567"

        # UK number
        assert ec_manager.normalize_phone("+44 20 7946 0958") == "+442079460958"

    def test_normalize_phone_invalid(self, ec_manager):
        """Test invalid phone handling"""
        assert ec_manager.normalize_phone(None) is None
        assert ec_manager.normalize_phone("") is None
        assert ec_manager.normalize_phone("abc") is None
        assert ec_manager.normalize_phone("123") is None  # Too short

    def test_normalize_name(self, ec_manager):
        """Test name normalization"""
        assert ec_manager.normalize_name("JOHN") == "john"
        assert ec_manager.normalize_name("  Mary  ") == "mary"
        assert ec_manager.normalize_name("Jean-Paul") == "jean-paul"
        assert ec_manager.normalize_name("O'Connor") == "oconnor"  # Removes apostrophe

    def test_normalize_name_invalid(self, ec_manager):
        """Test invalid name handling"""
        assert ec_manager.normalize_name(None) is None
        assert ec_manager.normalize_name("") is None
        assert ec_manager.normalize_name("   ") is None


class TestSHA256Hashing:
    """Test SHA-256 hashing"""

    @pytest.fixture
    def ec_manager(self):
        """Create EnhancedConversionsManager with mocked client"""
        mock_client = Mock()
        return EnhancedConversionsManager(mock_client)

    def test_sha256_hash_basic(self, ec_manager):
        """Test basic SHA-256 hashing"""
        # Known hash for "test"
        expected = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        assert ec_manager.sha256_hash("test") == expected

    def test_sha256_hash_email(self, ec_manager):
        """Test hashing normalized email"""
        email = "john.doe@gmail.com"
        normalized = ec_manager.normalize_email(email)  # -> johndoe@gmail.com
        hashed = ec_manager.sha256_hash(normalized)

        # Should be lowercase hex, 64 chars
        assert len(hashed) == 64
        assert hashed.islower()
        assert all(c in '0123456789abcdef' for c in hashed)

    def test_sha256_hash_empty(self, ec_manager):
        """Test hashing empty value"""
        assert ec_manager.sha256_hash(None) is None
        assert ec_manager.sha256_hash("") is None


class TestHashUserData:
    """Test complete user data hashing workflow"""

    @pytest.fixture
    def ec_manager(self):
        """Create EnhancedConversionsManager with mocked client"""
        mock_client = Mock()
        return EnhancedConversionsManager(mock_client)

    def test_hash_user_data_email_only(self, ec_manager):
        """Test hashing with email only"""
        result = ec_manager.hash_user_data(email="test@example.com")

        assert 'hashed_email' in result
        assert len(result['hashed_email']) == 64
        assert len(result) == 1  # Only email hashed

    def test_hash_user_data_full(self, ec_manager):
        """Test hashing with all fields"""
        result = ec_manager.hash_user_data(
            email="john.doe@gmail.com",
            phone="040 123 4567",
            first_name="John",
            last_name="Doe",
            street_address="123 Main St",
            city="Helsinki",
            region="Uusimaa",
            postal_code="00100",
            country_code="FI"
        )

        # Check all expected fields are present
        assert 'hashed_email' in result
        assert 'hashed_phone_number' in result
        assert 'hashed_first_name' in result
        assert 'hashed_last_name' in result
        assert 'hashed_street_address' in result
        assert 'hashed_city' in result
        assert 'hashed_region' in result
        assert 'hashed_postal_code' in result
        assert 'hashed_country_code' in result

        # All should be 64-char hex
        for key, value in result.items():
            assert len(value) == 64
            assert all(c in '0123456789abcdef' for c in value)

    def test_hash_user_data_invalid_fields(self, ec_manager):
        """Test hashing skips invalid fields"""
        result = ec_manager.hash_user_data(
            email="invalid",  # Invalid email
            phone="abc",      # Invalid phone
            first_name="John"  # Valid
        )

        # Should only hash the valid field
        assert 'hashed_first_name' in result
        assert 'hashed_email' not in result
        assert 'hashed_phone_number' not in result


class TestUserDataValidation:
    """Test user data validation"""

    @pytest.fixture
    def ec_manager(self):
        """Create EnhancedConversionsManager with mocked client"""
        mock_client = Mock()
        return EnhancedConversionsManager(mock_client)

    def test_validate_user_data_valid(self, ec_manager):
        """Test validation with valid data"""
        result = ec_manager.validate_user_data(
            email="test@example.com",
            phone="+358401234567",
            first_name="John",
            last_name="Doe"
        )

        assert result['valid'] is True
        assert len(result['issues']) == 0

    def test_validate_user_data_missing_identifier(self, ec_manager):
        """Test validation without email or phone"""
        result = ec_manager.validate_user_data(
            first_name="John",
            last_name="Doe"
        )

        assert result['valid'] is False
        assert any('email or phone' in issue.lower() for issue in result['issues'])

    def test_validate_user_data_invalid_email(self, ec_manager):
        """Test validation with invalid email"""
        result = ec_manager.validate_user_data(email="notanemail")

        assert result['valid'] is False
        assert any('invalid email' in issue.lower() for issue in result['issues'])

    def test_validate_user_data_warnings(self, ec_manager):
        """Test validation warnings for missing optional data"""
        result = ec_manager.validate_user_data(email="test@example.com")

        assert result['valid'] is True
        assert len(result['warnings']) > 0
        assert any('name' in warning.lower() for warning in result['warnings'])
        assert any('address' in warning.lower() for warning in result['warnings'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
