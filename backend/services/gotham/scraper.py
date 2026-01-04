"""
GOTHAM LIVE FUEL PRICE SCRAPER
Pobiera aktualne ceny paliw ze stron internetowych dla polskiego rynku.

Author: Lead Backend Developer
Version: 1.0.0
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class FuelPriceScraper:
    """
    Scraper dla aktualnych cen paliw w Polsce.

    Źródła:
    - autocentrum.pl (primary)
    - e-petrol.pl (fallback)
    """

    # Safe defaults (fallback gdy scraping nie działa)
    SAFE_DEFAULTS = {
        "Pb95": 6.05,
        "ON": 6.15,
        "LPG": 2.85
    }

    # Data file path
    DATA_FILE = Path(__file__).parent.parent.parent.parent / "dane" / "gotham_market_data.json"

    @classmethod
    def scrape_autocentrum(cls) -> Optional[Dict[str, float]]:
        """
        Scrape fuel prices from autocentrum.pl

        Returns:
            Dict with fuel prices or None if failed
        """
        try:
            url = "https://www.autocentrum.pl/paliwa/ceny-paliw/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse prices (structure may vary - adjust selectors as needed)
            prices = {}

            # Example parsing logic (adjust based on actual HTML structure)
            # Looking for price tables or divs containing fuel type and price
            price_containers = soup.find_all('div', class_='fuel-price') or soup.find_all('tr')

            for container in price_containers:
                text = container.get_text().strip()

                # Try to extract Pb95
                if 'Pb95' in text or 'E95' in text or '95' in text:
                    price = cls._extract_price(text)
                    if price:
                        prices['Pb95'] = price

                # Try to extract Diesel (ON)
                if 'ON' in text or 'Diesel' in text or 'diesel' in text.lower():
                    price = cls._extract_price(text)
                    if price:
                        prices['ON'] = price

                # Try to extract LPG
                if 'LPG' in text or 'Gaz' in text:
                    price = cls._extract_price(text)
                    if price:
                        prices['LPG'] = price

            if len(prices) >= 2:  # At least 2 fuel types found
                logger.info(f"[SCRAPER] Autocentrum.pl - Success: {prices}")
                return prices
            else:
                logger.warning(f"[SCRAPER] Autocentrum.pl - Insufficient data: {prices}")
                return None

        except Exception as e:
            logger.error(f"[SCRAPER] Autocentrum.pl failed: {e}")
            return None

    @classmethod
    def scrape_e_petrol(cls) -> Optional[Dict[str, float]]:
        """
        Scrape fuel prices from e-petrol.pl (fallback source)

        Returns:
            Dict with fuel prices or None if failed
        """
        try:
            url = "https://e-petrol.pl/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            prices = {}

            # Parse e-petrol structure
            price_elements = soup.find_all('div', class_='price') or soup.find_all('span', class_='value')

            for elem in price_elements:
                text = elem.get_text().strip()
                parent_text = elem.parent.get_text() if elem.parent else ""

                if '95' in parent_text or 'Pb95' in parent_text:
                    price = cls._extract_price(text)
                    if price:
                        prices['Pb95'] = price

                if 'Diesel' in parent_text or 'ON' in parent_text:
                    price = cls._extract_price(text)
                    if price:
                        prices['ON'] = price

                if 'LPG' in parent_text or 'Gaz' in parent_text:
                    price = cls._extract_price(text)
                    if price:
                        prices['LPG'] = price

            if len(prices) >= 2:
                logger.info(f"[SCRAPER] E-petrol.pl - Success: {prices}")
                return prices
            else:
                logger.warning(f"[SCRAPER] E-petrol.pl - Insufficient data: {prices}")
                return None

        except Exception as e:
            logger.error(f"[SCRAPER] E-petrol.pl failed: {e}")
            return None

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        """
        Extract price from text string.

        Examples:
        - "6.05 zł" -> 6.05
        - "6,15" -> 6.15
        - "Pb95: 6.05 PLN" -> 6.05
        """
        import re

        # Remove non-numeric chars except comma and dot
        # Look for patterns like: 6.05, 6,05, or 605 (in grosz)
        match = re.search(r'(\d+)[,.](\d{2})', text)
        if match:
            return float(f"{match.group(1)}.{match.group(2)}")

        return None

    @classmethod
    def get_live_prices(cls) -> Dict[str, float]:
        """
        Get live fuel prices with fallback chain.

        Strategy:
        1. Try autocentrum.pl
        2. Try e-petrol.pl
        3. Use safe defaults

        Returns:
            Dict with fuel prices (always returns valid data)
        """
        logger.info("[SCRAPER] Fetching live fuel prices...")

        # Try primary source
        prices = cls.scrape_autocentrum()
        if prices:
            return cls._normalize_prices(prices)

        # Try fallback source
        prices = cls.scrape_e_petrol()
        if prices:
            return cls._normalize_prices(prices)

        # Use safe defaults
        logger.warning("[SCRAPER] All sources failed - using safe defaults")
        return cls.SAFE_DEFAULTS.copy()

    @classmethod
    def _normalize_prices(cls, prices: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize prices - fill missing values with defaults.
        """
        normalized = cls.SAFE_DEFAULTS.copy()
        normalized.update(prices)
        return normalized

    @classmethod
    def save_to_json(cls, prices: Dict[str, float]) -> None:
        """
        Save fuel prices to JSON file.

        Format:
        {
            "fuel_prices": {
                "Pb95": 6.05,
                "ON": 6.15,
                "LPG": 2.85
            },
            "last_updated": "2025-01-04T10:30:00",
            "source": "autocentrum.pl"
        }
        """
        data = {
            "fuel_prices": prices,
            "last_updated": datetime.now().isoformat(),
            "source": "live_scraper"
        }

        # Ensure directory exists
        cls.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data (to preserve market data)
        existing_data = {}
        if cls.DATA_FILE.exists():
            try:
                with open(cls.DATA_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                logger.warning(f"[SCRAPER] Could not load existing data: {e}")

        # Merge with existing data
        existing_data.update(data)

        # Save
        with open(cls.DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        logger.info(f"[SCRAPER] Prices saved to {cls.DATA_FILE}: {prices}")

    @classmethod
    def load_from_json(cls) -> Optional[Dict[str, any]]:
        """
        Load fuel prices from JSON file.

        Returns:
            Dict with prices and metadata, or None if file doesn't exist
        """
        if not cls.DATA_FILE.exists():
            return None

        try:
            with open(cls.DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if data has fuel_prices key
            if 'fuel_prices' not in data:
                return None

            return data
        except Exception as e:
            logger.error(f"[SCRAPER] Error loading JSON: {e}")
            return None

    @classmethod
    def is_data_fresh(cls, max_age_hours: int = 24) -> bool:
        """
        Check if cached data is still fresh (< 24 hours old).

        Args:
            max_age_hours: Maximum age in hours (default: 24)

        Returns:
            True if data is fresh, False otherwise
        """
        data = cls.load_from_json()
        if not data or 'last_updated' not in data:
            return False

        try:
            last_updated = datetime.fromisoformat(data['last_updated'])
            age = datetime.now() - last_updated

            is_fresh = age < timedelta(hours=max_age_hours)

            if is_fresh:
                logger.info(f"[SCRAPER] Cached data is fresh (age: {age.total_seconds() / 3600:.1f}h)")
            else:
                logger.info(f"[SCRAPER] Cached data is stale (age: {age.total_seconds() / 3600:.1f}h)")

            return is_fresh
        except Exception as e:
            logger.error(f"[SCRAPER] Error checking data freshness: {e}")
            return False

    @classmethod
    def get_prices_with_cache(cls, force_refresh: bool = False) -> Dict[str, float]:
        """
        Get fuel prices with intelligent caching.

        Strategy:
        1. Check if cached data exists and is fresh (< 24h)
        2. If yes, return cached data
        3. If no, scrape new data and cache it

        Args:
            force_refresh: Force scraping even if cache is fresh

        Returns:
            Dict with fuel prices
        """
        # Check cache first
        if not force_refresh and cls.is_data_fresh():
            data = cls.load_from_json()
            if data and 'fuel_prices' in data:
                logger.info(f"[SCRAPER] Using cached prices: {data['fuel_prices']}")
                return data['fuel_prices']

        # Scrape new data
        logger.info("[SCRAPER] Cache miss or stale - scraping new data...")
        print("[GOTHAM] 🔍 Scraping live fuel prices...")
        prices = cls.get_live_prices()

        # Save to cache
        cls.save_to_json(prices)

        print(f"[GOTHAM] 💾 Fuel prices cached: Pb95={prices.get('Pb95', 0)} PLN, ON={prices.get('ON', 0)} PLN, LPG={prices.get('LPG', 0)} PLN")

        return prices


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== GOTHAM LIVE FUEL PRICE SCRAPER ===\n")

    # Test scraping
    print("1. Testing live scraping...")
    prices = FuelPriceScraper.get_live_prices()
    print(f"   Live prices: {prices}\n")

    # Test caching
    print("2. Saving to cache...")
    FuelPriceScraper.save_to_json(prices)
    print(f"   Saved to: {FuelPriceScraper.DATA_FILE}\n")

    # Test loading from cache
    print("3. Loading from cache...")
    cached_prices = FuelPriceScraper.get_prices_with_cache()
    print(f"   Cached prices: {cached_prices}\n")

    # Test freshness check
    print("4. Checking data freshness...")
    is_fresh = FuelPriceScraper.is_data_fresh()
    print(f"   Is fresh: {is_fresh}\n")
