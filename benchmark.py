"""
Performance Benchmarking Script for Distributed Rate Limiter

Measures:
- Throughput (requests/second)
- Latency (p50, p95, p99)
- Memory footprint per client
- Scalability across multiple nodes
"""

import asyncio
import time
import statistics
from typing import List
import psutil
import os

from storage.redis_simulator import RedisSimulator
from rate_limiter import RateLimiterEngine
from algorithms.priority_queue import PriorityQueue


class BenchmarkResults:
    """Container for benchmark results"""
    def __init__(self):
        self.throughput = 0
        self.latencies = []
        self.memory_per_client = 0
        self.p50 = 0
        self.p95 = 0
        self.p99 = 0


async def benchmark_throughput(num_requests: int = 10000, num_clients: int = 100) -> float:
    """
    Measure requests per second throughput.
    
    Args:
        num_requests: Total number of requests to send
        num_clients: Number of unique clients
        
    Returns:
        Requests per second
    """
    redis = RedisSimulator(latency_ms=1)  # Minimal latency for max throughput
    rate_limiter = RateLimiterEngine(redis)
    
    start_time = time.time()
    
    # Send requests
    tasks = []
    for i in range(num_requests):
        client_id = f"client_{i % num_clients}"
        tenant_id = "benchmark_tenant"
        timestamp = time.time()
        
        task = rate_limiter.check_and_increment(tenant_id, client_id, timestamp)
        tasks.append(task)
    
    # Execute all requests
    await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    throughput = num_requests / duration
    
    return throughput


async def benchmark_latency(duration_seconds: int = 10) -> dict:
    """
    Measure latency percentiles under sustained load.
    
    Args:
        duration_seconds: How long to run the benchmark
        
    Returns:
        Dictionary with p50, p95, p99 latencies in milliseconds
    """
    redis = RedisSimulator(latency_ms=50)  # Realistic latency
    rate_limiter = RateLimiterEngine(redis)
    
    latencies = []
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < duration_seconds:
        client_id = f"client_{request_count % 10}"
        tenant_id = "benchmark_tenant"
        
        req_start = time.time()
        await rate_limiter.check_and_increment(tenant_id, client_id, time.time())
        req_end = time.time()
        
        latency_ms = (req_end - req_start) * 1000
        latencies.append(latency_ms)
        request_count += 1
    
    # Calculate percentiles
    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    
    return {
        'p50': p50,
        'p95': p95,
        'p99': p99,
        'total_requests': request_count
    }


def benchmark_memory(num_clients: int = 1000) -> float:
    """
    Measure memory footprint per active client.
    
    Args:
        num_clients: Number of clients to simulate
        
    Returns:
        Memory per client in KB
    """
    process = psutil.Process(os.getpid())
    
    # Baseline memory
    baseline_memory = process.memory_info().rss / 1024  # KB
    
    # Create rate limiter with many clients
    redis = RedisSimulator(latency_ms=1)
    rate_limiter = RateLimiterEngine(redis)
    
    # Simulate activity for all clients
    async def simulate_clients():
        tasks = []
        for i in range(num_clients):
            client_id = f"client_{i}"
            tenant_id = "benchmark_tenant"
            task = rate_limiter.check_and_increment(tenant_id, client_id, time.time())
            tasks.append(task)
        await asyncio.gather(*tasks)
    
    asyncio.run(simulate_clients())
    
    # Measure memory after
    final_memory = process.memory_info().rss / 1024  # KB
    
    memory_increase = final_memory - baseline_memory
    memory_per_client = memory_increase / num_clients
    
    return memory_per_client


async def benchmark_scalability(num_nodes: int = 3) -> dict:
    """
    Test scalability with multiple API nodes.
    
    Args:
        num_nodes: Number of simulated API nodes
        
    Returns:
        Dictionary with throughput per node configuration
    """
    results = {}
    
    for nodes in range(1, num_nodes + 1):
        # Shared Redis across all nodes
        redis = RedisSimulator(latency_ms=50)
        
        # Create multiple rate limiters (simulating nodes)
        rate_limiters = [RateLimiterEngine(redis) for _ in range(nodes)]
        
        # Distribute requests across nodes
        num_requests = 1000
        start_time = time.time()
        
        tasks = []
        for i in range(num_requests):
            node_idx = i % nodes
            limiter = rate_limiters[node_idx]
            client_id = f"client_{i % 10}"
            tenant_id = "benchmark_tenant"
            
            task = limiter.check_and_increment(tenant_id, client_id, time.time())
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = num_requests / duration
        
        results[f'{nodes}_nodes'] = throughput
    
    return results


async def run_all_benchmarks():
    """Run all benchmarks and print results"""
    print("=" * 60)
    print("DISTRIBUTED RATE LIMITER - PERFORMANCE BENCHMARKS")
    print("=" * 60)
    print()
    
    # Throughput
    print("1. THROUGHPUT BENCHMARK")
    print("-" * 60)
    throughput = await benchmark_throughput(num_requests=10000, num_clients=100)
    print(f"   Throughput: {throughput:,.0f} requests/second")
    print(f"   Target: >10,000 req/s")
    print(f"   Status: {'✅ PASS' if throughput > 10000 else '❌ FAIL'}")
    print()
    
    # Latency
    print("2. LATENCY BENCHMARK")
    print("-" * 60)
    latency_results = await benchmark_latency(duration_seconds=5)
    print(f"   p50 latency: {latency_results['p50']:.2f} ms")
    print(f"   p95 latency: {latency_results['p95']:.2f} ms")
    print(f"   p99 latency: {latency_results['p99']:.2f} ms")
    print(f"   Total requests: {latency_results['total_requests']:,}")
    print(f"   Target: p95 <5ms")
    print(f"   Status: {'✅ PASS' if latency_results['p95'] < 5 else '❌ FAIL'}")
    print()
    
    # Memory
    print("3. MEMORY FOOTPRINT BENCHMARK")
    print("-" * 60)
    memory_per_client = benchmark_memory(num_clients=1000)
    print(f"   Memory per client: {memory_per_client:.2f} KB")
    print(f"   Target: <1 KB per client")
    print(f"   Status: {'✅ PASS' if memory_per_client < 1 else '❌ FAIL'}")
    print()
    
    # Scalability
    print("4. SCALABILITY BENCHMARK")
    print("-" * 60)
    scalability_results = await benchmark_scalability(num_nodes=3)
    for config, throughput in scalability_results.items():
        print(f"   {config}: {throughput:,.0f} req/s")
    print()
    
    print("=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
