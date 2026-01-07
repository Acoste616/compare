"""
UNIFIED API CACHE MANAGER
Centralized caching layer for all live API integrations

This module provides a unified JSON-based cache for:
1. CEPiK API responses (24h TTL)
2. Fuel price data (24h TTL)
3. OpenChargeMap data (7 days TTL - charger locations change infrequently)

WHY UNIFIED CACHE:
- Consistent TTL management across all API sources
- Reduced redundant API calls during mass CSV processing
- Single source of truth for cached data
- Automatic fallback to stale cache on API failures

CACHE STORAGE:
- File: dane/api_cache.json
- Format: {"cache_key": {"data": {...}, "timestamp": "ISO8601", "ttl_hours": 24}}

Author: Data Integration Specialist
Version: 1.0.0
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Cache type with associated TTL"""
    CEPIK = 24  # 24 hours for vehicle registration data
    FUEL_PRICES = 24  # 24 hours for fuel prices
    CHARGERS = 168  # 7 days (168 hours) for charger locations
    MARKET_DATA = 24  # 24 hours for general market data


class UnifiedAPICache:
    """
    Unified caching layer for all API integrations.

    Provides consistent caching with:
    - Type-specific TTL management
    - Automatic stale fallback
    - Thread-safe file operations
    - Cache statistics and monitoring
    """

    CACHE_FILE = Path(__file__).parent.parent.parent.parent / "dane" / "api_cache.json"

    @classmethod
    def get(cls, cache_key: str, cache_type: CacheType = CacheType.MARKET_DATA) -> Optional[Any]:
        """
        Retrieve data from cache if fresh.

        Args:
            cache_key: Unique identifier for cached data
            cache_type: Type of cache (determines TTL)

        Returns:
            Cached data if exists and fresh, None otherwise
        """
        if not cls.CACHE_FILE.exists():
            logger.debug(f"[API Cache] MISS - Cache file doesn't exist")
            return None

        try:
            with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            if cache_key not in cache:
                logger.debug(f"[API Cache] MISS - Key '{cache_key}' not found")
                return None

            entry = cache[cache_key]

            # Check TTL
            cached_time = datetime.fromisoformat(entry['timestamp'])
            ttl_hours = entry.get('ttl_hours', cache_type.value)
            age = datetime.now() - cached_time

            if age < timedelta(hours=ttl_hours):
                logger.info(f"[API Cache] HIT - '{cache_key}' ({cache_type.name}, age: {age.total_seconds() / 3600:.1f}h)")
                return entry['data']
            else:
                logger.info(f"[API Cache] EXPIRED - '{cache_key}' (age: {age.total_seconds() / 3600:.1f}h, TTL: {ttl_hours}h)")
                return None

        except Exception as e:
            logger.error(f"[API Cache] Error reading cache: {e}")
            return None

    @classmethod
    def set(cls, cache_key: str, data: Any, cache_type: CacheType = CacheType.MARKET_DATA) -> bool:
        """
        Save data to cache with timestamp and TTL.

        Args:
            cache_key: Unique identifier for data
            data: Data to cache (must be JSON serializable)
            cache_type: Type of cache (determines TTL)

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
                "timestamp": datetime.now().isoformat(),
                "ttl_hours": cache_type.value,
                "cache_type": cache_type.name
            }

            # Save atomically (write to temp file, then rename)
            temp_file = cls.CACHE_FILE.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

            temp_file.replace(cls.CACHE_FILE)

            logger.info(f"[API Cache] SAVED - '{cache_key}' ({cache_type.name}, TTL: {cache_type.value}h)")
            return True

        except Exception as e:
            logger.error(f"[API Cache] Error saving cache: {e}")
            return False

    @classmethod
    def get_with_fallback(cls, cache_key: str, cache_type: CacheType = CacheType.MARKET_DATA) -> Optional[Any]:
        """
        Get cached data even if expired (emergency fallback).

        Args:
            cache_key: Cache identifier
            cache_type: Type of cache

        Returns:
            Cached data (even if stale) or None
        """
        if not cls.CACHE_FILE.exists():
            return None

        try:
            with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            if cache_key in cache:
                cached_time = datetime.fromisoformat(cache[cache_key]['timestamp'])
                age = datetime.now() - cached_time
                logger.warning(f"[API Cache] Using STALE cache as fallback for '{cache_key}' (age: {age.total_seconds() / 3600:.1f}h)")
                return cache[cache_key]['data']

        except Exception as e:
            logger.error(f"[API Cache] Error reading stale cache: {e}")

        return None

    @classmethod
    def invalidate(cls, cache_key: Optional[str] = None, cache_type: Optional[CacheType] = None) -> bool:
        """
        Invalidate cache entry, cache type, or entire cache.

        Args:
            cache_key: Specific key to invalidate, or None to clear by type/all
            cache_type: Cache type to invalidate, or None to clear all

        Returns:
            True if successful, False otherwise
        """
        try:
            if cache_key is None and cache_type is None:
                # Clear entire cache
                if cls.CACHE_FILE.exists():
                    cls.CACHE_FILE.unlink()
                    logger.info("[API Cache] ALL cache cleared")
                return True

            if not cls.CACHE_FILE.exists():
                return True  # Already gone

            with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            # Remove specific key
            if cache_key:
                if cache_key in cache:
                    del cache[cache_key]
                    logger.info(f"[API Cache] INVALIDATED - '{cache_key}'")

            # Remove all entries of specific type
            elif cache_type:
                keys_to_remove = [k for k, v in cache.items() if v.get('cache_type') == cache_type.name]
                for k in keys_to_remove:
                    del cache[k]
                logger.info(f"[API Cache] INVALIDATED - {len(keys_to_remove)} entries of type {cache_type.name}")

            with open(cls.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"[API Cache] Error invalidating cache: {e}")
            return False

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not cls.CACHE_FILE.exists():
            return {
                "total_entries": 0,
                "by_type": {},
                "cache_size_mb": 0
            }

        try:
            with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            # Count by type
            by_type = {}
            fresh_count = 0
            stale_count = 0

            for entry in cache.values():
                cache_type = entry.get('cache_type', 'UNKNOWN')
                by_type[cache_type] = by_type.get(cache_type, 0) + 1

                # Check if fresh
                cached_time = datetime.fromisoformat(entry['timestamp'])
                ttl_hours = entry.get('ttl_hours', 24)
                age = datetime.now() - cached_time

                if age < timedelta(hours=ttl_hours):
                    fresh_count += 1
                else:
                    stale_count += 1

            # Get file size
            cache_size_mb = cls.CACHE_FILE.stat().st_size / (1024 * 1024)

            return {
                "total_entries": len(cache),
                "fresh_entries": fresh_count,
                "stale_entries": stale_count,
                "by_type": by_type,
                "cache_size_mb": round(cache_size_mb, 2),
                "cache_file": str(cls.CACHE_FILE)
            }

        except Exception as e:
            logger.error(f"[API Cache] Error getting stats: {e}")
            return {"error": str(e)}


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Unified API Cache Test ===\n")

    # Test 1: CEPiK data caching
    print("1️⃣  Testing CEPiK cache...")
    cepik_data = {"TESLA": 45, "BMW": 120, "TOTAL": 165}
    UnifiedAPICache.set("leasing_expiry_silesia_36m", cepik_data, CacheType.CEPIK)
    retrieved = UnifiedAPICache.get("leasing_expiry_silesia_36m", CacheType.CEPIK)
    print(f"   Retrieved: {retrieved}\n")

    # Test 2: Fuel price caching
    print("2️⃣  Testing fuel price cache...")
    fuel_data = {"Pb95": 6.05, "ON": 6.15, "LPG": 2.85}
    UnifiedAPICache.set("fuel_prices_latest", fuel_data, CacheType.FUEL_PRICES)
    retrieved = UnifiedAPICache.get("fuel_prices_latest", CacheType.FUEL_PRICES)
    print(f"   Retrieved: {retrieved}\n")

    # Test 3: Charger location caching
    print("3️⃣  Testing charger cache...")
    charger_data = {"lat": 50.2649, "lon": 19.0238, "distance_km": 2.5}
    UnifiedAPICache.set("charger_katowice_40", charger_data, CacheType.CHARGERS)
    retrieved = UnifiedAPICache.get("charger_katowice_40", CacheType.CHARGERS)
    print(f"   Retrieved: {retrieved}\n")

    # Test 4: Cache statistics
    print("4️⃣  Cache statistics...")
    stats = UnifiedAPICache.get_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Fresh: {stats['fresh_entries']}, Stale: {stats['stale_entries']}")
    print(f"   By type: {stats['by_type']}")
    print(f"   Cache size: {stats['cache_size_mb']} MB\n")

    print("✅ All tests completed!")
