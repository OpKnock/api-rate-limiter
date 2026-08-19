"""Tests for fingerprinting."""

import pytest

from fastapi_420.fingerprinting import IPFingerprinter, CompositeFingerprinter
from fastapi_420.fingerprinting.base import ClientIdentity
from fastapi_420.types import FingerprintLevel


class TestIPFingerprinter:
    def test_relaxed_level(self):
        fp = IPFingerprinter(FingerprintLevel.RELAXED)
        identity = ClientIdentity(ip="192.168.1.1", user_agent="Mozilla/5.0")
        result = fp.fingerprint(identity)
        assert result == "192.168.1.1"
    
    def test_normal_level(self):
        fp = IPFingerprinter(FingerprintLevel.NORMAL)
        identity = ClientIdentity(ip="192.168.1.1", user_agent="Mozilla/5.0")
        result = fp.fingerprint(identity)
        assert "192.168.1.1" in result
        assert "Mozilla" in result
    
    def test_strict_level(self):
        fp = IPFingerprinter(FingerprintLevel.STRICT)
        identity = ClientIdentity(
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            auth_header="Bearer token123",
            custom={"x-forwarded-for": "10.0.0.1"}
        )
        result = fp.fingerprint(identity)
        assert "192.168.1.1" in result
        assert "Mozilla" in result
        assert "Bearer" in result


class TestCompositeFingerprinter:
    def test_combines_fingerprinters(self):
        fp = CompositeFingerprinter(FingerprintLevel.NORMAL)
        identity = ClientIdentity(ip="192.168.1.1", user_agent="Mozilla/5.0")
        result = fp.fingerprint(identity)
        assert len(result) == 32  # SHA256 truncated
    
    def test_different_ips_produce_different_prints(self):
        fp = CompositeFingerprinter(FingerprintLevel.NORMAL)
        id1 = ClientIdentity(ip="192.168.1.1")
        id2 = ClientIdentity(ip="192.168.1.2")
        assert fp.fingerprint(id1) != fp.fingerprint(id2)