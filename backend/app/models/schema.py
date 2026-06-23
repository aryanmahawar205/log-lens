from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class NormalizedLogEntry(BaseModel):
    """
    Common schema for all parsed log entries.
    Every parser should emit this structure to the normalization layer.
    """
    upload_id: Optional[int] = Field(None, description="The dataset upload ID this entry belongs to")
    timestamp: datetime = Field(..., description="The time the request was received")
    ip: str = Field(..., description="Client IP address")
    method: str = Field(..., description="HTTP method (e.g., GET, POST)")
    url: str = Field(..., description="Requested URL path")
    query_string: Optional[str] = Field(None, description="Query string if present")
    status_code: int = Field(..., description="HTTP response status code")
    bytes_sent: int = Field(..., description="Number of bytes sent to the client")
    request_size_bytes: Optional[int] = Field(None, description="Number of bytes in the client request")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    referrer: Optional[str] = Field(None, description="HTTP Referer header")
    user_agent: Optional[str] = Field(None, description="User-Agent header")
    host: Optional[str] = Field(None, description="Host header")
    virtual_host: Optional[str] = Field(None, description="Virtual host handling the request")
    protocol: Optional[str] = Field(None, description="HTTP protocol version")

class SecurityFinding(BaseModel):
    """
    Standardized schema for security findings from any engine.
    """
    rule_id: str
    rule_title: str
    severity: str
    dataset_id: int
    timestamp: datetime
    ip: str
    evidence: List[str]
    sigma_source: Optional[str] = None
