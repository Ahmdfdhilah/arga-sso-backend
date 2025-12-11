from pydantic import BaseModel, Field
from datetime import datetime


class BaseResponse(BaseModel):
    error: bool = Field(False, description="Whether the request resulted in an error")
    message: str = Field(..., description="Response message")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp"
    )
