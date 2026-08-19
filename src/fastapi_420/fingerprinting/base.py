"""Base fingerprinter class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ClientIdentity:
    """Client identity for fingerprinting."""
    ip: str
    user_agent: Optional[str] = None
    auth_header: Optional[str] = None
    custom: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip": self.ip,
            "user_agent": self.user_agent,
            "auth_header": self.auth_header,
            "custom": self.custom,
        }


class Fingerprinter(ABC):
    """Base class for client fingerprinting."""
    
    @abstractmethod
    def fingerprint(self, identity: ClientIdentity) -> str:
        """Generate fingerprint from client identity."""
        pass
    
    def extract_identity(self, request) -> ClientIdentity:
        """Extract identity from request. Override in subclasses."""
        return ClientIdentity(
            ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            auth_header=request.headers.get("authorization"),
        )
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP from request."""
        # Check forwarded headers
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"