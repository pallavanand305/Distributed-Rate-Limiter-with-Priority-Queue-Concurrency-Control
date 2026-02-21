from hypothesis import given, strategies as st, settings
from algorithms.token_bucket import TokenBucket

@given(rate=st.floats(min_value=1.0, max_value=1000.0), burst=st.integers(min_value=1, max_value=1000), refills=st.lists(st.floats(min_value=0.0, max_value=10.0), min_size=1, max_size=20))
@settings(max_examples=100)
def test_burst_capacity_enforcement(rate, burst, refills):
    tb = TokenBucket(rate, burst)
    tenant_id = 'tenant1'
    current_time = 0.0
    tb.refill(tenant_id, current_time)
    for time_delta in refills:
        current_time += time_delta
        tb.refill(tenant_id, current_time)
        assert tb.get_available_tokens(tenant_id) <= burst

@given(rate=st.floats(min_value=1.0, max_value=100.0), burst=st.integers(min_value=10, max_value=100), elapsed=st.floats(min_value=0.1, max_value=10.0))
@settings(max_examples=100)
def test_token_bucket_refill(rate, burst, elapsed):
    tb = TokenBucket(rate, burst)
    tenant_id = 'tenant1'
    tb.refill(tenant_id, 0.0)
    initial_tokens = tb.get_available_tokens(tenant_id)
    tb.consume(tenant_id, int(initial_tokens))
    tb.refill(tenant_id, elapsed)
    expected_tokens = min(burst, elapsed * rate)
    actual_tokens = tb.get_available_tokens(tenant_id)
    assert abs(actual_tokens - expected_tokens) < 0.01

@given(rate=st.floats(min_value=1.0, max_value=100.0), burst=st.integers(min_value=10, max_value=100))
@settings(max_examples=100)
def test_token_bucket_round_trip(rate, burst):
    tb = TokenBucket(rate, burst)
    tenant_id = 'tenant1'
    tb.refill(tenant_id, 0.0)
    initial = tb.get_available_tokens(tenant_id)
    assert initial == burst
    consumed = min(5, burst)
    assert tb.consume(tenant_id, consumed)
    assert tb.get_available_tokens(tenant_id) == burst - consumed
