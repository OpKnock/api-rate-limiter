"""Authentication-based fingerprinter."""

from fastapi_420.fingerprinting.base import Fingerprinter, ClientIdentity
from fastapi_420.types import FingerprintLevel


class AuthFingerprinter(Fingerprinter):
    """Fingerprint based on authentication headers."""
    
    def __init__(self, level: FingerprintLevel = FingerprintLevel.NORMAL):
        self.level = level
    
    def fingerprint(self, identity: ClientIdentity) -> str:
        if self.level != FingerprintLevel.STRICT:
            return ""
        
        if not identity.auth_header:
            return "no-auth"
        
        # Extract token type and hash for privacy
        if identity.auth_header.startswith("Bearer "):
            token = identity.auth_header[7:]
            # Use first 8 chars of hash for identification
            return f"bearer:{hashlib.sha256(token.encode()).hexdigest()[:8]}"
        elif identity.auth_header.startswith("Basic "):
            return "basic-auth"
        elif identity.auth_header.startswith("ApiKey "):
            return "apikey"
        
        return "other-auth"