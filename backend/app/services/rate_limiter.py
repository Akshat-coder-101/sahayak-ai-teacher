import time
import threading
from typing import Dict, List, Callable
from fastapi import Request, HTTPException, status

class SlidingWindowRateLimiter:
    """
    Thread-safe, in-memory sliding window rate limiter.
    Tracks request timestamps per client identifier (IP / X-Forwarded-For).
    """
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._history: Dict[str, List[float]] = {}

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = getattr(request, "client", None)
        return getattr(client, "host", "127.0.0.1") if client else "127.0.0.1"

    def check(self, request: Request) -> None:
        client_ip = self._get_client_ip(request)
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # Clean timestamps older than window
            timestamps = self._history.get(client_ip, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]
            
            if len(valid_timestamps) >= self.max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(earliest + self.window_seconds - now))
                self._history[client_ip] = valid_timestamps
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds}s.",
                    headers={"Retry-After": str(retry_after)}
                )

            valid_timestamps.append(now)
            self._history[client_ip] = valid_timestamps

    def reset(self) -> None:
        """Utility for test suites to clear limits."""
        with self._lock:
            self._history.clear()

def create_rate_limiter(max_requests: int, window_seconds: int = 60) -> Callable[[Request], None]:
    """Factory creating a FastAPI dependency enforcing rate limits."""
    limiter = SlidingWindowRateLimiter(max_requests, window_seconds)
    def dependency(request: Request):
        limiter.check(request)
    dependency.limiter = limiter  # type: ignore[attr-defined]
    return dependency

# Standard rate limiters for critical sensitive endpoints
auth_rate_limiter = create_rate_limiter(max_requests=15, window_seconds=60)
sandbox_rate_limiter = create_rate_limiter(max_requests=25, window_seconds=60)
