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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

    # Marki konkurencyjne (premium segment - potencjalni klienci leasingu)
    COMPETITOR_BRANDS = ["BMW", "MERCEDES-BENZ", "AUDI", "VOLVO"]

    # Cache settings
    CACHE_FILE = Path(__file__).parent.parent.parent.parent / "dane" / "cepik_cache.json"
    CACHE_TTL_HOURS = 24

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
        cached_data = self._get_from_cache(cache_key)
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
        self._save_to_cache(cache_key, results)

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
        cached_data = self._get_from_cache(cache_key)
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
        self._save_to_cache(cache_key, count)

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

    def _get_from_cache(self, cache_key: str) -> Optional[any]:
        """
        Pobiera dane z cache.

        Args:
            cache_key: Klucz cache

        Returns:
            Cached data lub None jeśli brak/stare dane
        """
        if not self.CACHE_FILE.exists():
            return None

        try:
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            if cache_key not in cache:
                return None

            entry = cache[cache_key]

            # Check TTL
            cached_time = datetime.fromisoformat(entry['timestamp'])
            age = datetime.now() - cached_time

            if age < timedelta(hours=self.CACHE_TTL_HOURS):
                logger.info(f"[CEPiK Cache] HIT - {cache_key} (age: {age.total_seconds() / 3600:.1f}h)")
                return entry['data']
            else:
                logger.info(f"[CEPiK Cache] EXPIRED - {cache_key} (age: {age.total_seconds() / 3600:.1f}h)")
                return None

        except Exception as e:
            logger.error(f"[CEPiK Cache] Error reading cache: {e}")
            return None

    def _save_to_cache(self, cache_key: str, data: any) -> None:
        """
        Zapisuje dane do cache.

        Args:
            cache_key: Klucz cache
            data: Dane do zapisania
        """
        try:
            # Ensure directory exists
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Load existing cache
            cache = {}
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)

            # Add new entry
            cache[cache_key] = {
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            # Save
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

            logger.info(f"[CEPiK Cache] SAVED - {cache_key}")

        except Exception as e:
            logger.error(f"[CEPiK Cache] Error saving cache: {e}")

    @classmethod
    def clear_cache(cls) -> None:
        """Wyczyść cały cache (Admin Panel feature)."""
        if cls.CACHE_FILE.exists():
            cls.CACHE_FILE.unlink()
            logger.info("[CEPiK Cache] Cache cleared")


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== GOTHAM CEPiK API CONNECTOR TEST ===\n")

    connector = CEPiKConnector()

    # Get dates for lease ending window
    date_from, date_to = CEPiKConnector.get_lease_ending_dates()
    print(f"📅 Lease ending window: {date_from} - {date_to}")
    print(f"   (3 years ago from today)\n")

    # Test 1: Get competitor registrations
    print("1️⃣  Testing competitor registrations (BMW, Mercedes, Audi, Volvo)...")
    wojewodztwo = "ŚLĄSKIE"

    results = connector.get_competitor_registrations(wojewodztwo, date_from, date_to)

    print(f"\n🎯 POTENTIAL LEASING LEADS in {wojewodztwo}:")
    for brand, count in results.items():
        if brand != "TOTAL":
            print(f"   - {brand}: {count:,} cars")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   TOTAL: {results['TOTAL']:,} hot leads! 🔥\n")

    # Test 2: Get Tesla registrations
    print("2️⃣  Testing Tesla registrations (market share tracking)...")
    tesla_count = connector.get_tesla_registrations(wojewodztwo, date_from, date_to)
    print(f"\n🚗 TESLA registrations in {wojewodztwo}: {tesla_count:,}\n")

    # Test 3: Cache check
    print("3️⃣  Testing cache...")
    print("   Running same query again (should use cache)...")
    results_cached = connector.get_competitor_registrations(wojewodztwo, date_from, date_to)
    print(f"   ✅ Cached result: {results_cached['TOTAL']:,} leads\n")

    print("🎉 All tests completed!")
