"""Token bucket rate limiter for Airtable API.

Airtable has a rate limit of 5 requests per second per base.
This module provides both sync and async rate limiters.

Usage:
    from xwander_airtable.rate_limiter import RateLimiter, AsyncRateLimiter

    # Sync usage
    limiter = RateLimiter(base_id="app123")
    with limiter:
        # Make API request
        pass

    # Async usage
    limiter = AsyncRateLimiter(base_id="app123")
    async with limiter:
        # Make async API request
        pass

    # Decorator usage
    @limiter.limit
    def make_request():
        pass
"""

import time
import threading
import asyncio
from typing import Dict, Optional, Callable, TypeVar, Any
from functools import wraps
from contextlib import contextmanager, asynccontextmanager

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


class RateLimiter:
    """Token bucket rate limiter for synchronous requests.

    Implements a per-base rate limiter with:
    - 5 requests per second default (Airtable limit)
    - Thread-safe token bucket algorithm
    - Automatic waiting when limit reached
    - Shared limiters per base_id
    """

    # Shared limiters per base
    _instances: Dict[str, "RateLimiter"] = {}
    _lock = threading.Lock()

    def __new__(cls, base_id: str, rate: float = 5.0, burst: int = 5) -> "RateLimiter":
        """Return existing limiter for base_id or create new one."""
        with cls._lock:
            if base_id not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[base_id] = instance
            return cls._instances[base_id]

    def __init__(self, base_id: str, rate: float = 5.0, burst: int = 5):
        """Initialize rate limiter.

        Args:
            base_id: Airtable base ID (limiters are shared per base)
            rate: Requests per second (default: 5)
            burst: Maximum burst capacity (default: 5)
        """
        if getattr(self, "_initialized", False):
            return

        self.base_id = base_id
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._lock = threading.Lock()
        self._initialized = True

    def _refill(self) -> None:
        """Refill tokens based on time elapsed."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_update = now

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire a token, waiting if necessary.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if token acquired, False if timeout
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return True

                # Calculate wait time for next token
                wait_time = (1 - self._tokens) / self.rate

            # Check timeout
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            time.sleep(wait_time)

    def __enter__(self) -> "RateLimiter":
        """Context manager entry - acquires token."""
        self.acquire()
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit."""
        pass

    def limit(self, func: F) -> F:
        """Decorator to rate limit a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)
        return wrapper  # type: ignore

    @classmethod
    def get_limiter(cls, base_id: str) -> "RateLimiter":
        """Get or create a limiter for the given base."""
        return cls(base_id)

    @classmethod
    def clear_all(cls) -> None:
        """Clear all cached limiters (for testing)."""
        with cls._lock:
            cls._instances.clear()


class AsyncRateLimiter:
    """Async token bucket rate limiter for Airtable API.

    Same algorithm as RateLimiter but for async/await usage.
    """

    # Shared limiters per base
    _instances: Dict[str, "AsyncRateLimiter"] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get_limiter(cls, base_id: str, rate: float = 5.0, burst: int = 5) -> "AsyncRateLimiter":
        """Get or create an async limiter for the given base."""
        async with cls._lock:
            if base_id not in cls._instances:
                cls._instances[base_id] = cls(base_id, rate, burst)
            return cls._instances[base_id]

    def __init__(self, base_id: str, rate: float = 5.0, burst: int = 5):
        """Initialize async rate limiter."""
        self.base_id = base_id
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on time elapsed."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_update = now

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire a token, waiting if necessary.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if token acquired, False if timeout
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return True

                # Calculate wait time for next token
                wait_time = (1 - self._tokens) / self.rate

            # Check timeout
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            await asyncio.sleep(wait_time)

    async def __aenter__(self) -> "AsyncRateLimiter":
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        pass

    def limit(self, func: F) -> F:
        """Decorator to rate limit an async function."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await self.acquire()
            return await func(*args, **kwargs)
        return wrapper  # type: ignore

    @classmethod
    async def clear_all(cls) -> None:
        """Clear all cached limiters (for testing)."""
        async with cls._lock:
            cls._instances.clear()


@contextmanager
def rate_limited(base_id: str):
    """Context manager for rate-limited operations.

    Usage:
        with rate_limited("app123"):
            # Make API request
            pass
    """
    limiter = RateLimiter.get_limiter(base_id)
    with limiter:
        yield limiter


@asynccontextmanager
async def async_rate_limited(base_id: str):
    """Async context manager for rate-limited operations.

    Usage:
        async with async_rate_limited("app123"):
            # Make async API request
            pass
    """
    limiter = await AsyncRateLimiter.get_limiter(base_id)
    async with limiter:
        yield limiter
