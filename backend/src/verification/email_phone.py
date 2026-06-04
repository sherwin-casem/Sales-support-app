"""OSS email and phone verification."""

from __future__ import annotations

import re

import dns.resolver
import phonenumbers
from phonenumbers import NumberParseException

from src.common.enums import EmailVerificationStatus, PhoneVerificationStatus

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def verify_email(email: str | None) -> EmailVerificationStatus:
    if not email or not email.strip():
        return EmailVerificationStatus.UNKNOWN
    addr = email.strip().lower()
    if not EMAIL_REGEX.match(addr):
        return EmailVerificationStatus.INVALID
    domain = addr.split("@", 1)[1]
    try:
        dns.resolver.resolve(domain, "MX")
        return EmailVerificationStatus.MX_FOUND
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, Exception):
        return EmailVerificationStatus.VALID_FORMAT


def verify_phone(phone: str | None, default_region: str = "US") -> PhoneVerificationStatus:
    if not phone or not phone.strip():
        return PhoneVerificationStatus.UNKNOWN
    try:
        parsed = phonenumbers.parse(phone.strip(), default_region)
        if phonenumbers.is_valid_number(parsed):
            return PhoneVerificationStatus.VALID_FORMAT
        return PhoneVerificationStatus.INVALID
    except NumberParseException:
        return PhoneVerificationStatus.INVALID
