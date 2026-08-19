"""Composite fingerprinter with multiple strategies."""

import hashlib
from fastapi_420.fingerprinting.base import Fingerprinter, ClientIdentity
from fastapi_420.fingerprinting.ip import IPFingerprinter
from fastapi_420.fingerprinting.auth import AuthFingerprinter
from fastapi_420.fingerprinting.headers import HeaderFingerprinter
from fastapi_420.types import FingerprintLevel


class CompositeFingerprinter(Fingerprinter):
    """Composite fingerprinter combining multiple strategies."""
    
    def __init__(self, level: FingerprintLevel = FingerprintLevel.NORMAL):
        self.level = level
        self._fingerprinters = [
            IPFingerprinter(level),
            HeaderFingerprinter(level),
            AuthFingerprinter(level),
        ]
    
    def fingerprint(self, identity: ClientIdentity) -> str:
        parts = []
        for fp in self._fingerprinters:
            try:
                part = fp.fingerprint(identity)
                if part:
                    parts.append(part)
            except Exception:
                continue
        
        # Hash the combined parts for consistent length
        combined = "|".join(parts)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def add_fingerprinter(self, fingerprinter: Fingerprinter) -> None:
        """Add a custom fingerprinter."""
        self._fingerprinters.append(fingerprinter)