"""
Sliding Window Counter Rate Limiter

Implements a precise sliding window algorithm with O(1) space complexity per client.
Uses two buckets (current and previous) to calculate weighted request counts.
"""

import time
from typing import Optional, Tuple


class SlidingWindowCounter:
    """
    Sliding window counter for precise rate limiting.
    
    Uses two time buckets to track requests:
    - Current window: Active time bucket
    - Previous window: Previous time bucket for overlap calculation
    
    Space Complexity: O(1) per client (only 2 buckets)
    Time Complexity: O(1) for check and increment operations
    """
    
    def __init__(self, window_size_seconds: int, max_requests: int, redis_client=None):
        """
        Initialize sliding window counter.
        
        Args:
            window_size_seconds: Size of the sliding window in seconds
            max_requests: Maximum requests allowed within the window
            redis_client: Redis client for distributed state (optional)
        """
        self.window_size = window_size_seconds
        self.max_requests = max_requests
        self.redis = redis_client
        
    async def check_rate_limit(
        self, 
        client_id: str, 
        timestamp: Optional[float] = None
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.
        
        Algorithm:
        1. Calculate current and previous window boundaries
        2. Retrieve counts from Redis
        3. Calculate weighted count based on sliding window overlap
        4. Compare against max_requests limit
        
        Args:
            client_id: Unique identifier for the client
            timestamp: Current timestamp (defaults to time.time())
            
        Returns:
            Tuple of (allowed: bool, remaining: int)
            - allowed: True if request is within limits
            - remaining: Number of requests remaining in quota
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Calculate window boundaries
        current_window_start = int(timestamp // self.window_size) * self.window_size
        previous_window_start = current_window_start - self.window_size
        
        # Get counts from Redis
        current_key = f"rate_limit:{client_id}:current:{current_window_start}"
        previous_key = f"rate_limit:{client_id}:previous:{previous_window_start}"
        
        if self.redis:
            current_count_str = await self.redis.get(current_key)
            previous_count_str = await self.redis.get(previous_key)
            current_count = int(current_count_str) if current_count_str else 0
            previous_count = int(previous_count_str) if previous_count_str else 0
        else:
            # Fallback for testing without Redis
            current_count = 0
            previous_count = 0
            
        # Calculate weighted count using sliding window formula
        # This includes the current request that would be added
        time_in_current_window = timestamp - current_window_start
        overlap_ratio = (self.window_size - time_in_current_window) / self.window_size
        weighted_count = previous_count * overlap_ratio + current_count + 1
        
        # Check if within limits (including the new request)
        allowed = weighted_count <= self.max_requests
        remaining = max(0, int(self.max_requests - (weighted_count - 1)))
        
        return allowed, remaining
    
    async def increment_counter(
        self, 
        client_id: str, 
        timestamp: Optional[float] = None
    ) -> int:
        """
        Increment request counter for client using atomic Redis operation.
        
        Args:
            client_id: Unique identifier for the client
            timestamp: Current timestamp (defaults to time.time())
            
        Returns:
            New counter value after increment
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Calculate current window
        current_window_start = int(timestamp // self.window_size) * self.window_size
        current_key = f"rate_limit:{client_id}:current:{current_window_start}"
        
        if self.redis:
            # Atomic increment
            new_count = await self.redis.incr(current_key)
            # Set expiration to window_size * 2 to keep previous window
            await self.redis.expire(current_key, self.window_size * 2)
            return new_count
        else:
            # Fallback for testing without Redis
            return 1
    
    def calculate_reset_time(self, timestamp: Optional[float] = None) -> float:
        """
        Calculate when the rate limit will reset.
        
        Args:
            timestamp: Current timestamp (defaults to time.time())
            
        Returns:
            Unix timestamp when the window resets
        """
        if timestamp is None:
            timestamp = time.time()
            
        current_window_start = int(timestamp // self.window_size) * self.window_size
        return current_window_start + self.window_size
