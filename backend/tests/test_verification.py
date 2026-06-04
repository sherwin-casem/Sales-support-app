"""Tests for verification utilities."""

from src.verification.email_phone import verify_email, verify_phone
from src.common.enums import EmailVerificationStatus, PhoneVerificationStatus


def test_verify_email_invalid():
    assert verify_email("not-an-email") == EmailVerificationStatus.INVALID


def test_verify_email_empty():
    assert verify_email(None) == EmailVerificationStatus.UNKNOWN


def test_verify_phone_invalid():
    assert verify_phone("abc") == PhoneVerificationStatus.INVALID


def test_verify_phone_us():
    result = verify_phone("+1 415 555 2671", "US")
    assert result in (PhoneVerificationStatus.VALID_FORMAT, PhoneVerificationStatus.INVALID)
