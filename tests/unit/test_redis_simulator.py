import pytest
import asyncio
import time
from storage.redis_simulator import RedisSimulator

@pytest.mark.asyncio
async def test_basic_get_set():
    redis = RedisSimulator()
    await redis.set('key1', 'value1')
    value = await redis.get('key1')
    assert value == 'value1'

@pytest.mark.asyncio
async def test_atomic_incr():
    redis = RedisSimulator()
    tasks = [redis.incr('counter') for _ in range(10)]
    await asyncio.gather(*tasks)
    value = await redis.get('counter')
    assert value == 10

@pytest.mark.asyncio
async def test_hash_operations():
    redis = RedisSimulator()
    await redis.hset('hash1', 'field1', 'value1')
    await redis.hset('hash1', 'field2', 'value2')
    value1 = await redis.hget('hash1', 'field1')
    value2 = await redis.hget('hash1', 'field2')
    assert value1 == 'value1'
    assert value2 == 'value2'

@pytest.mark.asyncio
async def test_key_expiration():
    redis = RedisSimulator()
    await redis.set('temp_key', 'temp_value')
    await redis.expire('temp_key', 1)
    await asyncio.sleep(1.1)
    value = await redis.get('temp_key')
    assert value is None

@pytest.mark.asyncio
async def test_simulated_latency():
    redis = RedisSimulator(latency_ms=10.0)
    start = time.time()
    await redis.get('key')
    elapsed = (time.time() - start) * 1000
    assert elapsed >= 10.0
