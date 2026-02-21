from fastapi import FastAPI, HTTPException
import time
from storage.redis_simulator import RedisSimulator
from rate_limiter import RateLimiterEngine
from algorithms.priority_queue import PriorityQueue
from models import (
    RateLimitCheckRequest, RateLimitCheckResponse,
    QueueStatusResponse, QueueStats,
    TenantConfigRequest, TenantConfigResponse, TenantConfig
)

app = FastAPI(
    title="Distributed Rate Limiter",
    description="High-performance rate limiting service with priority-based scheduling",
    version="1.0.0"
)

# Initialize components
redis = RedisSimulator(latency_ms=1)
print("Redis initialized")
rate_limiter = RateLimiterEngine(redis)
print("Rate limiter initialized")
priority_queue = PriorityQueue()
print("Priority queue initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "distributed-rate-limiter"}

print("Health route registered")

@app.post("/v1/rate-limit/check", response_model=RateLimitCheckResponse)
async def check_rate_limit(request: RateLimitCheckRequest):
    """Check if request is within rate limits"""
    print("Rate limit check route being registered")
    try:
        timestamp = time.time()
        allowed, remaining, reset_time = await rate_limiter.check_and_increment(
            request.tenant_id, request.client_id, timestamp
        )
        
        if allowed:
            return RateLimitCheckResponse(
                allowed=True,
                remaining_quota=remaining,
                reset_time=reset_time,
                queued=False
            )
        else:
            # Add to priority queue
            priority_queue.insert(
                f"{request.tenant_id}:{request.client_id}:{timestamp}",
                request.priority,
                {
                    "tenant_id": request.tenant_id,
                    "client_id": request.client_id,
                    "timestamp": timestamp
                }
            )
            return RateLimitCheckResponse(
                allowed=False,
                remaining_quota=0,
                reset_time=reset_time,
                queued=True,
                queue_position=priority_queue.size()
            )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.get("/v1/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(tenant_id: str):
    """Get queue status for a tenant"""
    by_priority = {0: 0, 1: 0, 2: 0}
    oldest_age = None
    current_time = time.time()
    
    # Count requests for this tenant
    for item in priority_queue.heap:
        priority, seq, req_id, data = item
        if data.get("tenant_id") == tenant_id:
            by_priority[priority] += 1
            age = current_time - data.get("timestamp", current_time)
            if oldest_age is None or age > oldest_age:
                oldest_age = age
    
    total = sum(by_priority.values())
    stats = QueueStats(
        total_queued=total,
        by_priority=by_priority,
        oldest_request_age=oldest_age,
        average_wait_time=oldest_age / 2 if oldest_age else None
    )
    
    return QueueStatusResponse(tenant_id=tenant_id, stats=stats)


@app.put("/v1/tenant/config", response_model=TenantConfigResponse)
async def update_tenant_config(request: TenantConfigRequest):
    """Update tenant configuration"""
    try:
        # Validate configuration
        config = TenantConfig(
            tenant_id=request.tenant_id,
            rate_limit=request.rate_limit,
            burst_capacity=request.burst_capacity
        )
        
        # Update in rate limiter
        success = await rate_limiter.update_tenant_config(request.tenant_id, config)
        
        if not success:
            raise HTTPException(status_code=503, detail="Failed to update configuration")
        
        return TenantConfigResponse(
            tenant_id=request.tenant_id,
            rate_limit=request.rate_limit,
            burst_capacity=request.burst_capacity,
            updated=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
