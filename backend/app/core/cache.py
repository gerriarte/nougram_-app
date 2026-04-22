"""
Simple in-memory cache with TTL (Time To Live) support
For production, consider using Redis or Memcached
"""

from datetime import datetime, timedelta
from threading import Lock
from typing import Any


class CacheEntry:
    """Cache entry with expiration time"""

    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.utcnow() > self.expires_at


class SimpleCache:
    """
    Thread-safe in-memory cache with TTL

    Usage:
        cache = SimpleCache()
        cache.set("key", "value", ttl_seconds=60)
        value = cache.get("key")
        cache.invalidate("key")
        cache.clear()
    """

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                return None

            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl_seconds)

    def invalidate(self, key: str) -> None:
        """
        Remove key from cache

        Args:
            key: Cache key to remove
        """
        with self._lock:
            self._cache.pop(key, None)

    def invalidate_pattern(self, pattern: str) -> None:
        """
        Remove all keys matching pattern

        Args:
            pattern: Pattern to match (simple substring match)
        """
        with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> None:
        """Remove all expired entries (useful for periodic cleanup)"""
        with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]


# Global cache instance
_cache_instance: SimpleCache | None = None


def get_cache() -> SimpleCache:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleCache()
    return _cache_instance
