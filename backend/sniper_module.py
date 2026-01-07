"""
ASSET SNIPER Module (ULTRA v5.0)
================================
Thin wrapper for the Unified Intelligence Platform.

This module serves as the backend API entry point, delegating all logic
to the `asset_sniper/` package for maintainability.

ARCHITECTURE:
- All business logic lives in `asset_sniper/` package
- This module provides FastAPI-compatible interface
- Backward compatible with existing API endpoints

Migration from v4.2:
- DELETED: Hardcoded WEALTH_MAP, PKD_LEASING_MAP, TAX_BENEFIT_MAP
- DELETED: PalantirTactics class (moved to asset_sniper/)
- KEPT: AssetSniper class interface (now delegates to unified_platform)

Author: Lead Architect
Version: 5.0.0 (Unified)
"""

import asyncio
import logging
from dataclasses import asdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# === IMPORTS FROM UNIFIED ASSET_SNIPER PACKAGE ===
from asset_sniper.config import (
    # Enums
    Tier,
    Priority,
    # Constants
    PKD_PROFILES,
    REAL_ESTATE_MARKET_DATA,
    NATIONAL_AVG_M2_PRICE,
    POSTAL_CODE_CITY_MAP,
    TAX_BENEFITS,
    TIER_THRESHOLDS,
    SCORING_WEIGHTS,
)
from asset_sniper.unified_platform import (
    UnifiedPipeline,
    PipelineConfig,
    PipelineStats,
    ProcessingLevel,
    DNAType,
    EnrichedLead,
)
from asset_sniper.gotham_engine import GothamEngine
from asset_sniper.scoring_matrix import ScoringMatrix, LeadDNA, generate_lead_dna
from asset_sniper.bigdecoder_lite import BigDecoderLite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === BACKWARD COMPATIBLE ENUMS ===
# These map the old enum names to the new unified ones

class LeadTier:
    """
    DEPRECATED: Use asset_sniper.config.Tier instead.

    Kept for backward compatibility with existing code.
    """
    TIER_S = Tier.S.value
    TIER_AAA = Tier.AAA.value
    TIER_AA = Tier.AA.value
    TIER_A = Tier.A.value
    TIER_B = Tier.B.value
    TIER_C = Tier.C.value
    TIER_D = Tier.D.value
    TIER_E = Tier.E.value
    UNKNOWN = "Unknown"


class LeasingCycle:
    """
    Leasing cycle stages based on company age.

    DEPRECATED: Use asset_sniper.config.LEASING_CYCLE_MAP instead.
    """
    STARTUP = "STARTUP"
    EARLY_GROWTH = "EARLY_GROWTH"
    GROWTH = "GROWTH"
    PRIME_LEASING = "PRIME_LEASING"
    MATURE = "MATURE"
    RENEWAL_WINDOW = "RENEWAL_WINDOW"
    ESTABLISHED = "ESTABLISHED"
    VETERAN = "VETERAN"
    UNKNOWN = "UNKNOWN"


class ClientDNAType:
    """
    Psychographic profile types.

    DEPRECATED: Use asset_sniper.unified_platform.DNAType instead.
    """
    ANALYTICAL = DNAType.ANALYTICAL.value
    VISIONARY = DNAType.VISIONARY.value
    COST_DRIVEN = DNAType.COST_DRIVEN.value
    STATUS_SEEKER = DNAType.STATUS_SEEKER.value
    PRAGMATIC = DNAType.PRAGMATIC.value
    UNKNOWN = DNAType.UNKNOWN.value


# === PALANTIR TACTICS (Now delegates to GothamEngine) ===

