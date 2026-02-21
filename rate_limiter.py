import time
from typing import Optional, Dict
from storage.redis_simulator import RedisSimulator
from algorithms.sliding_window import SlidingWindowCounter
from algorithms.token_bucket import TokenBucket
from models import TenantConfig

class RateLimiterEngine:
    def __init__(self, redis: RedisSimulator, default_rate: int = 100, default_burst: int = 200):
        self.redis = redis
        self.default_rate = default_rate
        self.default_burst = default_burst
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
    
    async def check_and_increment(self, tenant_id: str, client_id: str, timestamp: float) -> tuple[bool, int, float]:
        config = await self.get_tenant_config(tenant_id)
        
        key = f'{tenant_id}:{client_id}'
        if key not in self.sliding_windows:
            self.sliding_windows[key] = SlidingWindowCounter(window_size_seconds=1, max_requests=config.rate_limit, redis_client=self.redis)
        
        if tenant_id not in self.token_buckets:
            self.token_buckets[tenant_id] = TokenBucket(rate=config.rate_limit, burst_capacity=config.burst_capacity)
        
        tb = self.token_buckets[tenant_id]
        tb.refill(client_id, timestamp)
        
        sw = self.sliding_windows[key]
        allowed, remaining = await sw.check_rate_limit(client_id, timestamp)
        
        if allowed and tb.consume(client_id, 1):
            await sw.increment_counter(client_id, timestamp)
            reset_time = sw.calculate_reset_time(timestamp)
            return True, remaining, reset_time
        
        return False, 0, timestamp + 1.0
    
    async def get_tenant_config(self, tenant_id: str) -> TenantConfig:
        rate = await self.redis.hget(f'tenant:{tenant_id}', 'rate_limit')
        burst = await self.redis.hget(f'tenant:{tenant_id}', 'burst_capacity')
        
        if rate is None or burst is None:
            return TenantConfig(tenant_id=tenant_id, rate_limit=self.default_rate, burst_capacity=self.default_burst)
        
        return TenantConfig(tenant_id=tenant_id, rate_limit=int(rate), burst_capacity=int(burst))
    
    async def update_tenant_config(self, tenant_id: str, config: TenantConfig) -> bool:
        try:
            await self.redis.hset(f'tenant:{tenant_id}', 'rate_limit', config.rate_limit)
            await self.redis.hset(f'tenant:{tenant_id}', 'burst_capacity', config.burst_capacity)
            return True
        except Exception:
            return False
