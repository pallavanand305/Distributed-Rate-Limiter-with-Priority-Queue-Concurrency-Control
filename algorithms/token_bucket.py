from typing import Dict
import time

class TokenBucket:
    def __init__(self, rate: float, burst_capacity: int):
        self.rate = rate
        self.burst_capacity = burst_capacity
        self.buckets: Dict[str, Dict] = {}
    
    def refill(self, tenant_id: str, current_time: float) -> None:
        if tenant_id not in self.buckets:
            self.buckets[tenant_id] = {'tokens': self.burst_capacity, 'last_refill': current_time}
            return
        
        bucket = self.buckets[tenant_id]
        elapsed = current_time - bucket['last_refill']
        if elapsed > 0:
            tokens_to_add = elapsed * self.rate
            bucket['tokens'] = min(self.burst_capacity, bucket['tokens'] + tokens_to_add)
            bucket['last_refill'] = current_time
    
    def consume(self, tenant_id: str, tokens: int) -> bool:
        if tenant_id not in self.buckets:
            return False
        
        bucket = self.buckets[tenant_id]
        if bucket['tokens'] >= tokens:
            bucket['tokens'] -= tokens
            return True
        return False
    
    def get_available_tokens(self, tenant_id: str) -> float:
        if tenant_id not in self.buckets:
            return 0.0
        return self.buckets[tenant_id]['tokens']
