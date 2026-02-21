from pydantic import BaseModel, Field, validator
from typing import Optional
from dataclasses import dataclass

class TenantConfig(BaseModel):
    tenant_id: str
    rate_limit: int = Field(gt=0)
    burst_capacity: int = Field(gt=0)
    
    @validator('burst_capacity')
    def burst_must_be_gte_rate(cls, v, values):
        if 'rate_limit' in values and v < values['rate_limit']:
            raise ValueError('burst_capacity must be >= rate_limit')
        return v

class RequestMetadata(BaseModel):
    client_id: str
    tenant_id: str
    priority: int = Field(ge=0, le=2)
    timestamp: Optional[float] = None

class RateLimitState(BaseModel):
    current_count: int
    window_start: float
    window_size: float
    max_requests: int
    
    def weighted_count(self, current_time: float) -> float:
        elapsed = current_time - self.window_start
        if elapsed >= self.window_size:
            return 0.0
        weight = (self.window_size - elapsed) / self.window_size
        return self.current_count * weight

class QueueStats(BaseModel):
    total_queued: int
    by_priority: dict
    oldest_request_age: Optional[float] = None
    average_wait_time: Optional[float] = None

class RateLimitCheckRequest(BaseModel):
    tenant_id: str
    client_id: str
    priority: int = Field(default=2, ge=0, le=2)

class RateLimitCheckResponse(BaseModel):
    allowed: bool
    remaining_quota: Optional[int] = None
    reset_time: Optional[float] = None
    queued: bool = False
    queue_position: Optional[int] = None

class QueueStatusResponse(BaseModel):
    tenant_id: str
    stats: QueueStats

class TenantConfigRequest(BaseModel):
    tenant_id: str
    rate_limit: int = Field(gt=0)
    burst_capacity: int = Field(gt=0)

class TenantConfigResponse(BaseModel):
    tenant_id: str
    rate_limit: int
    burst_capacity: int
    updated: bool
