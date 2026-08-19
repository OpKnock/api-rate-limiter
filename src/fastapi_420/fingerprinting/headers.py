"""Header-based fingerprinter."""

import hashlib
from fastapi_420.fingerprinting.base import Fingerprinter, ClientIdentity
from fastapi_420.types import FingerprintLevel


class HeaderFingerprinter(Fingerprinter):
    """Fingerprint based on request headers."""
    
    # Headers that are safe to include in fingerprint
    SAFE_HEADERS = {
        "accept",
        "accept-language",
        "accept-encoding",
        "user-agent",
    }
    
    def __init__(self, level: FingerprintLevel = FingerprintLevel.NORMAL):
        self.level = level
    
    def fingerprint(self, identity: ClientIdentity) -> str:
        if self.level == FingerprintLevel.RELAXED:
            return ""
        
        parts = []
        
        if identity.user_agent:
            parts.append(f"ua:{hashlib.sha256(identity.user_agent.encode()).hexdigest()[:8]}")
        
        return "|".join(parts)