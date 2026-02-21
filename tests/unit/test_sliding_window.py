"""
Unit tests for sliding window rate limiter edge cases.
"""

import pytest
from algorithms.sliding_window import SlidingWindowCounter


class MockRedis:
    """Mock Redis for unit testing"""
    def __init__(self):
        self.data = {}
        
    async def get(self, key: str):
        return self.data.get(key)
    
    async def incr(self, key: str):
        val = int(self.data.get(key, "0"))
        val += 1
        self.data[key] = str(val)
        return val
    
    async def expire(self, key: str, seconds: int):
        pass


@pytest.mark.asyncio
async def test_window_boundary_transition():
    """Test requests at window boundaries"""
    redis = MockRedis()
    limiter = SlidingWindowCounter(10, 5, redis)
    client_id = "test_client"
    
    # Request at start of window
    allowed, remaining = await limiter.check_rate_limit(client_id, 1000.0)
    assert allowed
    assert remaining == 5  # Before increment, all quota available
    await limiter.increment_counter(client_id, 1000.0)
    
    # Request at end of window
    allowed, remaining = await limiter.check_rate_limit(client_id, 1009.9)
    assert allowed
    await limiter.increment_counter(client_id, 1009.9)
    
    # Request in next window
    allowed, remaining = await limiter.check_rate_limit(client_id, 1010.0)
    assert allowed


@pytest.mark.asyncio
async def test_empty_state():
    """Test with no previous requests"""
    redis = MockRedis()
    limiter = SlidingWindowCounter(60, 100, redis)
    client_id = "new_client"
    
    # First request should always be allowed
    allowed, remaining = await limiter.check_rate_limit(client_id, 1000.0)
    assert allowed
    assert remaining == 100  # Before increment, all quota available


@pytest.mark.asyncio
async def test_exact_limit_boundary():
    """Test behavior at exact limit"""
    redis = MockRedis()
    limiter = SlidingWindowCounter(10, 3, redis)
    client_id = "test_client"
    
    # Allow exactly 3 requests
    for i in range(3):
        allowed, _ = await limiter.check_rate_limit(client_id, 1000.0 + i * 0.1)
        assert allowed, f"Request {i+1} should be allowed"
        await limiter.increment_counter(client_id, 1000.0 + i * 0.1)
    
    # 4th request should be rejected
    allowed, remaining = await limiter.check_rate_limit(client_id, 1000.3)
    assert not allowed
    assert remaining == 0


@pytest.mark.asyncio
async def test_reset_time_calculation():
    """Test reset time calculation"""
    limiter = SlidingWindowCounter(60, 100)
    
    # Test at various timestamps
    reset_time = limiter.calculate_reset_time(1000.0)
    assert reset_time == 1020.0  # Next window boundary
    
    reset_time = limiter.calculate_reset_time(1050.5)
    assert reset_time == 1080.0


@pytest.mark.asyncio
async def test_multiple_clients_isolation():
    """Test that different clients have separate counters"""
    redis = MockRedis()
    limiter = SlidingWindowCounter(10, 2, redis)
    
    # Client 1 uses up their quota
    for i in range(2):
        allowed, _ = await limiter.check_rate_limit("client1", 1000.0 + i * 0.1)
        assert allowed
        await limiter.increment_counter("client1", 1000.0 + i * 0.1)
    
    # Client 1 should be rate limited
    allowed, _ = await limiter.check_rate_limit("client1", 1000.2)
    assert not allowed
    
    # Client 2 should still have quota
    allowed, _ = await limiter.check_rate_limit("client2", 1000.2)
    assert allowed
