"""
ASSET SNIPER - Gotham Engine Module (Palantir-Level Intelligence)
Warstwy danych: Wealth Proxy (M2), Charger Infrastructure, Tax Engine, Leasing Cycle

Gotham Layers:
1. Wealth Proxy - KALKULOWANA zamożność na podstawie cen m² nieruchomości
2. Charger Infrastructure - precyzyjna odległość do ładowarki (ZIP prefix coords)
3. Tax Engine - korzyści podatkowe EV vs ICE
4. Leasing Cycle - cykl wymiany samochodu (wiek firmy)
5. Palantir Correlations - agresywne estymacje gdy brak danych

Based on: BIBLE v1.0 + Palantir Upgrade
Author: BigDInc Team
"""

import pandas as pd
import math
from typing import Tuple, Dict, Optional, List
from datetime import date
import logging
import re

from .config import (
    # Legacy (deprecated)
    WEALTH_PROXY_SILESIA,
    # New Palantir-level data
    REAL_ESTATE_MARKET_DATA,
    NATIONAL_AVG_M2_PRICE,
    POSTAL_CODE_CITY_MAP,
    POSTAL_PREFIX_COORDINATES,
    HIGH_WEALTH_STREET_KEYWORDS,
    PKD_WEALTH_CORRELATION,
    # Other configs
    TAX_BENEFITS,
    LEASING_CYCLE_MAP,
)

logger = logging.getLogger(__name__)

# Import OpenChargeMap client for live charger data
try:
    from asset_sniper.integrations.opencharge_client import OpenChargeClient
    OPENCHARGE_AVAILABLE = True
except ImportError:
    OPENCHARGE_AVAILABLE = False
    logger.warning("[GOTHAM] OpenChargeMap client not available - will use fallback")


