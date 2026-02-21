import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

def test_rate_limit_check_allowed():
    response = client.post('/v1/rate-limit/check', json={
        'tenant_id': 'tenant1',
        'client_id': 'client1',
        'priority': 2
    })
    assert response.status_code == 200
    data = response.json()
    assert data['allowed'] == True
    assert 'remaining_quota' in data
    assert 'reset_time' in data

def test_rate_limit_check_queued():
    for i in range(150):
        client.post('/v1/rate-limit/check', json={
            'tenant_id': 'tenant2',
            'client_id': 'client2',
            'priority': 2
        })
    
    response = client.post('/v1/rate-limit/check', json={
        'tenant_id': 'tenant2',
        'client_id': 'client2',
        'priority': 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data['queued'] == True

def test_queue_status():
    response = client.get('/v1/queue/status?tenant_id=tenant1')
    assert response.status_code == 200
    data = response.json()
    assert 'stats' in data
    assert 'total_queued' in data['stats']

def test_tenant_config_update():
    response = client.put('/v1/tenant/config', json={
        'tenant_id': 'tenant3',
        'rate_limit': 50,
        'burst_capacity': 100
    })
    assert response.status_code == 200
    data = response.json()
    assert data['updated'] == True
    assert data['rate_limit'] == 50

def test_tenant_config_invalid():
    response = client.put('/v1/tenant/config', json={
        'tenant_id': 'tenant4',
        'rate_limit': 100,
        'burst_capacity': 50
    })
    assert response.status_code == 400