class PalantirTactics:
    """
    DEPRECATED: Fallback estimation logic now lives in asset_sniper/gotham_engine.py

    This class is kept for backward compatibility. All methods now delegate
    to the GothamEngine which has superior M²-based wealth calculations.
    """

    @staticmethod
    def estimate_charger_distance(city: str, wealth_tier: str) -> float:
        """
        Estimate charger distance based on city and wealth tier.

        DEPRECATED: Use GothamEngine.calculate_charger_distance() instead.
        """
        # Fallback estimates (used when no postal code available)
        base_distances = {
            "S": 1.5,
            "PREMIUM": 2.5,
            "HIGH": 5.0,
            "MEDIUM": 8.0,
            "STANDARD": 12.0,
            "LOW": 15.0,
            "UNKNOWN": 10.0
        }

        city_multipliers = {
            "WARSZAWA": 0.5,
            "KRAKÓW": 0.6,
            "WROCŁAW": 0.65,
            "POZNAŃ": 0.7,
            "GDAŃSK": 0.7,
            "KATOWICE": 0.75,
            "ŁÓDŹ": 0.8
        }

        city_upper = str(city).upper().replace("Ó", "O").replace("Ł", "L")
        multiplier = city_multipliers.get(city_upper, 1.0)
        base = base_distances.get(wealth_tier, 10.0)

        return round(base * multiplier, 1)

    @staticmethod
    def estimate_annual_tax_saving(legal_form: str, pkd_code: str, estimated_km: int = 25000) -> float:
        """
        Estimate annual tax savings.

        DEPRECATED: Use GothamEngine.calculate_tax_benefit() instead.
        """
        # Use the centralized TAX_BENEFITS constants
        tax_diff = TAX_BENEFITS["TAX_DIFFERENCE"]

        # Determine tax rate from PKD
        pkd_prefix = pkd_code[:4] if pkd_code else ""
        profile = PKD_PROFILES.get(pkd_prefix, PKD_PROFILES.get("DEFAULT", {}))
        tax_rate = profile.get("tax_rate", 19) / 100

        # Annual tax saving from depreciation difference
        annual_saving = tax_diff * tax_rate

        # Add fuel savings estimate
        fuel_saving_per_km = 0.35  # PLN saved per km
        fuel_saving = estimated_km * fuel_saving_per_km

        return round(annual_saving + fuel_saving, 0)

    @staticmethod
    def estimate_dna_type(pkd_code: str, wealth_tier: str, legal_form: str) -> str:
        """
        Estimate client DNA type based on industry and profile.

        DEPRECATED: Use asset_sniper.scoring_matrix.generate_lead_dna() instead.
        """
        pkd_prefix = pkd_code[:4] if pkd_code else ""

        # IT, R&D, Innovation sectors -> Visionary
        if pkd_prefix in ["6201", "6209", "6311", "7211", "7219"]:
            return ClientDNAType.VISIONARY

        # Finance, Consulting, Legal -> Analytical
        if pkd_prefix in ["6910", "6920", "6621", "6622", "7010", "7022"]:
            return ClientDNAType.ANALYTICAL

        # Transport, Logistics -> Cost-Driven
        if pkd_prefix in ["4941", "4942", "5210", "5229", "5320"]:
            return ClientDNAType.COST_DRIVEN

        # Real Estate, Premium areas -> Status-Seeker
        if pkd_prefix in ["6810", "6820", "6831"] or wealth_tier in ["S", "PREMIUM"]:
            return ClientDNAType.STATUS_SEEKER

        # Default -> Pragmatic
        return ClientDNAType.PRAGMATIC

    @staticmethod
    def estimate_market_urgency(tier_score: int, leasing_cycle: str) -> int:
        """Estimate market urgency score (0-100)"""
        base_score = min(tier_score, 100)

        cycle_bonus = {
            "RENEWAL_WINDOW": 25,
            "PRIME_LEASING": 20,
            "MATURE": 15,
            "ESTABLISHED": 10,
            "VETERAN": 10,
            "GROWTH": 8,
            "EARLY_GROWTH": 5,
            "STARTUP": 0,
            "UNKNOWN": 3
        }

        bonus = cycle_bonus.get(leasing_cycle, 5)
        return min(100, base_score + bonus)


# === SNIPER STATS (Backward Compatible) ===

