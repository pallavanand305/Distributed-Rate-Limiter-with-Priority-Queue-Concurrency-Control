# Distributed Rate Limiter with Priority Queue & Concurrency Control

A high-performance, distributed rate-limiting service with priority-based scheduling built with FastAPI, Redis (simulated), and AsyncIO. This system implements custom data structures and algorithms from first principles to handle high-scale infrastructure workloads similar to AWS API Gateway and Cloudflare.

## Features

- **Sliding Window Rate Limiting**: Precise rate limiting with O(1) space complexity per client
- **Priority Queue Scheduling**: Binary min-heap with FIFO ordering within priority levels
- **Multi-Tenant Fairness**: Isolated quotas and burst capacities per tenant
- **Token Bucket**: Controlled burst traffic management
- **Distributed Consistency**: Atomic operations across multiple API nodes
- **High Performance**: >10,000 req/s throughput, <5ms p95 latency

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             ▼                                ▼
    ┌────────────────┐              ┌────────────────┐
    │   API Node 1   │              │   API Node 2   │
    │   (FastAPI)    │              │   (FastAPI)    │
    └────────┬───────┘              └────────┬───────┘
             │                                │
             │         ┌────────────────┐    │
             └────────►│   API Node 3   │◄───┘
                       │   (FastAPI)    │
                       └────────┬───────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Redis Simulator     │
                    │  (Distributed State)  │
                    └───────────────────────┘
```

## Core Algorithms

### 1. Sliding Window Counter
- **Space Complexity**: O(1) per client
- **Time Complexity**: O(1) for check and increment
- Uses two buckets (current and previous) with weighted count calculation
- Handles window boundaries precisely

### 2. Binary Min-Heap Priority Queue
- **Time Complexity**: O(log n) for insert, extract_min, decrease_key
- Supports three priority levels: CRITICAL (0), HIGH (1), NORMAL (2)
- Preserves FIFO ordering within same priority
- Custom implementation using dynamic arrays

### 3. Token Bucket
- Allows controlled burst traffic
- Refills at configured rate per tenant
- Caps at burst_capacity

## Installation

```bash
# Clone the repository
git clone https://github.com/pallavanand305/Distributed-Rate-Limiter-with-Priority-Queue-Concurrency-Control.git
cd Distributed-Rate-Limiter-with-Priority-Queue-Concurrency-Control

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Start the Server

```bash
# Run the FastAPI server
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "distributed-rate-limiter"
}
```

### 2. Rate Limit Check

**POST** `/v1/rate-limit/check`

Check if a request should proceed or be queued.

```bash
curl -X POST http://localhost:8000/v1/rate-limit/check \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant1",
    "client_id": "client123",
    "priority": 2,
    "request_data": {}
  }'
```

Response (allowed):
```json
{
  "allowed": true,
  "remaining_quota": 95,
  "reset_time": 1708531200.0,
  "queued": false,
  "queue_position": null
}
```

Response (rate limited):
```json
{
  "allowed": false,
  "remaining_quota": 0,
  "reset_time": 1708531200.0,
  "queued": true,
  "queue_position": 5
}
```

### 3. Queue Status

**GET** `/v1/queue/status?tenant_id={id}`

Get queue depth and health metrics for a tenant.

```bash
curl "http://localhost:8000/v1/queue/status?tenant_id=tenant1"
```

Response:
```json
{
  "tenant_id": "tenant1",
  "total_queued": 10,
  "by_priority": {
    "0": 2,
    "1": 3,
    "2": 5
  },
  "oldest_request_age_seconds": 5.2,
  "average_wait_time_seconds": 2.8
}
```

### 4. Tenant Configuration

**PUT** `/v1/tenant/config`

Update rate limits and burst settings for a tenant.

```bash
curl -X PUT http://localhost:8000/v1/tenant/config \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant1",
    "rate_limit": 100,
    "burst_capacity": 150,
    "window_size_seconds": 60
  }'
```

Response:
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "applied_config": {
    "tenant_id": "tenant1",
    "rate_limit": 100,
    "burst_capacity": 150,
    "window_size_seconds": 60
  }
}
```

## Configuration

### Default Tenant Configuration

```python
{
    "rate_limit": 100,        # Requests per second
    "burst_capacity": 150,    # Maximum burst requests
    "window_size_seconds": 60 # Sliding window size
}
```

### Redis Simulator

The system uses a Redis simulator with configurable latency:

```python
redis = RedisSimulator(latency_ms=50)  # 50ms simulated latency
```

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Property-Based Tests

```bash
pytest tests/property/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Specific Test File

```bash
pytest tests/unit/test_sliding_window.py -v
```

## Running Benchmarks

```bash
python benchmark.py
```

Expected performance:
- **Throughput**: >10,000 requests/second
- **Latency**: p95 <5ms
- **Memory**: <1KB per active client

## Project Structure

```
.
├── algorithms/
│   ├── sliding_window.py    # Sliding window rate limiter
│   ├── priority_queue.py    # Binary min-heap implementation
│   └── token_bucket.py      # Token bucket algorithm
├── storage/
│   └── redis_simulator.py   # Redis simulator with latency
├── tests/
│   ├── unit/                # Unit tests
│   ├── property/            # Property-based tests
│   └── integration/         # Integration tests
├── models.py                # Pydantic data models
├── rate_limiter.py          # Rate limiter engine
├── main.py                  # FastAPI application
├── benchmark.py             # Performance benchmarks
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Design Decisions

### Sliding Window Algorithm

We use a two-bucket sliding window approach:
- **Precision**: Accurately handles window boundaries
- **Efficiency**: O(1) space per client
- **Trade-off**: Slight approximation at window transitions vs. perfect accuracy

### Priority Queue

Custom binary min-heap implementation:
- **Control**: Full control over performance characteristics
- **FIFO**: Sequence numbers ensure FIFO within priority levels
- **Efficiency**: O(log n) operations

### Token Bucket

Allows burst traffic while maintaining average rate:
- **Flexibility**: Handles legitimate traffic spikes
- **Fairness**: Per-tenant burst capacities
- **Simplicity**: Easy to reason about and configure

## Fault Tolerance

### Redis Failure Handling

- Graceful degradation with 503 responses
- Retry logic with exponential backoff
- No data loss on temporary failures

### Clock Skew

- Tolerates up to 100ms clock skew between nodes
- Uses weighted calculations for accuracy

### Hot Keys

- Atomic operations prevent race conditions
- Lock-based consistency for concurrent updates

## Scaling Strategy

### Horizontal Scaling

- Stateless API nodes
- Shared Redis for distributed state
- Load balancer for request distribution

### Millions of Tenants

- O(1) space per client
- Lazy initialization of tenant state
- TTL-based cleanup of inactive clients

### Performance Optimization

- Async I/O for non-blocking operations
- Batch operations where possible
- Minimal memory footprint

## Testing Strategy

### Property-Based Testing

Uses Hypothesis for comprehensive input coverage:
- 100+ iterations per property test
- Validates universal correctness properties
- Catches edge cases automatically

### Unit Testing

- Specific examples and edge cases
- Window boundaries, empty states, exact limits
- Error conditions and validation

### Integration Testing

- End-to-end flows
- Multi-tenant scenarios
- Distributed consistency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built as a demonstration of:
- Custom data structure implementation
- Distributed systems design
- High-performance async Python
- Property-based testing methodology
