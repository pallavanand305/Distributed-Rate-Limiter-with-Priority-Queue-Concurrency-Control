import asyncio
from typing import Dict, Any, Optional

class RedisSimulator:
    def __init__(self, latency_ms: float = 0.0):
        self.latency_ms = latency_ms
        self.data: Dict[str, Any] = {}
        self.lock = asyncio.Lock()
        self.expiry: Dict[str, float] = {}
    
    async def _simulate_latency(self):
        if self.latency_ms > 0:
            await asyncio.sleep(self.latency_ms / 1000.0)
    
    async def get(self, key: str) -> Optional[Any]:
        await self._simulate_latency()
        return self.data.get(key)
    
    async def set(self, key: str, value: Any) -> None:
        await self._simulate_latency()
        self.data[key] = value
    
    async def incr(self, key: str) -> int:
        await self._simulate_latency()
        async with self.lock:
            current = self.data.get(key, 0)
            if isinstance(current, str):
                current = int(current)
            self.data[key] = current + 1
            return self.data[key]
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        await self._simulate_latency()
        hash_data = self.data.get(key, {})
        if isinstance(hash_data, dict):
            return hash_data.get(field)
        return None
    
    async def hset(self, key: str, field: str, value: Any) -> None:
        await self._simulate_latency()
        if key not in self.data or not isinstance(self.data[key], dict):
            self.data[key] = {}
        self.data[key][field] = value
    
    async def expire(self, key: str, seconds: int) -> None:
        await self._simulate_latency()
        self.expiry[key] = asyncio.get_event_loop().time() + seconds
        asyncio.create_task(self._cleanup_expired(key, seconds))
    
    async def _cleanup_expired(self, key: str, seconds: int):
        await asyncio.sleep(seconds)
        if key in self.expiry and asyncio.get_event_loop().time() >= self.expiry[key]:
            self.data.pop(key, None)
            self.expiry.pop(key, None)
