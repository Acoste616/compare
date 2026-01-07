"""
ASSET SNIPER - Gotham Engine Module
Warstwy danych: Wealth Proxy, Charger Infrastructure, Tax Engine, Leasing Cycle

Gotham Layers:
1. Wealth Proxy - zamożność regionu (kod pocztowy)
2. Charger Infrastructure - najbliższa ładowarka
3. Tax Engine - korzyści podatkowe EV vs ICE
4. Leasing Cycle - cykl wymiany samochodu (wiek firmy)

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import pandas as pd
import math
from typing import Tuple, Dict, Optional
from datetime import date
import logging

from .config import (
    WEALTH_PROXY_SILESIA,
    CHARGER_LOCATIONS,
    TAX_BENEFITS,
    LEASING_CYCLE_MAP,
)

logger = logging.getLogger(__name__)


class GothamEngine:
    """
    Data enrichment engine with market intelligence layers.

    Layers:
    1. Wealth Proxy - Region wealth estimation
    2. Charger Infrastructure - Distance to nearest charger
    3. Tax Engine - EV tax benefits calculation
    4. Leasing Cycle - Company age -> lease renewal probability
    """

    def __init__(self, use_live_api: bool = False):
        """
        Initialize Gotham Engine.

        Args:
            use_live_api: If True, use live APIs (OpenChargeMap, etc.)
                         If False, use static data only
        """
        self.use_live_api = use_live_api
        logger.info(f"[GOTHAM] Initialized (live_api={use_live_api})")

    # === LAYER 1: WEALTH PROXY ===

    @staticmethod
    def get_wealth_score(postal_code: str) -> Tuple[int, str]:
        """
        Get wealth score from postal code.

        Args:
            postal_code: Polish postal code (XX-XXX format)

        Returns:
            Tuple of (wealth_score 1-10, wealth_tier name)
        """
        if not postal_code or len(postal_code) < 6:
            return WEALTH_PROXY_SILESIA["DEFAULT"]

        # Lookup by full postal code first
        if postal_code in WEALTH_PROXY_SILESIA:
            return WEALTH_PROXY_SILESIA[postal_code]

        # Fallback to prefix (first 2 digits)
        prefix = postal_code[:2]
        for key, value in WEALTH_PROXY_SILESIA.items():
            if key.startswith(prefix) and key != "DEFAULT":
                return value

        return WEALTH_PROXY_SILESIA["DEFAULT"]

    # === LAYER 2: CHARGER INFRASTRUCTURE ===

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
        Get approximate coordinates for postal code (simplified mapping).

        NOTE: In production, use geocoding API or postal code database.

        Args:
            postal_code: Polish postal code

        Returns:
            Tuple of (latitude, longitude) or None
        """
        # Simplified mapping for major cities (first 2 digits)
        postal_coords = {
            "40": (50.2649, 19.0238),  # Katowice
            "41": (50.3484, 18.9152),  # Bytom
            "42": (50.8118, 19.1203),  # Częstochowa
            "43": (49.8224, 19.0444),  # Bielsko-Biała / Tychy
            "44": (50.2945, 18.6714),  # Gliwice
        }

        prefix = postal_code[:2] if postal_code else ""
        return postal_coords.get(prefix)

    def calculate_charger_distance(self, postal_code: str) -> float:
        """
        Calculate distance to nearest EV charger.

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

        # Find nearest charger
        min_distance = float('inf')
        for charger in CHARGER_LOCATIONS:
            distance = self._haversine_distance(lat, lon, charger["lat"], charger["lon"])
            if distance < min_distance:
                min_distance = distance

        return round(min_distance, 1)

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

    # === MAIN PROCESSING METHOD ===

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process DataFrame through all Gotham layers.

        Adds columns:
        - wealth_score (int 1-10)
        - wealth_tier (str: PREMIUM/HIGH/MEDIUM/STANDARD/LOW)
        - charger_distance_km (float)
        - tax_benefit_annual (float)
        - tax_benefit_total_first_year (float)
        - leasing_cycle (str)
        - leasing_propensity (float 0-1)

        Args:
            df: DataFrame with cleaned data from LeadRefinery

        Returns:
            Enriched DataFrame
        """
        logger.info(f"[GOTHAM] Processing {len(df)} rows...")

        df_enriched = df.copy()

        # Find relevant columns
        postal_col = self._find_column(df_enriched, ['kod_pocztowy_clean', 'KodPocztowy', 'zip_code'])
        pkd_col = self._find_column(df_enriched, ['pkd_clean', 'PkdGlowny', 'pkd', 'GlownyKodPkd'])
        form_col = self._find_column(df_enriched, ['legal_form_clean', 'FormaPrawna', 'legal_form'])
        date_col = self._find_column(df_enriched, ['data_rozpoczecia', 'DataRozpoczeciaDzialalnosci', 'start_date'])

        # Layer 1: Wealth Proxy
        if postal_col:
            wealth_data = df_enriched[postal_col].apply(self.get_wealth_score)
            df_enriched['wealth_score'] = wealth_data.apply(lambda x: x[0])
            df_enriched['wealth_tier'] = wealth_data.apply(lambda x: x[1])
        else:
            df_enriched['wealth_score'] = 5
            df_enriched['wealth_tier'] = "STANDARD"
            logger.warning("[GOTHAM] Postal code column not found - using default wealth")

        # Layer 2: Charger Infrastructure
        if postal_col:
            df_enriched['charger_distance_km'] = df_enriched[postal_col].apply(self.calculate_charger_distance)
        else:
            df_enriched['charger_distance_km'] = 0.0
            logger.warning("[GOTHAM] Postal code column not found - cannot calculate charger distance")

        # Layer 3: Tax Engine
        if pkd_col and form_col:
            def calc_tax(row):
                pkd = row.get(pkd_col, "")
                form = row.get(form_col, "")
                return self.calculate_tax_benefit(pkd, form)

            tax_data = df_enriched.apply(calc_tax, axis=1)
            df_enriched['tax_benefit_annual'] = tax_data.apply(lambda x: x['annual_tax_saving'])
            df_enriched['tax_benefit_total_first_year'] = tax_data.apply(lambda x: x['total_first_year'])
            df_enriched['naszeauto_subsidy'] = tax_data.apply(lambda x: x['naszeauto_subsidy'])
        else:
            df_enriched['tax_benefit_annual'] = 0.0
            df_enriched['tax_benefit_total_first_year'] = 0.0
            df_enriched['naszeauto_subsidy'] = 0.0
            logger.warning("[GOTHAM] PKD or legal form column not found - using default tax benefits")

        # Layer 4: Leasing Cycle
        if date_col:
            cycle_data = df_enriched[date_col].apply(self.calculate_leasing_cycle)
            df_enriched['company_age_years'] = cycle_data.apply(lambda x: x['age_years'])
            df_enriched['leasing_cycle'] = cycle_data.apply(lambda x: x['cycle'])
            df_enriched['leasing_propensity'] = cycle_data.apply(lambda x: x['propensity'])
        else:
            df_enriched['company_age_years'] = 0.0
            df_enriched['leasing_cycle'] = "UNKNOWN"
            df_enriched['leasing_propensity'] = 0.0
            logger.warning("[GOTHAM] Start date column not found - using default leasing cycle")

        logger.info(f"[GOTHAM] Processing complete. {len(df_enriched)} rows enriched.")
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
    print("=== Gotham Engine Test ===\n")

    # Test data
    test_data = {
        'kod_pocztowy_clean': ['40-001', '44-100', '42-200', '43-100'],
        'pkd_clean': ['6910Z', '6201Z', '4941Z', '7022Z'],
        'legal_form_clean': ['SPÓŁKA Z O.O.', 'JEDNOOSOBOWA DZIAŁALNOŚĆ', 'SPÓŁKA Z O.O.', 'SPÓŁKA KOMANDYTOWA'],
        'data_rozpoczecia': [date(2019, 3, 15), date(2015, 8, 20), date(2023, 1, 10), date(2018, 6, 1)],
    }

    df_test = pd.DataFrame(test_data)

    print("Input data:")
    print(df_test)
    print()

    # Process through Gotham
    gotham = GothamEngine()
    df_result = gotham.process(df_test)

    print("Enriched data:")
    gotham_cols = ['wealth_score', 'wealth_tier', 'charger_distance_km', 'tax_benefit_annual', 'leasing_cycle', 'leasing_propensity']
    print(df_result[gotham_cols])
    print()

    print("✅ Gotham Engine Test Complete!")
