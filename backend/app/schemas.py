
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MonitoredAPICreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    check_interval_seconds: int = Field(default=60, ge=10, le=86400)
    timeout_seconds: int = Field(default=10, ge=1, le=120)


class MonitoredAPIResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    method: str
    check_interval_seconds: int
    timeout_seconds: int
    is_active: bool
    created_at: datetime
