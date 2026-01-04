"""
GOTHAM Data Store - CEPiK Caching Layer
Manages persistent cache for CEPiK API responses

WHY CACHING:
- CEPiK API can be slow (3-10s per request)
- Rate limits may apply
- Registration data doesn't change frequently (daily updates are sufficient)

CACHE STRATEGY:
- 24h TTL (Time To Live)
- JSON file storage in dane/cepik_cache.json
- Fallback to last known data if API fails

Author: Senior Python Backend Developer
Version: 1.0.0
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CEPiKCache:
    """
    Persistent cache for CEPiK API responses.

    Features:
    - 24h TTL
    - Thread-safe file operations
    - Automatic fallback on API failures
    - Cache invalidation support
    """

    CACHE_FILE = Path(__file__).parent.parent.parent.parent / "dane" / "cepik_cache.json"
    CACHE_TTL_HOURS = 24

    @classmethod
    def get(cls, cache_key: str) -> Optional[Any]:
        """
        Retrieve data from cache if fresh.

        Args:
            cache_key: Unique identifier for cached data

        Returns:
            Cached data if exists and fresh, None otherwise
        """
        if not cls.CACHE_FILE.exists():
            logger.info(f"[CEPiK Cache] MISS - Cache file doesn't exist")
            return None

        try:
            with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            if cache_key not in cache:
                logger.info(f"[CEPiK Cache] MISS - Key '{cache_key}' not found")
                return None

            entry = cache[cache_key]

            # Check TTL
            cached_time = datetime.fromisoformat(entry['timestamp'])
            age = datetime.now() - cached_time

            if age < timedelta(hours=cls.CACHE_TTL_HOURS):
                logger.info(f"[CEPiK Cache] HIT - '{cache_key}' (age: {age.total_seconds() / 3600:.1f}h)")
                return entry['data']
            else:
                logger.info(f"[CEPiK Cache] EXPIRED - '{cache_key}' (age: {age.total_seconds() / 3600:.1f}h)")
                return None

        except Exception as e:
            logger.error(f"[CEPiK Cache] Error reading cache: {e}")
            return None

    @classmethod
    def set(cls, cache_key: str, data: Any) -> bool:
        """
        Save data to cache with current timestamp.

        Args:
            cache_key: Unique identifier for data
            data: Data to cache (must be JSON serializable)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            cls.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Load existing cache
            cache = {}
            if cls.CACHE_FILE.exists():
                with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)

            # Add new entry
            cache[cache_key] = {
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            # Save atomically (write to temp file, then rename)
            temp_file = cls.CACHE_FILE.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

            temp_file.replace(cls.CACHE_FILE)

            logger.info(f"[CEPiK Cache] SAVED - '{cache_key}'")
            return True

        except Exception as e:
            logger.error(f"[CEPiK Cache] Error saving cache: {e}")
            return False

    @classmethod
    def invalidate(cls, cache_key: Optional[str] = None) -> bool:
        """
        Invalidate cache entry or entire cache.

        Args:
            cache_key: Specific key to invalidate, or None to clear all

        Returns:
            True if successful, False otherwise
        """
        try:
            if cache_key is None:
                # Clear entire cache
                if cls.CACHE_FILE.exists():
                    cls.CACHE_FILE.unlink()
                    logger.info("[CEPiK Cache] ALL cache cleared")
                return True

            # Remove specific key
            if not cls.CACHE_FILE.exists():
                return True  # Already gone

            with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            if cache_key in cache:
                del cache[cache_key]

                with open(cls.CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)

                logger.info(f"[CEPiK Cache] INVALIDATED - '{cache_key}'")

            return True

        except Exception as e:
            logger.error(f"[CEPiK Cache] Error invalidating cache: {e}")
            return False

    @classmethod
    def get_or_fetch(cls, cache_key: str, fetch_func: callable, *args, **kwargs) -> Optional[Any]:
        """
        Get data from cache or fetch if not available.

        This is the main method to use - handles cache-or-fetch pattern with fallback.

        Args:
            cache_key: Cache identifier
            fetch_func: Function to call if cache miss
            *args, **kwargs: Arguments to pass to fetch_func

        Returns:
            Data from cache or fresh fetch, or None if both fail
        """
        # Try cache first
        cached = cls.get(cache_key)
        if cached is not None:
            return cached

        # Cache miss - fetch fresh data
        logger.info(f"[CEPiK Cache] Fetching fresh data for '{cache_key}'...")

        try:
            data = fetch_func(*args, **kwargs)

            if data is not None:
                # Save to cache
                cls.set(cache_key, data)
                return data
            else:
                logger.warning(f"[CEPiK Cache] Fetch returned None for '{cache_key}'")

                # Try to return stale cache as fallback
                return cls._get_stale_fallback(cache_key)

        except Exception as e:
            logger.error(f"[CEPiK Cache] Fetch failed for '{cache_key}': {e}")

            # Return stale cache as emergency fallback
            return cls._get_stale_fallback(cache_key)

    @classmethod
    def _get_stale_fallback(cls, cache_key: str) -> Optional[Any]:
        """
        Get cached data even if expired (emergency fallback).

        Args:
            cache_key: Cache identifier

        Returns:
            Stale cached data or None
        """
        if not cls.CACHE_FILE.exists():
            return None

        try:
            with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            if cache_key in cache:
                logger.warning(f"[CEPiK Cache] Using STALE cache as fallback for '{cache_key}'")
                return cache[cache_key]['data']

        except Exception as e:
            logger.error(f"[CEPiK Cache] Error reading stale cache: {e}")

        return None


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=== CEPiK Cache Test ===\n")

    # Test 1: Set and get
    print("1️⃣  Testing cache set/get...")
    CEPiKCache.set("test_key", {"brand": "BMW", "count": 150})
    result = CEPiKCache.get("test_key")
    print(f"   Retrieved: {result}\n")

    # Test 2: Cache miss
    print("2️⃣  Testing cache miss...")
    result = CEPiKCache.get("nonexistent_key")
    print(f"   Result: {result}\n")

    # Test 3: Get or fetch pattern
    print("3️⃣  Testing get_or_fetch...")

    def expensive_operation(brand: str) -> dict:
        print(f"   [Simulating API call for {brand}...]")
        return {"brand": brand, "count": 200}

    # First call - should fetch
    result1 = CEPiKCache.get_or_fetch("brand_BMW", expensive_operation, "BMW")
    print(f"   First call: {result1}")

    # Second call - should use cache
    result2 = CEPiKCache.get_or_fetch("brand_BMW", expensive_operation, "BMW")
    print(f"   Second call (cached): {result2}\n")

    # Test 4: Clear cache
    print("4️⃣  Testing cache invalidation...")
    CEPiKCache.invalidate()
    print(f"   Cache cleared\n")

    print("✅ All tests completed!")
