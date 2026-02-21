import pytest
from algorithms.token_bucket import TokenBucket

def test_zero_tokens_consumption():
    tb = TokenBucket(10.0, 100)
    tb.refill('tenant1', 0.0)
    assert tb.consume('tenant1', 0)
    assert tb.get_available_tokens('tenant1') == 100

def test_refill_zero_elapsed():
    tb = TokenBucket(10.0, 100)
    tb.refill('tenant1', 0.0)
    tb.consume('tenant1', 50)
    tb.refill('tenant1', 0.0)
    assert tb.get_available_tokens('tenant1') == 50

def test_refill_exceeding_burst():
    tb = TokenBucket(10.0, 100)
    tb.refill('tenant1', 0.0)
    tb.refill('tenant1', 20.0)
    assert tb.get_available_tokens('tenant1') == 100

def test_negative_token_prevention():
    tb = TokenBucket(10.0, 100)
    tb.refill('tenant1', 0.0)
    assert not tb.consume('tenant1', 150)
    assert tb.get_available_tokens('tenant1') == 100

def test_consume_nonexistent_tenant():
    tb = TokenBucket(10.0, 100)
    assert not tb.consume('nonexistent', 10)