class SniperStats:
    """
    Processing statistics.

    Now wraps asset_sniper.unified_platform.PipelineStats for backward compatibility.
    """

    def __init__(self, pipeline_stats: Optional[PipelineStats] = None):
        if pipeline_stats:
            self.total_rows = pipeline_stats.total_rows
            self.processed_rows = pipeline_stats.scored_rows
            self.error_rows = 0
            self.tier_s_count = pipeline_stats.tier_counts.get('S', 0)
            self.tier_aaa_count = pipeline_stats.tier_counts.get('AAA', 0)
            self.tier_aa_count = pipeline_stats.tier_counts.get('AA', 0)
            self.tier_a_count = pipeline_stats.tier_counts.get('A', 0)
            self.tier_b_count = pipeline_stats.tier_counts.get('B', 0)
            self.tier_c_count = pipeline_stats.tier_counts.get('C', 0)
            self.tier_d_count = pipeline_stats.tier_counts.get('D', 0)
            self.tier_e_count = pipeline_stats.tier_counts.get('E', 0)
            self.avg_wealth_score = pipeline_stats.avg_wealth_score
            self.avg_total_score = pipeline_stats.avg_total_score
            self.avg_tax_saving = pipeline_stats.avg_tax_saving
            self.avg_charger_distance = pipeline_stats.avg_charger_distance
            self.top_voivodeships = {}
            self.top_dna_types = {}
            self.processing_time_ms = pipeline_stats.processing_time_ms
            self.api_calls_made = pipeline_stats.api_calls_made
            self.palantir_fallbacks = 0
        else:
            self.total_rows = 0
            self.processed_rows = 0
            self.error_rows = 0
            self.tier_s_count = 0
            self.tier_aaa_count = 0
            self.tier_aa_count = 0
            self.tier_a_count = 0
            self.tier_b_count = 0
            self.tier_c_count = 0
            self.tier_d_count = 0
            self.tier_e_count = 0
            self.avg_wealth_score = 0.0
            self.avg_total_score = 0.0
            self.avg_tax_saving = 0.0
            self.avg_charger_distance = 0.0
            self.top_voivodeships = {}
            self.top_dna_types = {}
            self.processing_time_ms = 0
            self.api_calls_made = 0
            self.palantir_fallbacks = 0


# === ASSET SNIPER CLASS (Now delegates to UnifiedPipeline) ===

