import pytest

from app.core.rate_limit import InMemoryRateLimiter, RateLimitExceeded, RateLimitRule


async def test_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter()
    rule = RateLimitRule(requests=2, window_seconds=60)

    await limiter.check("login:127.0.0.1", rule)
    await limiter.check("login:127.0.0.1", rule)

    with pytest.raises(RateLimitExceeded) as error:
        await limiter.check("login:127.0.0.1", rule)

    assert error.value.retry_after > 0


async def test_rate_limiter_reset() -> None:
    limiter = InMemoryRateLimiter()
    rule = RateLimitRule(requests=1, window_seconds=60)
    await limiter.check("cadastro:127.0.0.1", rule)

    limiter.reset()

    await limiter.check("cadastro:127.0.0.1", rule)
