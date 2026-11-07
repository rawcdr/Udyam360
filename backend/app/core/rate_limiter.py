"""Sliding-window rate limiter and security lockout coordinator for Udyam360."""

import time
import threading
from typing import Dict, List, Optional, Tuple


class RateLimiter:
    """Thread-safe sliding-window in-memory rate limiter with lockout support."""

    def __init__(self):
        self._lock = threading.Lock()
        # key -> list of float timestamps
        self._requests: Dict[str, List[float]] = {}
        # key -> timestamp of last event (for cooldowns)
        self._last_event: Dict[str, float] = {}
        # key -> lockout expiry timestamp
        self._lockouts: Dict[str, float] = {}

    def check_and_record(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """Checks if a request is permitted under the sliding window limit and records it.

        Returns:
            (allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        with self._lock:
            # Check active lockout
            if key in self._lockouts:
                remaining = int(self._lockouts[key] - now)
                if remaining > 0:
                    return False, remaining
                del self._lockouts[key]

            timestamps = self._requests.get(key, [])
            cutoff = now - window_seconds
            # Evict timestamps older than sliding window
            timestamps = [ts for ts in timestamps if ts > cutoff]

            if len(timestamps) >= max_requests:
                earliest = timestamps[0]
                retry_after = max(1, int(earliest + window_seconds - now))
                self._requests[key] = timestamps
                return False, retry_after

            timestamps.append(now)
            self._requests[key] = timestamps
            return True, 0

    def check_cooldown(self, key: str, cooldown_seconds: int) -> Optional[int]:
        """Checks if the key is currently within a mandatory cooldown period.
        
        Returns remaining cooldown seconds, or None if cooldown has passed.
        """
        now = time.time()
        with self._lock:
            last = self._last_event.get(key)
            if last is not None:
                diff = now - last
                if diff < cooldown_seconds:
                    return max(1, int(cooldown_seconds - diff))
            return None

    def record_cooldown(self, key: str) -> None:
        """Records an event timestamp for cooldown checking."""
        now = time.time()
        with self._lock:
            self._last_event[key] = now

    def set_lockout(self, key: str, duration_seconds: int) -> None:
        """Enforces a temporary lockout for suspicious or repeatedly failed attempts."""
        now = time.time()
        with self._lock:
            self._lockouts[key] = now + duration_seconds

    def check_lockout(self, key: str) -> Optional[int]:
        """Returns remaining lockout seconds or None."""
        now = time.time()
        with self._lock:
            if key in self._lockouts:
                remaining = int(self._lockouts[key] - now)
                if remaining > 0:
                    return remaining
                del self._lockouts[key]
            return None

    def clear(self) -> None:
        """Resets all tracking (used primarily by automated test fixtures)."""
        with self._lock:
            self._requests.clear()
            self._last_event.clear()
            self._lockouts.clear()


rate_limiter = RateLimiter()

