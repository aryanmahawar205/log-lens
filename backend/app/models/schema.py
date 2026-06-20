from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class NormalizedLogEntry(BaseModel):
    """
    Common schema for all parsed log entries.
    Every parser should emit this structure to the normalization layer.
    """
    timestamp: datetime = Field(..., description="The time the request was received")
    ip: str = Field(..., description="Client IP address")
    method: str = Field(..., description="HTTP method (e.g., GET, POST)")
    url: str = Field(..., description="Requested URL path")
    query_string: Optional[str] = Field(None, description="Query string if present")
    status_code: int = Field(..., description="HTTP response status code")
    bytes_sent: int = Field(..., description="Number of bytes sent to the client")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    referrer: Optional[str] = Field(None, description="HTTP Referer header")
    user_agent: Optional[str] = Field(None, description="User-Agent header")
    host: Optional[str] = Field(None, description="Host header")
    protocol: Optional[str] = Field(None, description="HTTP protocol version")