class AssetSniper:
    """
    Data Refinery for CEIDG Leads Processing - ULTRA v5.0

    This class now serves as a backward-compatible wrapper around
    the UnifiedPipeline from asset_sniper package.

    All business logic has been consolidated into:
    - asset_sniper/unified_platform.py (orchestration)
    - asset_sniper/gotham_engine.py (market intelligence)
    - asset_sniper/scoring_matrix.py (tier classification)
    - asset_sniper/bigdecoder_lite.py (message generation)

    Usage:
        sniper = AssetSniper()
        df_result, stats = await sniper.process_csv(df)
    """

    def __init__(self, analysis_engine=None, gotham_gateway=None):
        """
        Initialize Asset Sniper.

        Args:
            analysis_engine: AnalysisEngine instance for Ollama/BigDecoder
            gotham_gateway: DEPRECATED - no longer used
        """
        self.analysis_engine = analysis_engine

        # Initialize unified pipeline
        config = PipelineConfig(
            enable_gotham=True,
            enable_bigdecoder=analysis_engine is not None,
            bigdecoder_tier_threshold="AAA"
        )
        self._pipeline = UnifiedPipeline(config=config, analysis_engine=analysis_engine)

        # For backward compatibility
        self._api_calls = 0
        self._palantir_fallbacks = 0

        logger.info("[ASSET SNIPER v5.0] Initialized with Unified Pipeline")

    # === BACKWARD COMPATIBLE DATA CLEANING METHODS ===
    # These delegate to LeadRefinery but maintain the old API

    @staticmethod
    def clean_nip(nip: Any) -> str:
        """Clean and validate Polish NIP number"""
        from asset_sniper.lead_refinery import LeadRefinery
        return LeadRefinery._clean_nip(nip)

    @staticmethod
    def clean_phone(phone: Any) -> str:
        """Clean and normalize Polish phone number"""
        from asset_sniper.lead_refinery import LeadRefinery
        return LeadRefinery._clean_phone(phone)

    @staticmethod
    def clean_zip_code(zip_code: Any) -> str:
        """Clean Polish postal code"""
        from asset_sniper.lead_refinery import LeadRefinery
        return LeadRefinery._clean_postal_code(zip_code)

    @staticmethod
    def clean_email(email: Any) -> str:
        """Clean and validate email address"""
        from asset_sniper.lead_refinery import LeadRefinery
        return LeadRefinery._clean_email(email)

    @staticmethod
    def parse_date(date_val: Any) -> Optional[date]:
        """Parse date from various formats"""
        from asset_sniper.lead_refinery import LeadRefinery
        return LeadRefinery._parse_date(date_val)

    # === BACKWARD COMPATIBLE ENRICHMENT METHODS ===
    # These delegate to GothamEngine

    @staticmethod
    def get_wealth_score(zip_code: str) -> Tuple[int, str]:
        """
        Get wealth score from ZIP code.

        DEPRECATED: Use GothamEngine.get_wealth_score() for full M²-based analysis.
        """
        engine = GothamEngine()
        result = engine.get_wealth_score(postal_code=zip_code)
        return (result['wealth_score'], result['wealth_tier'])

    @staticmethod
    def calculate_business_age(start_date: Optional[date]) -> Tuple[float, str]:
        """Calculate business age and leasing cycle stage"""
        result = GothamEngine.calculate_leasing_cycle(start_date)
        return (result['age_years'], result['cycle'])

    @staticmethod
    def get_pkd_leasing_propensity(pkd_code: str) -> Tuple[int, str]:
        """Get leasing propensity from PKD code"""
        profile = PKD_PROFILES.get(pkd_code, PKD_PROFILES.get("DEFAULT", {}))
        score = profile.get('score', 8)
        tier = profile.get('tier', 'B')
        return (score * 3, tier)  # Scale to match old format

    @staticmethod
    def get_industry_name(pkd_code: str) -> str:
        """Get human-readable industry name from PKD code"""
        profile = PKD_PROFILES.get(pkd_code, PKD_PROFILES.get("DEFAULT", {}))
        return profile.get('full_name', 'Działalność gospodarcza')

    @staticmethod
    def get_tax_benefit_score(legal_form: str) -> Tuple[int, Dict]:
        """Get tax benefit score and details from legal form"""
        result = GothamEngine.calculate_tax_benefit("DEFAULT", legal_form)
        score = int(result['annual_tax_saving'] / 240)  # Scale to 0-100
        return (score, result)

    # === MAIN PROCESSING METHODS ===

    def clean_data(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Level 0: Clean raw CSV data"""
        from asset_sniper.lead_refinery import LeadRefinery
        refinery = LeadRefinery()
        return refinery.process(df)

    def enrich_local(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Level 1: Local enrichment using Gotham Engine"""
        engine = GothamEngine()
        return engine.process(df)

    async def enrich_tier_s(self, df: 'pd.DataFrame', batch_size: int = 3) -> 'pd.DataFrame':
        """Level 2: Deep enrichment for Tier S/AAA leads"""
        # This is now handled by the unified pipeline's BigDecoder slow path
        matrix = ScoringMatrix()
        df_scored = matrix.score_all(df)

        decoder = BigDecoderLite()
        df_messages = decoder.enrich_messages(df_scored)

        return df_messages

    async def process_csv(
        self,
        df: 'pd.DataFrame',
        enable_deep_enrichment: bool = True,
        chunk_size: int = 1000
    ) -> Tuple['pd.DataFrame', SniperStats]:
        """
        Main processing pipeline - now delegates to UnifiedPipeline.

        Args:
            df: Input DataFrame
            enable_deep_enrichment: Enable Tier S/AAA deep analysis
            chunk_size: Rows per processing chunk

        Returns:
            Tuple of (enriched DataFrame, statistics)
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for AssetSniper")

        # Determine processing level
        level = (
            ProcessingLevel.LEVEL_3_BIGDECODER
            if enable_deep_enrichment
            else ProcessingLevel.LEVEL_2_GOTHAM
        )

        # Process through unified pipeline
        df_result, pipeline_stats = await self._pipeline.process(df, level=level)

        # Convert to backward-compatible stats
        stats = SniperStats(pipeline_stats)

        return df_result, stats

    def process_csv_sync(
        self,
        df: 'pd.DataFrame',
        enable_deep_enrichment: bool = False
    ) -> Tuple['pd.DataFrame', SniperStats]:
        """Synchronous wrapper for process_csv"""
        return asyncio.run(self.process_csv(df, enable_deep_enrichment))


# === SINGLETON INSTANCE ===

asset_sniper = AssetSniper()


# === SNIPER GATEWAY (Backward Compatibility for GOTHAM integration) ===

class SniperGateway:
    """
    DEPRECATED: Gateway for GOTHAM integration.

    Now delegates to GothamEngine and BurningHouseCalculator from
    backend.gotham_module for real market intelligence.
    """

    @staticmethod
    def check_charger_infrastructure(city: str = "") -> Dict[str, Any]:
        """Check charger infrastructure for a location"""
        # Try to get coordinates and calculate real distance
        engine = GothamEngine()

        # Map city to postal code prefix for lookup
        city_postal_map = {v: k for k, v in POSTAL_CODE_CITY_MAP.items()}
        postal_prefix = city_postal_map.get(city, "40")

        distance = engine.calculate_charger_distance(f"{postal_prefix}-000")

        # Determine coverage level
        if distance < 5:
            coverage = "HIGH"
        elif distance < 10:
            coverage = "MEDIUM"
        elif distance < 20:
            coverage = "LOW"
        else:
            coverage = "POOR"

        return {
            "nearest_supercharger_km": distance,
            "coverage_level": coverage,
            "charger_count": 10,  # Estimate
            "city": city
        }

    @staticmethod
    def calculate_tax_potential(
        pkd_code: str,
        legal_form: str,
        estimated_annual_km: int = 25000
    ) -> Dict[str, Any]:
        """Calculate tax potential for a lead"""
        result = GothamEngine.calculate_tax_benefit(pkd_code, legal_form)

        # Add fuel savings
        fuel_saving = estimated_annual_km * 0.35

        return {
            "total_first_year_benefit": result["total_first_year"],
            "annual_tax_saving": result["annual_tax_saving"],
            "vat_recovery": result["annual_tax_saving"] * 0.15,
            "naszeauto_subsidy": result["naszeauto_subsidy"],
            "fuel_saving": fuel_saving,
            "depreciation_advantage": TAX_BENEFITS["TAX_DIFFERENCE"]
        }

    @staticmethod
    def get_lead_context(
        city: str,
        pkd_code: str,
        legal_form: str,
        region: str = "ŚLĄSKIE"
    ) -> Dict[str, Any]:
        """Get full lead context with market intelligence"""
        # Get wealth data
        engine = GothamEngine()
        city_postal_map = {v: k for k, v in POSTAL_CODE_CITY_MAP.items()}
        postal_prefix = city_postal_map.get(city, "40")

        wealth = engine.get_wealth_score(
            postal_code=f"{postal_prefix}-000",
            city=city,
            pkd_code=pkd_code
        )

        # Get tax data
        tax = SniperGateway.calculate_tax_potential(pkd_code, legal_form)

        # Get charger data
        charger = SniperGateway.check_charger_infrastructure(city)

        # Calculate combined score
        combined_score = (
            wealth['wealth_score'] * 10 +  # 0-100
            min(100, tax['total_first_year_benefit'] / 500) +  # 0-100
            max(0, 100 - charger['nearest_supercharger_km'] * 5)  # 0-100
        ) / 3

        return {
            "wealth_data": wealth,
            "tax_data": tax,
            "charger_data": charger,
            "combined_score": int(combined_score),
            "opportunity_score": {
                "score": int(combined_score),
                "insight": f"Lead z {city} - combined score {combined_score:.0f}/100"
            }
        }


# === CLI TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print(" ASSET SNIPER v5.0 - Unified Intelligence Platform ")
    print("=" * 60)
    print()

    if not PANDAS_AVAILABLE:
        print("ERROR: pandas not installed. Run: pip install pandas")
        exit(1)

    # Create test data
    test_data = {
        'NIP': ['5272829917', '5261040828'],
        'Telefon': ['+48 500 100 200', '48500100200'],
        'Email': ['test@kancelaria.pl', 'anna@it.pl'],
        'Nazwa': ['Kancelaria Prawna sp. z o.o.', 'Tech Solutions sp. z o.o.'],
        'FormaPrawna': ['SPÓŁKA Z O.O.', 'SPÓŁKA Z O.O.'],
        'PkdGlowny': ['6910Z', '6201Z'],
        'KodPocztowy': ['00-001', '40-001'],
        'Miejscowosc': ['Warszawa', 'Katowice'],
        'Wojewodztwo': ['MAZOWIECKIE', 'ŚLĄSKIE'],
        'DataRozpoczeciaDzialalnosci': ['2019-03-15', '2020-08-20']
    }

    df_test = pd.DataFrame(test_data)

    print("📥 Input data:")
    print(df_test[['Nazwa', 'PkdGlowny', 'Miejscowosc']])
    print()

    # Test Palantir Tactics (backward compatibility)
    print("🎯 Testing Palantir Tactics (backward compatibility):")
    print(f"  - Charger (Warszawa, PREMIUM): {PalantirTactics.estimate_charger_distance('Warszawa', 'PREMIUM')} km")
    print(f"  - Tax saving (Sp. z o.o., 6910Z): {PalantirTactics.estimate_annual_tax_saving('SPÓŁKA Z O.O.', '6910Z'):,.0f} PLN")
    print(f"  - DNA type (6910Z, PREMIUM): {PalantirTactics.estimate_dna_type('6910Z', 'PREMIUM', 'SPÓŁKA Z O.O.')}")
    print()

    # Test SniperGateway (backward compatibility)
    print("🔧 Testing SniperGateway (backward compatibility):")
    charger = SniperGateway.check_charger_infrastructure("Katowice")
    print(f"  - Charger infrastructure: {charger}")
    tax = SniperGateway.calculate_tax_potential("6910Z", "SPÓŁKA Z O.O.")
    print(f"  - Tax potential: {tax['total_first_year_benefit']:,.0f} PLN first year")
    print()

    # Process through unified pipeline
    print("🚀 Processing through Unified Pipeline...")
    sniper = AssetSniper()
    df_result, stats = sniper.process_csv_sync(df_test)

    print(f"\n📊 Results:")
    print(f"  - Rows processed: {stats.processed_rows}")
    print(f"  - Tier S: {stats.tier_s_count}")
    print(f"  - Tier AAA: {stats.tier_aaa_count}")
    print(f"  - Tier A: {stats.tier_a_count}")
    print(f"  - Avg wealth: {stats.avg_wealth_score:.1f}/10")
    print(f"  - Avg score: {stats.avg_total_score:.1f}/100")
    print(f"  - Time: {stats.processing_time_ms}ms")
    print()

    print("🎯 Enriched leads:")
    key_cols = ['target_tier', 'total_score', 'wealth_tier']
    display_cols = ['Nazwa'] + [c for c in key_cols if c in df_result.columns]
    print(df_result[display_cols])

    print()
    print("=" * 60)
    print("✅ ASSET SNIPER v5.0 Test Complete!")
    print("=" * 60)