class GothamEngine:
    """
    Data enrichment engine with Palantir-level market intelligence.

    Layers:
    1. Wealth Proxy (M2) - KALKULOWANA zamożność na podstawie cen m² nieruchomości
    2. Charger Infrastructure - Precyzyjna odległość do ładowarki
    3. Tax Engine - EV tax benefits calculation
    4. Leasing Cycle - Company age -> lease renewal probability
    5. Palantir Correlations - Agresywne estymacje gdy brak danych
    """

    # Wealth tier thresholds based on m² price vs national average
    WEALTH_TIERS = {
        "S": (1.5, float('inf')),   # >1.5x średniej = WEALTH S
        "PREMIUM": (1.3, 1.5),      # 1.3-1.5x = PREMIUM
        "HIGH": (1.1, 1.3),         # 1.1-1.3x = HIGH
        "MEDIUM": (0.9, 1.1),       # 0.9-1.1x = MEDIUM (around average)
        "STANDARD": (0.7, 0.9),     # 0.7-0.9x = STANDARD
        "LOW": (0.0, 0.7),          # <0.7x = LOW
    }

    def __init__(self, use_live_api: bool = True):
        """
        Initialize Gotham Engine with Palantir-level intelligence.

        Args:
            use_live_api: If True, use live APIs (OpenChargeMap, etc.)
                         If False, use static data only (NOT RECOMMENDED - mock data)
        """
        self.use_live_api = use_live_api
        self.opencharge_client = None

        if use_live_api and OPENCHARGE_AVAILABLE:
            self.opencharge_client = OpenChargeClient()
            logger.info(f"[GOTHAM] Initialized with Palantir-Level Intelligence + LIVE APIs")
        else:
            logger.warning(f"[GOTHAM] Initialized in FALLBACK mode (static data only)")

        # Cache for charger locations (avoid redundant API calls)
        self._charger_cache = {}

    # === LAYER 1: WEALTH PROXY (M2-Based Calculation) ===

    @staticmethod
    def _get_city_from_postal(postal_code: str) -> Optional[str]:
        """
        Get city name from postal code using prefix mapping.

        Uses hierarchical matching: 4-char prefix -> 3-char -> 2-char

        Args:
            postal_code: Polish postal code (XX-XXX format)

        Returns:
            City name or None
        """
        if not postal_code or len(postal_code) < 2:
            return None

        # Try 4-character prefix first (most specific, e.g., "81-8" for Sopot)
        if len(postal_code) >= 4:
            prefix_4 = postal_code[:4]
            if prefix_4 in POSTAL_CODE_CITY_MAP:
                return POSTAL_CODE_CITY_MAP[prefix_4]

        # Try 3-character prefix
        if len(postal_code) >= 3:
            prefix_3 = postal_code[:3]
            if prefix_3 in POSTAL_CODE_CITY_MAP:
                return POSTAL_CODE_CITY_MAP[prefix_3]

        # Fallback to 2-digit prefix
        prefix_2 = postal_code[:2]
        return POSTAL_CODE_CITY_MAP.get(prefix_2)

    @staticmethod
    def _calculate_wealth_from_m2(m2_price: float) -> Tuple[int, str]:
        """
        Calculate wealth score (1-10) and tier from m² price.

        Logic (Palantir asymmetry):
        - Cena m² > 1.5x średnia krajowa -> Wealth Tier S (score 10)
        - Firma stać na drogie biuro -> stać ją na Teslę

        Args:
            m2_price: Average m² price in PLN

        Returns:
            Tuple of (wealth_score 1-10, wealth_tier name)
        """
        ratio = m2_price / NATIONAL_AVG_M2_PRICE

        if ratio >= 1.5:
            return (10, "S")
        elif ratio >= 1.3:
            return (9, "PREMIUM")
        elif ratio >= 1.1:
            return (8, "HIGH")
        elif ratio >= 0.95:
            return (7, "MEDIUM_HIGH")
        elif ratio >= 0.85:
            return (6, "MEDIUM")
        elif ratio >= 0.75:
            return (5, "STANDARD")
        elif ratio >= 0.65:
            return (4, "STANDARD_LOW")
        elif ratio >= 0.55:
            return (3, "LOW")
        elif ratio >= 0.45:
            return (2, "LOW")
        else:
            return (1, "VERY_LOW")

    @staticmethod
    def _check_premium_street(street: str) -> bool:
        """
        Check if street name indicates high-wealth location.

        Palantir correlation: Prestigious street names = higher wealth probability.

        Args:
            street: Street address

        Returns:
            True if street matches wealth keywords
        """
        if not street:
            return False

        street_upper = street.upper()
        for keyword in HIGH_WEALTH_STREET_KEYWORDS:
            if keyword.upper() in street_upper:
                return True
        return False

    @staticmethod
    def _get_pkd_wealth_bonus(pkd_code: str) -> int:
        """
        Get wealth bonus from PKD code (Palantir correlation).

        Logic: Certain industries (lawyers, doctors, IT) indicate higher income.
        If we don't have location data, we can still estimate wealth from industry.

        Args:
            pkd_code: PKD industry code

        Returns:
            Wealth score (1-10)
        """
        if not pkd_code:
            return PKD_WEALTH_CORRELATION.get("DEFAULT", 5)

        return PKD_WEALTH_CORRELATION.get(pkd_code, PKD_WEALTH_CORRELATION.get("DEFAULT", 5))

    def get_wealth_score(
        self,
        postal_code: str,
        city: str = None,
        street: str = None,
        pkd_code: str = None
    ) -> Dict[str, any]:
        """
        Calculate wealth score using Palantir-level intelligence.

        Multi-layer fallback logic:
        1. Try m² price from postal code -> city mapping
        2. If city provided directly, use that
        3. Check for premium street keywords
        4. Fall back to PKD-based wealth correlation
        5. Never return just DEFAULT - always explain WHY

        Args:
            postal_code: Polish postal code (XX-XXX format)
            city: City name (optional, for direct lookup)
            street: Street address (optional, for premium detection)
            pkd_code: PKD code (optional, for industry correlation)

        Returns:
            Dictionary with:
            - wealth_score (int 1-10)
            - wealth_tier (str)
            - wealth_signal (str) - explanation of WHY this score
            - m2_price (float) - estimated m² price
            - data_source (str) - where the data came from
        """
        wealth_signal_parts = []
        data_source = "UNKNOWN"
        m2_price = None

        # === STEP 1: Try to get city from postal code ===
        resolved_city = city or self._get_city_from_postal(postal_code)

        if resolved_city and resolved_city in REAL_ESTATE_MARKET_DATA:
            city_data = REAL_ESTATE_MARKET_DATA[resolved_city]
            m2_price = city_data["avg_m2"]
            score, tier = self._calculate_wealth_from_m2(m2_price)
            data_source = f"M2_MARKET:{resolved_city}"
            wealth_signal_parts.append(f"Miasto {resolved_city} - cena m² {m2_price:,} PLN")

            # Check for premium district bonus
            if street:
                for district in city_data.get("premium_districts", []):
                    if district.upper() in street.upper():
                        score = min(10, score + 1)
                        wealth_signal_parts.append(f"Dzielnica premium: {district}")
                        break

        # === STEP 2: Premium street keyword detection ===
        elif street and self._check_premium_street(street):
            score = 8
            tier = "HIGH"
            data_source = "STREET_KEYWORDS"
            m2_price = NATIONAL_AVG_M2_PRICE * 1.2  # Estimate
            wealth_signal_parts.append(f"Ulica prestiżowa: {street[:30]}")

        # === STEP 3: PKD-based wealth correlation (Palantir fallback) ===
        elif pkd_code and pkd_code in PKD_WEALTH_CORRELATION:
            score = self._get_pkd_wealth_bonus(pkd_code)
            tier = "HIGH" if score >= 8 else "MEDIUM" if score >= 6 else "STANDARD"
            data_source = f"PKD_CORRELATION:{pkd_code}"
            m2_price = NATIONAL_AVG_M2_PRICE * (score / 10)  # Estimate
            wealth_signal_parts.append(f"Branża premium PKD {pkd_code} → zamożność {score}/10")

        # === STEP 4: Final fallback - use national average ===
        else:
            score = 5
            tier = "STANDARD"
            data_source = "DEFAULT_FALLBACK"
            m2_price = REAL_ESTATE_MARKET_DATA["DEFAULT"]["avg_m2"]
            wealth_signal_parts.append("Brak danych lokalizacji - użyto średniej krajowej")

        # === Build wealth signal explanation ===
        if not wealth_signal_parts:
            wealth_signal = "Brak sygnału zamożności"
        else:
            wealth_signal = " | ".join(wealth_signal_parts)

        return {
            "wealth_score": score,
            "wealth_tier": tier,
            "wealth_signal": wealth_signal,
            "m2_price": m2_price,
            "data_source": data_source,
            "city": resolved_city,
        }

    # === LEGACY COMPATIBILITY ===
    @staticmethod
    def get_wealth_score_legacy(postal_code: str) -> Tuple[int, str]:
        """
        DEPRECATED: Legacy wealth score method for backwards compatibility.
        Use get_wealth_score() for Palantir-level intelligence.
        """
        if not postal_code or len(postal_code) < 6:
            return WEALTH_PROXY_SILESIA["DEFAULT"]

        if postal_code in WEALTH_PROXY_SILESIA:
            return WEALTH_PROXY_SILESIA[postal_code]

        prefix = postal_code[:2]
        for key, value in WEALTH_PROXY_SILESIA.items():
            if key.startswith(prefix) and key != "DEFAULT":
                return value

        return WEALTH_PROXY_SILESIA["DEFAULT"]

    # === LAYER 2: CHARGER INFRASTRUCTURE (Geo-Precision Upgrade) ===

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    @staticmethod
    def _get_postal_coords(postal_code: str) -> Optional[Tuple[float, float]]:
        """
        Get precise coordinates for postal code using hierarchical prefix matching.

        Uses POSTAL_PREFIX_COORDINATES with 3-digit precision where available.
        Falls back to 2-digit prefix if 3-digit not found.

        Geo-precision upgrade: Instead of "all Katowice = same point",
        we now differentiate between Śródmieście, Brynów, Ligota, etc.

        Args:
            postal_code: Polish postal code (XX-XXX format)

        Returns:
            Tuple of (latitude, longitude) or None
        """
        if not postal_code or len(postal_code) < 2:
            return None

        # Try most specific prefix first (4 chars, e.g., "40-0")
        if len(postal_code) >= 4:
            prefix_4 = postal_code[:4]
            if prefix_4 in POSTAL_PREFIX_COORDINATES:
                return POSTAL_PREFIX_COORDINATES[prefix_4]

        # Try 3-digit prefix (first digit after dash, e.g., "40-0" -> check "40-0")
        if len(postal_code) >= 4:
            # Format: "40-001" -> try "40-0"
            prefix_3_dash = f"{postal_code[:2]}-{postal_code[3]}"
            if prefix_3_dash in POSTAL_PREFIX_COORDINATES:
                return POSTAL_PREFIX_COORDINATES[prefix_3_dash]

        # Try 3-char prefix without dash (e.g., "400")
        if len(postal_code) >= 3:
            prefix_3 = postal_code[:3].replace("-", "")
            if prefix_3 in POSTAL_PREFIX_COORDINATES:
                return POSTAL_PREFIX_COORDINATES[prefix_3]

        # Fallback to 2-digit prefix
        prefix_2 = postal_code[:2]
        if prefix_2 in POSTAL_PREFIX_COORDINATES:
            return POSTAL_PREFIX_COORDINATES[prefix_2]

        # Ultimate fallback: city center coordinates
        city = GothamEngine._get_city_from_postal(postal_code)
        if city and city in REAL_ESTATE_MARKET_DATA:
            # Use city-center fallback coords from common knowledge
            city_coords_fallback = {
                "Warszawa": (52.2297, 21.0122),
                "Kraków": (50.0647, 19.9450),
                "Wrocław": (51.1079, 17.0385),
                "Gdańsk": (54.3520, 18.6466),
                "Poznań": (52.4064, 16.9252),
                "Katowice": (50.2649, 19.0238),
                "Łódź": (51.7592, 19.4560),
                "Szczecin": (53.4285, 14.5528),
            }
            return city_coords_fallback.get(city)

        return None

    def calculate_charger_distance(self, postal_code: str) -> float:
        """
        Calculate distance to nearest EV charger using LIVE API data.

        NOW WITH REAL-TIME DATA:
        - Uses OpenChargeMap API to get live charger locations
        - Caches results per region to avoid redundant API calls
        - Filters for fast chargers (50kW+) only
        - Falls back to static data if API unavailable

        Args:
            postal_code: Polish postal code

        Returns:
            Distance in kilometers (0 if coordinates not found)
        """
        # Get coordinates for postal code
        coords = self._get_postal_coords(postal_code)
        if not coords:
            logger.debug(f"No coordinates for postal code: {postal_code}")
            return 0.0

        lat, lon = coords

        # Check cache first (cache key based on region - 2-digit postal prefix)
        cache_key = postal_code[:2] if len(postal_code) >= 2 else postal_code
        if cache_key in self._charger_cache:
            nearest_charger = self._charger_cache[cache_key]
            distance = self._haversine_distance(lat, lon, nearest_charger["lat"], nearest_charger["lon"])
            logger.debug(f"[GOTHAM] Using cached charger data for region {cache_key}")
            return round(distance, 1)

        # Use live API if available
        if self.use_live_api and self.opencharge_client:
            try:
                logger.info(f"[GOTHAM] 🔍 Fetching live charger data from OpenChargeMap for ({lat}, {lon})")

                # Get nearest fast charger (50kW+)
                nearest = self.opencharge_client.get_nearest_fast_charger(lat, lon)

                if nearest:
                    logger.info(f"[GOTHAM] ✅ Found nearest charger: {nearest['name']} at {nearest['distance_km']}km")

                    # Cache for this region
                    self._charger_cache[cache_key] = {
                        "lat": nearest["lat"],
                        "lon": nearest["lon"],
                        "name": nearest["name"]
                    }

                    return nearest["distance_km"]
                else:
                    logger.warning(f"[GOTHAM] ⚠️  No fast chargers found via API - using fallback")

            except Exception as e:
                logger.error(f"[GOTHAM] ❌ OpenChargeMap API error: {e} - using fallback")

        # Fallback to static charger data (from config.py)
        logger.debug(f"[GOTHAM] Using static charger data (fallback mode)")

        # Import static data as fallback
        from .config import CHARGER_LOCATIONS

        min_distance = float('inf')
        nearest_charger = None

        for charger in CHARGER_LOCATIONS:
            distance = self._haversine_distance(lat, lon, charger["lat"], charger["lon"])
            if distance < min_distance:
                min_distance = distance
                nearest_charger = charger

        # Cache the fallback result
        if nearest_charger:
            self._charger_cache[cache_key] = {
                "lat": nearest_charger["lat"],
                "lon": nearest_charger["lon"],
                "name": nearest_charger.get("name", "Unknown")
            }

        return round(min_distance, 1) if min_distance != float('inf') else 0.0

    # === LAYER 3: TAX ENGINE ===

    @staticmethod
    def calculate_tax_benefit(pkd_code: str, legal_form: str) -> Dict[str, float]:
        """
        Calculate annual tax benefits of EV vs ICE.

        Key benefits:
        - Higher depreciation limit (225k vs 150k PLN)
        - Tax savings at 19% or 32% rate
        - NaszEauto subsidy

        Args:
            pkd_code: PKD industry code
            legal_form: Legal form of company

        Returns:
            Dictionary with tax benefit breakdown
        """
        # Determine tax rate (32% for doctors, lawyers; 19% for others)
        tax_rate = 0.32 if pkd_code in ["6910Z", "8621Z"] else 0.19

        # Calculate depreciation advantage
        depreciation_diff = TAX_BENEFITS["TAX_DIFFERENCE"]
        annual_tax_saving = depreciation_diff * tax_rate

        # NaszEauto subsidy
        naszeauto = TAX_BENEFITS["NASZEAUTO_STANDARD"]  # TODO: Check for Karta Dużej Rodziny

        return {
            "annual_tax_saving": round(annual_tax_saving, 2),
            "depreciation_advantage": depreciation_diff,
            "naszeauto_subsidy": naszeauto,
            "total_first_year": round(annual_tax_saving + naszeauto, 2),
            "tax_rate": tax_rate,
        }

    # === LAYER 4: LEASING CYCLE ===

    @staticmethod
    def calculate_leasing_cycle(start_date: Optional[date]) -> Dict[str, any]:
        """
        Calculate leasing cycle stage based on company age.

        Business logic:
        - 0-1 years: Too early for leasing
        - 1-2 years: First consideration
        - 2-3 years: Active search
        - 3-4 years: Prime leasing window (3-year lease renewal)
        - 4-7 years: Mature company, regular leasing
        - 7+ years: Established, multiple leasing cycles

        Args:
            start_date: Company start date

        Returns:
            Dictionary with cycle info
        """
        if not start_date:
            return {
                "age_years": 0.0,
                "cycle": "UNKNOWN",
                "propensity": 0.0,
                "description": "Brak daty rozpoczęcia działalności",
            }

        # Calculate company age in years
        today = date.today()
        age_days = (today - start_date).days
        age_years = age_days / 365.25

        # Find matching cycle
        for (min_age, max_age), cycle_info in LEASING_CYCLE_MAP.items():
            if min_age <= age_years < max_age:
                return {
                    "age_years": round(age_years, 2),
                    **cycle_info,
                }

        # Fallback
        return {
            "age_years": round(age_years, 2),
            "cycle": "UNKNOWN",
            "propensity": 0.5,
            "description": "Nieznany cykl leasingowy",
        }

    # === MAIN PROCESSING METHOD (Palantir-Level Intelligence) ===

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process DataFrame through all Gotham layers with Palantir-level intelligence.

        Adds columns:
        - wealth_score (int 1-10) - CALCULATED from m² prices
        - wealth_tier (str: S/PREMIUM/HIGH/MEDIUM/STANDARD/LOW)
        - wealth_signal (str) - explanation of WHY this score
        - m2_price_estimated (float) - estimated m² price in PLN
        - wealth_data_source (str) - where the data came from
        - resolved_city (str) - city name resolved from postal code
        - charger_distance_km (float)
        - Potential_Savings_PLN (float) - renamed from tax_benefit_annual
        - tax_benefit_total_first_year (float)
        - leasing_cycle (str)
        - leasing_propensity (float 0-1)

        Args:
            df: DataFrame with cleaned data from LeadRefinery

        Returns:
            Enriched DataFrame with Palantir intelligence
        """
        logger.info(f"[GOTHAM-PALANTIR] Processing {len(df)} rows with asymmetric intelligence...")

        df_enriched = df.copy()

        # Find relevant columns (case-insensitive)
        postal_col = self._find_column(df_enriched, ['kod_pocztowy_clean', 'KodPocztowy', 'zip_code', 'postal_code'])
        city_col = self._find_column(df_enriched, ['miasto', 'Miasto', 'city', 'City', 'Miejscowosc'])
        street_col = self._find_column(df_enriched, ['ulica', 'Ulica', 'street', 'Street', 'Adres', 'adres'])
        pkd_col = self._find_column(df_enriched, ['pkd_clean', 'PkdGlowny', 'pkd', 'GlownyKodPkd'])
        form_col = self._find_column(df_enriched, ['legal_form_clean', 'FormaPrawna', 'legal_form'])
        date_col = self._find_column(df_enriched, ['data_rozpoczecia', 'DataRozpoczeciaDzialalnosci', 'start_date'])

        # === LAYER 1: WEALTH PROXY (M2-Based + Palantir Correlations) ===
        logger.info("[GOTHAM-PALANTIR] Layer 1: Wealth Proxy with M² intelligence...")

        def calculate_wealth_palantir(row):
            postal = row.get(postal_col, '') if postal_col else ''
            city = row.get(city_col, '') if city_col else None
            street = row.get(street_col, '') if street_col else None
            pkd = row.get(pkd_col, '') if pkd_col else None

            return self.get_wealth_score(
                postal_code=postal,
                city=city,
                street=street,
                pkd_code=pkd
            )

        wealth_data = df_enriched.apply(calculate_wealth_palantir, axis=1)

        df_enriched['wealth_score'] = wealth_data.apply(lambda x: x['wealth_score'])
        df_enriched['wealth_tier'] = wealth_data.apply(lambda x: x['wealth_tier'])
        df_enriched['wealth_signal'] = wealth_data.apply(lambda x: x['wealth_signal'])
        df_enriched['m2_price_estimated'] = wealth_data.apply(lambda x: x['m2_price'])
        df_enriched['wealth_data_source'] = wealth_data.apply(lambda x: x['data_source'])
        df_enriched['resolved_city'] = wealth_data.apply(lambda x: x.get('city', ''))

        # Log wealth distribution
        wealth_dist = df_enriched['wealth_tier'].value_counts()
        logger.info(f"[GOTHAM-PALANTIR] Wealth tier distribution: {wealth_dist.to_dict()}")

        # === LAYER 2: CHARGER INFRASTRUCTURE (Geo-Precision) ===
        logger.info("[GOTHAM-PALANTIR] Layer 2: Charger Infrastructure with precision coords...")

        if postal_col:
            df_enriched['charger_distance_km'] = df_enriched[postal_col].apply(self.calculate_charger_distance)
        else:
            df_enriched['charger_distance_km'] = 0.0
            logger.warning("[GOTHAM-PALANTIR] Postal code column not found - cannot calculate charger distance")

        # === LAYER 3: TAX ENGINE ===
        logger.info("[GOTHAM-PALANTIR] Layer 3: Tax Engine...")

        if pkd_col and form_col:
            def calc_tax(row):
                pkd = row.get(pkd_col, "")
                form = row.get(form_col, "")
                return self.calculate_tax_benefit(pkd, form)

            tax_data = df_enriched.apply(calc_tax, axis=1)
            # Renamed: Annual_Tax_Saving -> Potential_Savings_PLN (as per spec)
            df_enriched['Potential_Savings_PLN'] = tax_data.apply(lambda x: x['annual_tax_saving'])
            df_enriched['tax_benefit_total_first_year'] = tax_data.apply(lambda x: x['total_first_year'])
            df_enriched['naszeauto_subsidy'] = tax_data.apply(lambda x: x['naszeauto_subsidy'])
        elif pkd_col:
            # Fallback if only PKD available
            def calc_tax_pkd_only(row):
                pkd = row.get(pkd_col, "")
                return self.calculate_tax_benefit(pkd, "UNKNOWN")

            tax_data = df_enriched.apply(calc_tax_pkd_only, axis=1)
            df_enriched['Potential_Savings_PLN'] = tax_data.apply(lambda x: x['annual_tax_saving'])
            df_enriched['tax_benefit_total_first_year'] = tax_data.apply(lambda x: x['total_first_year'])
            df_enriched['naszeauto_subsidy'] = tax_data.apply(lambda x: x['naszeauto_subsidy'])
            logger.warning("[GOTHAM-PALANTIR] Legal form not found - using PKD-only tax calculation")
        else:
            df_enriched['Potential_Savings_PLN'] = 0.0
            df_enriched['tax_benefit_total_first_year'] = 0.0
            df_enriched['naszeauto_subsidy'] = 0.0
            logger.warning("[GOTHAM-PALANTIR] PKD or legal form column not found - using default tax benefits")

        # === LAYER 4: LEASING CYCLE ===
        logger.info("[GOTHAM-PALANTIR] Layer 4: Leasing Cycle analysis...")

        if date_col:
            cycle_data = df_enriched[date_col].apply(self.calculate_leasing_cycle)
            df_enriched['company_age_years'] = cycle_data.apply(lambda x: x['age_years'])
            df_enriched['leasing_cycle'] = cycle_data.apply(lambda x: x['cycle'])
            df_enriched['leasing_propensity'] = cycle_data.apply(lambda x: x['propensity'])
        else:
            df_enriched['company_age_years'] = 0.0
            df_enriched['leasing_cycle'] = "UNKNOWN"
            df_enriched['leasing_propensity'] = 0.0
            logger.warning("[GOTHAM-PALANTIR] Start date column not found - using default leasing cycle")

        # === SUMMARY STATISTICS ===
        avg_wealth = df_enriched['wealth_score'].mean()
        avg_m2 = df_enriched['m2_price_estimated'].mean()
        high_wealth_count = len(df_enriched[df_enriched['wealth_score'] >= 8])

        logger.info(f"[GOTHAM-PALANTIR] Processing complete:")
        logger.info(f"  - {len(df_enriched)} rows enriched")
        logger.info(f"  - Avg wealth score: {avg_wealth:.2f}/10")
        logger.info(f"  - Avg estimated m² price: {avg_m2:,.0f} PLN")
        logger.info(f"  - High-wealth leads (score >= 8): {high_wealth_count} ({high_wealth_count/len(df_enriched)*100:.1f}%)")

        return df_enriched

    @staticmethod
    def _find_column(df: pd.DataFrame, possible_names: list) -> Optional[str]:
        """Find first matching column name (case-insensitive)."""
        df_cols_lower = {col.lower(): col for col in df.columns}
        for name in possible_names:
            if name in df.columns:
                return name
            if name.lower() in df_cols_lower:
                return df_cols_lower[name.lower()]
        return None


# === CLI TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("GOTHAM ENGINE - Palantir-Level Intelligence Test")
    print("=" * 60 + "\n")

    # Test data with various scenarios
    test_data = {
        'kod_pocztowy_clean': ['00-001', '40-001', '44-100', '42-200', '41-200', '81-800'],
        'miasto': ['Warszawa', None, 'Gliwice', None, 'Sosnowiec', 'Sopot'],
        'ulica': ['Nowy Świat 15', 'ul. Chorzowska 50', 'Centrum 1', 'Zwykła 10', 'Rynek 5', 'Bohaterów Monte Cassino'],
        'pkd_clean': ['6910Z', '6201Z', '4941Z', '7022Z', '4711Z', '8621Z'],
        'legal_form_clean': ['SPÓŁKA Z O.O.', 'JEDNOOSOBOWA DZIAŁALNOŚĆ', 'SPÓŁKA Z O.O.', 'SPÓŁKA KOMANDYTOWA', 'JEDNOOSOBOWA DZIAŁALNOŚĆ', 'SPÓŁKA Z O.O.'],
        'data_rozpoczecia': [date(2019, 3, 15), date(2015, 8, 20), date(2023, 1, 10), date(2018, 6, 1), date(2021, 5, 1), date(2017, 2, 14)],
    }

    df_test = pd.DataFrame(test_data)

    print("📊 Input data:")
    print(df_test[['kod_pocztowy_clean', 'miasto', 'pkd_clean']])
    print()

    # Process through Gotham with Palantir intelligence
    gotham = GothamEngine()
    df_result = gotham.process(df_test)

    print("\n📈 Wealth Layer (M²-Based Scoring):")
    wealth_cols = ['resolved_city', 'wealth_score', 'wealth_tier', 'm2_price_estimated', 'wealth_signal']
    print(df_result[wealth_cols].to_string(max_colwidth=50))
    print()

    print("🔋 Charger & Tax Layer:")
    infra_cols = ['charger_distance_km', 'Potential_Savings_PLN', 'leasing_cycle']
    print(df_result[infra_cols])
    print()

    print("📊 Data Source Distribution:")
    print(df_result['wealth_data_source'].value_counts())
    print()

    # Demonstrate Palantir correlations
    print("\n🎯 Palantir Correlation Examples:")
    print("-" * 50)

    # Test PKD-only fallback
    pkd_test = gotham.get_wealth_score(postal_code="", pkd_code="6910Z")
    print(f"Prawnik bez lokalizacji: score={pkd_test['wealth_score']}, signal='{pkd_test['wealth_signal']}'")

    # Test premium street detection
    street_test = gotham.get_wealth_score(postal_code="", street="ul. Nowy Świat 15, Warszawa")
    print(f"Ulica prestiżowa: score={street_test['wealth_score']}, signal='{street_test['wealth_signal']}'")

    # Test full correlation
    full_test = gotham.get_wealth_score(postal_code="00-001", city="Warszawa", street="Ujazdowskie 10", pkd_code="6910Z")
    print(f"Pełne dane (Warszawa/Prawnik): score={full_test['wealth_score']}, signal='{full_test['wealth_signal']}'")

    print("\n" + "=" * 60)
    print("✅ GOTHAM-PALANTIR Engine Test Complete!")
    print("=" * 60)
