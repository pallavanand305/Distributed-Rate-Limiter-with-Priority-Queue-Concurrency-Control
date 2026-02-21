import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from storage.redis_simulator import RedisSimulator

@given(increments=st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_atomic_counter_updates(increments):
    async def run_test():
        redis = RedisSimulator()
        tasks = [redis.incr('counter') for _ in range(increments)]
        await asyncio.gather(*tasks)
        final_value = await redis.get('counter')
        assert final_value == increments
    asyncio.run(run_test())
