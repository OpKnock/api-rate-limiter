"""IP-based fingerprinter."""

from fastapi_420.fingerprinting.base import Fingerprinter, ClientIdentity
from fastapi_420.types import FingerprintLevel


class IPFingerprinter(Fingerprinter):
    """Simple IP-based fingerprinting."""
    
    def __init__(self, level: FingerprintLevel = FingerprintLevel.NORMAL):
        self.level = level
    
    def fingerprint(self, identity: ClientIdentity) -> str:
        parts = [identity.ip]
        
        if self.level in (FingerprintLevel.NORMAL, FingerprintLevel.STRICT):
            if identity.user_agent:
                parts.append(identity.user_agent)
        
        if self.level == FingerprintLevel.STRICT:
            if identity.auth_header:
                parts.append(identity.auth_header)
            if identity.custom:
                parts.append(str(sorted(identity.custom.items())))
        
        return "|".join(parts)