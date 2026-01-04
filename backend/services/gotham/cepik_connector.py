"""
GOTHAM CEPiK API CONNECTOR
Prawdziwe połączenie z API CEPiK (Centralna Ewidencja Pojazdów i Kierowców)

Obsługuje:
- Pobieranie danych o rejestracji pojazdów premium (BMW, Mercedes, Audi, Volvo)
- Śledzenie rejestracji Tesla (udział w rynku)
- Paginacja (max 500 wyników na stronę)
- Retry logic i error handling
- Caching 24h

API Documentation: https://api.cepik.gov.pl
Endpoint: GET /pojazdy

Author: Senior Python Backend Developer
Version: 1.0.0
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from backend.services.gotham.store import CEPiKCache

logger = logging.getLogger(__name__)


class CEPiKConnector:
    """
    Connector dla API CEPiK - obsługa pobierania danych o rejestracjach pojazdów.

    Kluczowe funkcje:
    - get_competitor_registrations() - pobiera leady leasingowe (BMW, Mercedes, Audi, Volvo)
    - get_tesla_registrations() - śledzi udział Tesla w rynku
    - Caching 24h w pliku JSON
    - Automatic retry dla błędów sieciowych
    """

    # API Configuration
    BASE_URL = "https://api.cepik.gov.pl"
    ENDPOINT = "/pojazdy"
    MAX_RESULTS_PER_PAGE = 500  # Limit API
    REQUEST_TIMEOUT = 30  # seconds

    # Kody województw (TERYT)
    WOJEWODZTWA = {
        "DOLNOŚLĄSKIE": "02",
        "KUJAWSKO-POMORSKIE": "04",
        "LUBELSKIE": "06",
        "LUBUSKIE": "08",
        "ŁÓDZKIE": "10",
        "MAŁOPOLSKIE": "12",
        "MAZOWIECKIE": "14",
        "OPOLSKIE": "16",
        "PODKARPACKIE": "18",
        "PODLASKIE": "20",
        "POMORSKIE": "22",
        "ŚLĄSKIE": "24",
        "ŚWIĘTOKRZYSKIE": "26",
        "WARMIŃSKO-MAZURSKIE": "28",
        "WIELKOPOLSKIE": "30",
        "ZACHODNIOPOMORSKIE": "32"
    }

    # TARGET BRANDS for lease expiry tracking (premium segment + Tesla)
    # These brands represent high-value leasing opportunities
    TARGET_BRANDS = ["TESLA", "BMW", "MERCEDES-BENZ", "AUDI", "VOLVO"]

    # Legacy: Competitor brands (without Tesla)
    COMPETITOR_BRANDS = ["BMW", "MERCEDES-BENZ", "AUDI", "VOLVO"]

    def __init__(self):
        """Initialize connector with retry logic and session pooling."""
        self.session = self._create_session()

    @classmethod
    def _create_session(cls) -> requests.Session:
        """
        Create requests session with retry logic.

        Retry strategy:
        - 3 retries for network errors
        - Exponential backoff (0.5s, 1s, 2s)
        - Retry on 500, 502, 503, 504
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,  # 0.5s, 1s, 2s
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(
        self,
        wojewodztwo_kod: str,
        date_from: str,
        date_to: str,
        marka: str,
        page: int = 1
    ) -> Optional[Dict]:
        """
        Make API request to CEPiK.

        Args:
            wojewodztwo_kod: TERYT code (e.g., "24" for Śląskie)
            date_from: Start date in YYYYMMDD format
            date_to: End date in YYYYMMDD format
            marka: Brand name (e.g., "BMW", "TESLA")
            page: Page number for pagination

        Returns:
            API response JSON or None if error
        """
        url = f"{self.BASE_URL}{self.ENDPOINT}"

        params = {
            "wojewodztwo": wojewodztwo_kod,
            "data-od": date_from,
            "data-do": date_to,
            "filter[marka]": marka,
            "page": page,
            "limit": self.MAX_RESULTS_PER_PAGE
        }

        headers = {
            "User-Agent": "GOTHAM-Tesla-LeadGen/1.0",
            "Accept": "application/json"
        }

        try:
            logger.info(f"[CEPiK API] Request: {marka} in woj.{wojewodztwo_kod} ({date_from} - {date_to}), page {page}")

            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.REQUEST_TIMEOUT
            )

            # Handle HTTP errors
            if response.status_code == 404:
                logger.warning(f"[CEPiK API] 404 - No data found for {marka}")
                return {"data": [], "total": 0}

            elif response.status_code == 400:
                logger.error(f"[CEPiK API] 400 - Bad request: {response.text}")
                return None

            elif response.status_code != 200:
                logger.error(f"[CEPiK API] HTTP {response.status_code}: {response.text}")
                return None

            data = response.json()
            logger.info(f"[CEPiK API] Success: {len(data.get('data', []))} results")
            return data

        except requests.exceptions.Timeout:
            logger.error(f"[CEPiK API] Timeout after {self.REQUEST_TIMEOUT}s")
            return None

        except requests.exceptions.ConnectionError as e:
            logger.error(f"[CEPiK API] Connection error: {e}")
            return None

        except Exception as e:
            logger.error(f"[CEPiK API] Unexpected error: {e}")
            return None

    def _get_all_pages(
        self,
        wojewodztwo_kod: str,
        date_from: str,
        date_to: str,
        marka: str
    ) -> int:
        """
        Get total count with pagination handling.

        API może zwrócić max 500 wyników na stronę.
        Ta metoda automatycznie pobiera wszystkie strony.

        Args:
            wojewodztwo_kod: TERYT code
            date_from: Start date YYYYMMDD
            date_to: End date YYYYMMDD
            marka: Brand name

        Returns:
            Total count of registrations
        """
        total_count = 0
        page = 1

        while True:
            response = self._make_request(wojewodztwo_kod, date_from, date_to, marka, page)

            if response is None:
                # Error occurred - return current count
                logger.warning(f"[CEPiK API] Error on page {page}, returning partial count: {total_count}")
                break

            data_items = response.get("data", [])
            page_count = len(data_items)
            total_count += page_count

            logger.info(f"[CEPiK API] Page {page}: {page_count} items (total so far: {total_count})")

            # Check if we need to fetch more pages
            if page_count < self.MAX_RESULTS_PER_PAGE:
                # Last page reached
                break

            # Continue to next page
            page += 1

            # Safety limit - prevent infinite loops
            if page > 100:
                logger.warning(f"[CEPiK API] Reached page limit (100), stopping pagination")
                break

        return total_count

    def get_leasing_expiry_counts(self, months_back: int = 36) -> Dict[str, int]:
        """
        Get vehicle registration counts for brands whose leases are expiring.

        BUSINESS LOGIC:
        - Standard leasing contracts = 36 months (3 years)
        - Cars registered 36 months ago = leases expiring NOW
        - These are HOT LEADS for new Tesla sales!

        This function calculates the date range dynamically based on months_back parameter,
        fetches data for all TARGET_BRANDS (Tesla, BMW, Mercedes-Benz, Audi, Volvo),
        and returns counts for Silesian Voivodeship (code 24).

        Args:
            months_back: How many months back to look (default: 36 for 3-year leases)

        Returns:
            Dictionary with brand counts, e.g.:
            {
                "TESLA": 45,
                "BMW": 120,
                "MERCEDES-BENZ": 95,
                "AUDI": 85,
                "VOLVO": 32,
                "TOTAL": 377
            }

        Example:
            >>> connector = CEPiKConnector()
            >>> counts = connector.get_leasing_expiry_counts(months_back=36)
            >>> print(f"Total leads: {counts['TOTAL']}")
        """
        print(f"\n[GOTHAM] 🔍 Fetching real data from CEPiK API...")
        print(f"[GOTHAM] 📅 Looking back {months_back} months for lease expiries\n")

        # Calculate date range
        today = datetime.now()

        # Start date: X months ago (beginning of month)
        start_date = today - timedelta(days=30 * months_back)
        date_from = start_date.replace(day=1)

        # End date: X-1 months ago (end of month)
        end_date = today - timedelta(days=30 * (months_back - 1))
        if end_date.month == 12:
            date_to = end_date.replace(year=end_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            date_to = end_date.replace(month=end_date.month + 1, day=1) - timedelta(days=1)

        date_from_str = date_from.strftime("%Y%m%d")
        date_to_str = date_to.strftime("%Y%m%d")

        print(f"[GOTHAM] Date range: {date_from_str} - {date_to_str}")
        print(f"[GOTHAM]   ({date_from.strftime('%B %Y')} - registrations expiring now)\n")

        # Cache key
        cache_key = f"leasing_expiry_silesia_{months_back}m_{date_from_str}_{date_to_str}"

        # Check cache
        cached = CEPiKCache.get(cache_key)
        if cached is not None:
            print(f"[GOTHAM] ✅ Using cached data (fresh within 24h)")
            print(f"[GOTHAM] Total potential leads: {cached.get('TOTAL', 0):,}\n")
            return cached

        # Fetch fresh data
        wojewodztwo_kod = "24"  # Silesian Voivodeship (ŚLĄSKIE)
        results = {}
        total = 0

        print(f"[GOTHAM] 🌐 Querying CEPiK API for Silesian Voivodeship (code 24)...\n")

        # Query each brand
        for brand in self.TARGET_BRANDS:
            print(f"[GOTHAM] Fetching {brand}...")

            try:
                count = self._get_all_pages(wojewodztwo_kod, date_from_str, date_to_str, brand)
                results[brand] = count
                total += count

                print(f"[GOTHAM]   ✓ Found {count:,} {brand} vehicles\n")

                # Small delay to respect API rate limits
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"[GOTHAM] Error fetching {brand}: {e}")

                # Try to use fallback from cache
                stale_data = CEPiKCache._get_stale_fallback(cache_key)
                if stale_data and brand in stale_data:
                    results[brand] = stale_data[brand]
                    total += stale_data[brand]
                    print(f"[GOTHAM]   ⚠️  Using stale cache for {brand}: {stale_data[brand]:,}\n")
                else:
                    results[brand] = 0
                    print(f"[GOTHAM]   ❌ Failed to fetch {brand}, defaulting to 0\n")

        results["TOTAL"] = total

        # Save to cache
        CEPiKCache.set(cache_key, results)

        print(f"[GOTHAM] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"[GOTHAM] ✅ TOTAL POTENTIAL LEADS: {total:,} premium vehicles")
        print(f"[GOTHAM]    (Leases expiring in Silesia region)")
        print(f"[GOTHAM] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        return results

    def get_competitor_registrations(
        self,
        wojewodztwo: str,
        date_from: str,
        date_to: str
    ) -> Dict[str, int]:
        """
        Pobiera liczbę rejestracji aut premium (potencjalni klienci leasingu).

        Marki: BMW, Mercedes-Benz, Audi, Volvo

        LOGIKA BIZNESOWA:
        - Auta zarejestrowane 3 lata temu = kończy się leasing
        - To są gorące leady dla Tesla!

        Args:
            wojewodztwo: Nazwa województwa (e.g., "ŚLĄSKIE")
            date_from: Data początkowa YYYYMMDD
            date_to: Data końcowa YYYYMMDD

        Returns:
            Dict z liczbą rejestracji per marka, np:
            {
                "BMW": 245,
                "MERCEDES-BENZ": 189,
                "AUDI": 312,
                "VOLVO": 78,
                "TOTAL": 824
            }
        """
        # Check cache first
        cache_key = f"competitors_{wojewodztwo}_{date_from}_{date_to}"
        cached_data = CEPiKCache.get(cache_key)
        if cached_data is not None:
            logger.info(f"[CEPiK] Using cached data for {cache_key}")
            return cached_data

        # Get województwo code
        woj_kod = self.WOJEWODZTWA.get(wojewodztwo.upper())
        if not woj_kod:
            logger.error(f"[CEPiK] Invalid województwo: {wojewodztwo}")
            return {"TOTAL": 0}

        results = {}
        total = 0

        logger.info(f"[CEPiK] Fetching competitor registrations for {wojewodztwo} ({date_from} - {date_to})")

        # Query each brand
        for brand in self.COMPETITOR_BRANDS:
            count = self._get_all_pages(woj_kod, date_from, date_to, brand)
            results[brand] = count
            total += count

            logger.info(f"[CEPiK] Found {count} {brand}s ending lease in {wojewodztwo}")

        results["TOTAL"] = total

        # Save to cache
        CEPiKCache.set(cache_key, results)

        logger.info(f"[CEPiK] ✅ Total potential leads: {total} premium cars in {wojewodztwo}")

        return results

    def get_tesla_registrations(
        self,
        wojewodztwo: str,
        date_from: str,
        date_to: str
    ) -> int:
        """
        Pobiera liczbę rejestracji Tesla (tracking market share).

        Args:
            wojewodztwo: Nazwa województwa
            date_from: Data początkowa YYYYMMDD
            date_to: Data końcowa YYYYMMDD

        Returns:
            Liczba zarejestrowanych Tesli
        """
        # Check cache first
        cache_key = f"tesla_{wojewodztwo}_{date_from}_{date_to}"
        cached_data = CEPiKCache.get(cache_key)
        if cached_data is not None:
            logger.info(f"[CEPiK] Using cached Tesla data for {cache_key}")
            return cached_data

        # Get województwo code
        woj_kod = self.WOJEWODZTWA.get(wojewodztwo.upper())
        if not woj_kod:
            logger.error(f"[CEPiK] Invalid województwo: {wojewodztwo}")
            return 0

        logger.info(f"[CEPiK] Fetching Tesla registrations for {wojewodztwo}")

        count = self._get_all_pages(woj_kod, date_from, date_to, "TESLA")

        # Save to cache
        CEPiKCache.set(cache_key, count)

        logger.info(f"[CEPiK] Found {count} TESLAs registered in {wojewodztwo}")

        return count

    @classmethod
    def get_lease_ending_dates(cls) -> Tuple[str, str]:
        """
        Oblicza zakres dat dla aut kończących leasing.

        LOGIKA BIZNESOWA:
        - Leasing trwa 3 lata
        - Auta zarejestrowane dokładnie 3 lata temu = TERAZ kończy się leasing
        - Okno: 1 miesiąc (np. styczeń 2023 dla stycznia 2026)

        Returns:
            Tuple (date_from, date_to) w formacie YYYYMMDD
        """
        today = datetime.now()

        # 3 lata wstecz
        three_years_ago = today.replace(year=today.year - 3)

        # Początek miesiąca
        date_from = three_years_ago.replace(day=1)

        # Koniec miesiąca (początek następnego miesiąca - 1 dzień)
        if three_years_ago.month == 12:
            date_to = three_years_ago.replace(year=three_years_ago.year + 1, month=1, day=1)
        else:
            date_to = three_years_ago.replace(month=three_years_ago.month + 1, day=1)

        date_to = date_to - timedelta(days=1)

        return date_from.strftime("%Y%m%d"), date_to.strftime("%Y%m%d")

    @staticmethod
    def clear_cache() -> None:
        """
        Clear CEPiK cache (Admin Panel feature).

        Use this to force fresh data fetch or reset after API changes.
        """
        CEPiKCache.invalidate()
        logger.info("[CEPiK] Cache cleared - next request will fetch fresh data")


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== GOTHAM CEPiK API CONNECTOR TEST ===\n")

    connector = CEPiKConnector()

    # Test 1: NEW FUNCTION - Get leasing expiry counts (main use case)
    print("1️⃣  Testing get_leasing_expiry_counts() - PRIMARY FUNCTION")
    print("   This is the MAIN function to use - it includes ALL brands (Tesla + competitors)\n")

    results = connector.get_leasing_expiry_counts(months_back=36)

    print(f"\n🎯 LEASING EXPIRY LEADS (Silesia, 36 months back):")
    for brand, count in results.items():
        if brand != "TOTAL":
            print(f"   - {brand}: {count:,} cars")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   TOTAL: {results['TOTAL']:,} hot leads! 🔥\n")

    # Test 2: Cache check
    print("2️⃣  Testing cache...")
    print("   Running same query again (should use cache)...")
    results_cached = connector.get_leasing_expiry_counts(months_back=36)
    print(f"   ✅ Cached result: {results_cached['TOTAL']:,} leads\n")

    # Test 3: Legacy functions (backward compatibility)
    print("3️⃣  Testing legacy functions (for backward compatibility)...")

    # Get dates for lease ending window
    date_from, date_to = CEPiKConnector.get_lease_ending_dates()
    print(f"   📅 Lease ending window: {date_from} - {date_to}")
    print(f"      (3 years ago from today)\n")

    # Get competitor registrations (without Tesla)
    wojewodztwo = "ŚLĄSKIE"
    competitor_results = connector.get_competitor_registrations(wojewodztwo, date_from, date_to)
    print(f"   Competitor brands only: {competitor_results['TOTAL']:,} cars\n")

    # Get Tesla separately
    tesla_count = connector.get_tesla_registrations(wojewodztwo, date_from, date_to)
    print(f"   Tesla separately: {tesla_count:,} cars\n")

    print("🎉 All tests completed!")
