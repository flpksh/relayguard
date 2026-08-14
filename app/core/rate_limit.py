import asyncio
from collections import deque
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class RateLimitRule:
    requests: int
    window_seconds: int


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        super().__init__("limite de requisições excedido")
        self.retry_after = retry_after


class InMemoryRateLimiter:
    """Limitador adequado ao processo único usado atualmente pelo RelayGuard."""

    def __init__(self, *, max_keys: int = 10_000) -> None:
        self._requests: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()
        self._max_keys = max_keys

    async def check(self, key: str, rule: RateLimitRule) -> None:
        now = monotonic()
        threshold = now - rule.window_seconds
        async with self._lock:
            values = self._requests.setdefault(key, deque())
            while values and values[0] <= threshold:
                values.popleft()
            if len(values) >= rule.requests:
                retry_after = max(1, int(rule.window_seconds - (now - values[0])) + 1)
                raise RateLimitExceeded(retry_after)
            values.append(now)
            self._discard_expired_keys(threshold)

    def _discard_expired_keys(self, threshold: float) -> None:
        if len(self._requests) <= self._max_keys:
            return
        expired = [
            key
            for key, values in self._requests.items()
            if not values or values[-1] <= threshold
        ]
        for key in expired:
            self._requests.pop(key, None)
        while len(self._requests) > self._max_keys:
            self._requests.pop(next(iter(self._requests)))

    def reset(self) -> None:
        self._requests.clear()


auth_rate_limiter = InMemoryRateLimiter()
