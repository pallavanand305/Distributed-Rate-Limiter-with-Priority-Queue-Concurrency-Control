import pytest
from pydantic import ValidationError
from models import TenantConfig, RequestMetadata, RateLimitState

def test_tenant_config_invalid_rate():
    with pytest.raises(ValidationError):
        TenantConfig(tenant_id='t1', rate_limit=0, burst_capacity=100)

def test_tenant_config_invalid_burst():
    with pytest.raises(ValidationError):
        TenantConfig(tenant_id='t1', rate_limit=100, burst_capacity=50)

def test_tenant_config_valid():
    config = TenantConfig(tenant_id='t1', rate_limit=100, burst_capacity=200)
    assert config.rate_limit == 100
    assert config.burst_capacity == 200

def test_request_metadata_invalid_priority():
    with pytest.raises(ValidationError):
        RequestMetadata(client_id='c1', tenant_id='t1', priority=3)

def test_request_metadata_valid():
    req = RequestMetadata(client_id='c1', tenant_id='t1', priority=1)
    assert req.priority == 1

def test_rate_limit_state_weighted_count():
    state = RateLimitState(current_count=10, window_start=0.0, window_size=1.0, max_requests=100)
    assert state.weighted_count(0.5) == 5.0
    assert state.weighted_count(1.0) == 0.0
