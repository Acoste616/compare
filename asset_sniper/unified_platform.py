"""
UNIFIED INTELLIGENCE PLATFORM v5.0
=====================================
The Single Entry Point for the Industrial Lead Refinery & Cognitive Analysis Suite.

This module orchestrates:
- LEAD FACTORY (The Orchestrator) - Mass CSV processing
- GOTHAM ENGINE (The Data Refinery) - Hard financial data enrichment
- BIGDECODER (The Cognitive Brain) - Psychological profiling

Architecture:
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   RAW CSV       │ ──▶ │  LEAD FACTORY   │ ──▶ │  ENRICHED CSV   │
│   (100k+ rows)  │     │  (4 Stages)     │     │  (Tier S-E)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  GOTHAM  │ │ SCORING  │ │BIGDECODER│
              │  ENGINE  │ │  MATRIX  │ │  (FAST/  │
              │ (Wealth, │ │ (5-factor│ │   SLOW)  │
              │  Tax,    │ │  0-100)  │ │          │
              │  Charger)│ │          │ │          │
              └──────────┘ └──────────┘ └──────────┘

Author: BigDInc Team
Version: 5.0.0 (Unified)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# === LOCAL IMPORTS (Consolidated) ===
from .config import (
    BATCH_CONFIG,
    NATIONAL_AVG_M2_PRICE,
    OUTPUT_COLUMNS_DNA,
    OUTPUT_COLUMNS_FINANCIAL,
    OUTPUT_COLUMNS_REQUIRED,
    OUTPUT_COLUMNS_WEALTH,
    PKD_PROFILES,
    Priority,
    REAL_ESTATE_MARKET_DATA,
    SCORING_WEIGHTS,
    TAX_BENEFITS,
    TIER_THRESHOLDS,
    Tier,
)
from .gotham_engine import GothamEngine
from .lead_refinery import LeadRefinery
from .scoring_matrix import ScoringMatrix, generate_lead_dna
from .bigdecoder_lite import BigDecoderLite

logger = logging.getLogger(__name__)


# === ENUMS ===

class ProcessingLevel(str, Enum):
    """Level of enrichment to apply"""
    LEVEL_0_CLEAN = "clean"           # Just data cleaning
    LEVEL_1_LOCAL = "local"           # Local enrichment (free, instant)
    LEVEL_2_GOTHAM = "gotham"         # Full Gotham layers (API calls)
    LEVEL_3_BIGDECODER = "bigdecoder" # Full AI profiling (Ollama)


class DNAType(str, Enum):
    """Client DNA psychographic types"""
    ANALYTICAL = "Analytical"
    VISIONARY = "Visionary"
    COST_DRIVEN = "Cost-Driven"
    STATUS_SEEKER = "Status-Seeker"
    PRAGMATIC = "Pragmatic"
    UNKNOWN = "Unknown"


# === DATA CLASSES ===

@dataclass
class PipelineConfig:
    """Configuration for the unified pipeline"""
    # Processing levels
    enable_gotham: bool = True
    enable_bigdecoder: bool = True
    bigdecoder_tier_threshold: str = "AAA"  # S, AAA = slow path; AA+ = fast path only

    # Performance settings
    chunk_size: int = 10_000
    parallel_workers: int = 4
    api_rate_limit: int = 100  # calls per minute

    # Output settings
    output_tiers: List[str] = field(default_factory=lambda: ["S", "AAA", "AA", "A"])
    include_dna_columns: bool = True
    include_wealth_columns: bool = True
    include_financial_columns: bool = True


@dataclass
class PipelineStats:
    """Statistics from pipeline execution"""
    # Input
    total_rows: int = 0

    # Processing
    cleaned_rows: int = 0
    enriched_rows: int = 0
    scored_rows: int = 0
    dna_profiles_generated: int = 0

    # Tier distribution
    tier_counts: Dict[str, int] = field(default_factory=dict)

    # Quality metrics
    avg_wealth_score: float = 0.0
    avg_total_score: float = 0.0
    avg_charger_distance: float = 0.0
    avg_tax_saving: float = 0.0

    # Performance
    processing_time_ms: int = 0
    api_calls_made: int = 0

    # Top insights
    top_pkd_industries: Dict[str, int] = field(default_factory=dict)
    top_cities: Dict[str, int] = field(default_factory=dict)


@dataclass
class EnrichedLead:
    """Complete enriched lead with all intelligence layers"""
    # === Identity ===
    nip: str = ""
    company_name: str = ""
    first_name: str = ""
    last_name: str = ""

    # === Contact ===
    phone: str = ""
    email: str = ""

    # === Location ===
    city: str = ""
    postal_code: str = ""
    voivodeship: str = ""

    # === Business ===
    pkd_code: str = ""
    legal_form: str = ""
    start_date: Optional[datetime] = None
    company_age_years: float = 0.0

    # === GOTHAM Layer 1: Wealth Proxy ===
    wealth_score: int = 5
    wealth_tier: str = "STANDARD"
    wealth_signal: str = ""
    m2_price_estimated: float = 0.0

    # === GOTHAM Layer 2: Charger Infrastructure ===
    charger_distance_km: float = 0.0
    charger_coverage: str = "UNKNOWN"

    # === GOTHAM Layer 3: Tax Engine ===
    potential_savings_pln: float = 0.0
    tax_benefit_first_year: float = 0.0
    naszeauto_subsidy: float = 27_000.0

    # === GOTHAM Layer 4: Leasing Cycle ===
    leasing_cycle: str = "UNKNOWN"
    leasing_propensity: float = 0.0

    # === Scoring Matrix ===
    total_score: int = 0
    target_tier: str = "E"
    priority: str = "ARCHIWUM"
    next_action: str = "Ignoruj"

    # === BigDecoder DNA ===
    lead_type: str = ""
    decision_driver: str = ""
    dna_type: str = DNAType.UNKNOWN.value
    best_hook: str = ""
    objection_killer: str = ""
    closing_trigger: str = ""

    # === Generated Content ===
    sniper_hook: str = ""
    tax_weapon: str = ""
    lead_description: str = ""
    gotham_insight: str = ""

    # === Metadata ===
    enrichment_level: ProcessingLevel = ProcessingLevel.LEVEL_0_CLEAN
    data_source: str = "local"
    processing_errors: List[str] = field(default_factory=list)


# === UNIFIED PIPELINE ===

class UnifiedPipeline:
    """
    UNIFIED INTELLIGENCE PLATFORM

    The single orchestrator for the Industrial Lead Refinery.
    Consolidates GOTHAM ENGINE + BIGDECODER + SCORING MATRIX.

    Pipeline Stages:
    1. INGESTOR  - Clean dirty CSV data
    2. GOTHAM    - Enrich with market intelligence
    3. SCORING   - Classify into Tier S-E
    4. BIGDECODER- Generate psychological profiles and hooks

    Usage:
        pipeline = UnifiedPipeline()
        df_result, stats = await pipeline.process(df_input)
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        analysis_engine=None  # Optional Ollama/AnalysisEngine for slow path
    ):
        """
        Initialize Unified Pipeline.

        Args:
            config: Pipeline configuration
            analysis_engine: AnalysisEngine instance for BigDecoder slow path
        """
        self.config = config or PipelineConfig()
        self.analysis_engine = analysis_engine

        # Initialize sub-modules
        self.lead_refinery = LeadRefinery()
        self.gotham_engine = GothamEngine()
        self.scoring_matrix = ScoringMatrix()
        self.bigdecoder_lite = BigDecoderLite()

        # Statistics
        self._api_calls = 0

        logger.info("[UNIFIED PIPELINE] Initialized with Palantir-level intelligence")

    # === MAIN PIPELINE ===

    async def process(
        self,
        df: pd.DataFrame,
        level: ProcessingLevel = ProcessingLevel.LEVEL_3_BIGDECODER
    ) -> Tuple[pd.DataFrame, PipelineStats]:
        """
        Process DataFrame through the unified intelligence pipeline.

        Args:
            df: Input DataFrame with raw lead data
            level: Processing level (CLEAN, LOCAL, GOTHAM, BIGDECODER)

        Returns:
            Tuple of (enriched DataFrame, processing statistics)
        """
        import time
        start_time = time.time()

        stats = PipelineStats(total_rows=len(df))

        logger.info(f"[UNIFIED PIPELINE] Starting Level {level.value} processing for {len(df)} rows")

        # === STAGE 1: INGESTOR (Data Cleaning) ===
        logger.info("[STAGE 1] Running Lead Refinery (data cleaning)...")
        df_clean = self.lead_refinery.process(df)
        stats.cleaned_rows = len(df_clean)

        if level == ProcessingLevel.LEVEL_0_CLEAN:
            stats.processing_time_ms = int((time.time() - start_time) * 1000)
            return df_clean, stats

        # === STAGE 2: GOTHAM ENGINE (Market Intelligence) ===
        logger.info("[STAGE 2] Running Gotham Engine (market intelligence)...")
        df_enriched = self.gotham_engine.process(df_clean)
        stats.enriched_rows = len(df_enriched)

        if level == ProcessingLevel.LEVEL_1_LOCAL:
            stats.processing_time_ms = int((time.time() - start_time) * 1000)
            return df_enriched, stats

        # === STAGE 3: SCORING MATRIX (Tier Classification) ===
        logger.info("[STAGE 3] Running Scoring Matrix (tier classification)...")
        df_scored = self.scoring_matrix.score_all(df_enriched)
        stats.scored_rows = len(df_scored)

        # Calculate tier distribution
        stats.tier_counts = df_scored['target_tier'].value_counts().to_dict()

        if level == ProcessingLevel.LEVEL_2_GOTHAM:
            stats.processing_time_ms = int((time.time() - start_time) * 1000)
            self._calculate_stats(df_scored, stats)
            return df_scored, stats

        # === STAGE 4: BIGDECODER (Psychological Profiling) ===
        logger.info("[STAGE 4] Running BigDecoder (cognitive analysis)...")

        # Fast Path: Template-based messages for all high-value leads
        df_final = self.bigdecoder_lite.enrich_messages(df_scored)

        # Slow Path: AI profiling for Tier S/AAA (if analysis_engine available)
        if self.analysis_engine and self.config.enable_bigdecoder:
            df_final = await self._run_bigdecoder_slow_path(df_final)

        # Count DNA profiles
        stats.dna_profiles_generated = len(df_final[df_final['lead_type'] != ''])

        # Calculate final stats
        self._calculate_stats(df_final, stats)
        stats.processing_time_ms = int((time.time() - start_time) * 1000)
        stats.api_calls_made = self._api_calls

        logger.info(f"[UNIFIED PIPELINE] Complete in {stats.processing_time_ms}ms")
        logger.info(f"[UNIFIED PIPELINE] Tier S={stats.tier_counts.get('S', 0)}, "
                   f"AAA={stats.tier_counts.get('AAA', 0)}, "
                   f"DNA profiles={stats.dna_profiles_generated}")

        return df_final, stats

    def process_sync(
        self,
        df: pd.DataFrame,
        level: ProcessingLevel = ProcessingLevel.LEVEL_2_GOTHAM
    ) -> Tuple[pd.DataFrame, PipelineStats]:
        """
        Synchronous wrapper for process() - skips slow path.

        Use this for quick local processing without AI enrichment.
        """
        return asyncio.run(self.process(df, level=level))

    # === INTERNAL METHODS ===

    async def _run_bigdecoder_slow_path(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run BigDecoder slow path (Ollama AI) for Tier S/AAA leads.

        This generates:
        - Full psychological profile (M1-M7 modules)
        - AI-generated sniper hooks
        - Strategic questions and responses
        """
        # Determine which tiers get slow path
        threshold_tiers = {
            "S": ["S"],
            "AAA": ["S", "AAA"],
            "AA": ["S", "AAA", "AA"],
        }
        target_tiers = threshold_tiers.get(
            self.config.bigdecoder_tier_threshold,
            ["S", "AAA"]
        )

        # Filter to target tiers
        tier_mask = df['target_tier'].isin(target_tiers)
        target_indices = df[tier_mask].index.tolist()

        if not target_indices:
            logger.info("[BIGDECODER SLOW] No Tier S/AAA leads for deep analysis")
            return df

        logger.info(f"[BIGDECODER SLOW] Running deep analysis for {len(target_indices)} leads")

        # Process in small batches to avoid overloading Ollama
        batch_size = 3
        for i in range(0, len(target_indices), batch_size):
            batch_indices = target_indices[i:i + batch_size]

            for idx in batch_indices:
                row = df.loc[idx]

                try:
                    # Build context for AI
                    context = self._build_lead_context(row)

                    # Call analysis engine (if available)
                    if self.analysis_engine:
                        self._api_calls += 1

                        # Simulate chat history from lead data
                        chat_history = [
                            {"role": "user", "content": f"Analizuję lead: {context}"}
                        ]

                        analysis = await self.analysis_engine.run_deep_analysis(
                            session_id=f"sniper_{idx}",
                            chat_history=chat_history,
                            language="PL"
                        )

                        # Extract key insights from M1-M7 analysis
                        if analysis:
                            m1 = analysis.get('m1_dna', {})
                            m4 = analysis.get('m4_motivation', {})
                            m6 = analysis.get('m6_playbook', {})

                            # Update DataFrame with AI insights
                            df.at[idx, 'lead_description'] = m1.get('summary', '')[:200]

                            hooks = m4.get('teslaHooks', [])
                            if hooks:
                                df.at[idx, 'sniper_hook'] = hooks[0]

                            ssr = m6.get('ssr', [])
                            if ssr:
                                df.at[idx, 'objection_killer'] = ssr[0].get('solution', '')

                    logger.debug(f"[BIGDECODER SLOW] ✓ Processed lead {idx}")

                except Exception as e:
                    logger.error(f"[BIGDECODER SLOW] Error for lead {idx}: {e}")

            # Small delay between batches
            await asyncio.sleep(0.5)

        return df

    def _build_lead_context(self, row: pd.Series) -> str:
        """Build context string for AI analysis"""
        parts = []

        if row.get('company_name_clean'):
            parts.append(f"Firma: {row['company_name_clean']}")

        pkd = row.get('pkd_clean', '') or row.get('GlownyKodPkd', '')
        if pkd:
            profile = PKD_PROFILES.get(pkd, PKD_PROFILES.get("DEFAULT", {}))
            parts.append(f"Branża: {profile.get('full_name', 'Nieznana')} (PKD: {pkd})")

        if row.get('wealth_tier'):
            parts.append(f"Zamożność: {row['wealth_tier']} (score {row.get('wealth_score', 5)}/10)")

        if row.get('Potential_Savings_PLN'):
            parts.append(f"Potencjalne oszczędności: {row['Potential_Savings_PLN']:,.0f} PLN/rok")

        if row.get('charger_distance_km'):
            parts.append(f"Ładowarka: {row['charger_distance_km']:.1f} km")

        if row.get('leasing_cycle'):
            parts.append(f"Cykl leasingowy: {row['leasing_cycle']}")

        return " | ".join(parts)

    def _calculate_stats(self, df: pd.DataFrame, stats: PipelineStats) -> None:
        """Calculate summary statistics from processed DataFrame"""
        # Averages
        if 'wealth_score' in df.columns:
            stats.avg_wealth_score = df['wealth_score'].mean()

        if 'total_score' in df.columns:
            stats.avg_total_score = df['total_score'].mean()

        if 'charger_distance_km' in df.columns:
            valid_distances = df[df['charger_distance_km'] > 0]['charger_distance_km']
            if len(valid_distances) > 0:
                stats.avg_charger_distance = valid_distances.mean()

        if 'Potential_Savings_PLN' in df.columns:
            stats.avg_tax_saving = df['Potential_Savings_PLN'].mean()

        # Top industries
        pkd_col = None
        for col in ['pkd_clean', 'GlownyKodPkd', 'pkd']:
            if col in df.columns:
                pkd_col = col
                break

        if pkd_col:
            stats.top_pkd_industries = df[pkd_col].value_counts().head(5).to_dict()

        # Top cities
        city_col = None
        for col in ['resolved_city', 'city_clean', 'Miejscowosc']:
            if col in df.columns:
                city_col = col
                break

        if city_col:
            stats.top_cities = df[city_col].value_counts().head(5).to_dict()


# === CONVENIENCE FUNCTIONS ===

def process_csv_file(
    input_path: str,
    output_path: str,
    level: ProcessingLevel = ProcessingLevel.LEVEL_2_GOTHAM,
    config: Optional[PipelineConfig] = None
) -> PipelineStats:
    """
    Process a CSV file through the unified pipeline.

    Args:
        input_path: Path to input CSV file
        output_path: Path to save enriched CSV
        level: Processing level
        config: Pipeline configuration

    Returns:
        Processing statistics
    """
    logger.info(f"[CSV PROCESSOR] Reading {input_path}...")
    df = pd.read_csv(input_path, encoding='utf-8', low_memory=False)

    pipeline = UnifiedPipeline(config=config)
    df_result, stats = pipeline.process_sync(df, level=level)

    logger.info(f"[CSV PROCESSOR] Writing {len(df_result)} rows to {output_path}...")
    df_result.to_csv(output_path, index=False, encoding='utf-8')

    return stats


# === CLI ===

if __name__ == "__main__":
    print("=" * 70)
    print(" UNIFIED INTELLIGENCE PLATFORM v5.0 ")
    print(" Industrial Lead Refinery & Cognitive Analysis Suite ")
    print("=" * 70)
    print()

    # Test data
    test_data = {
        'NIP': ['5272829917', '5261040828'],
        'Telefon': ['+48 500 100 200', '48500100200'],
        'Email': ['jan@kancelaria.pl', 'anna@it.pl'],
        'Nazwa': ['Kancelaria Prawna sp. z o.o.', 'Tech Solutions'],
        'FormaPrawna': ['SPÓŁKA Z O.O.', 'JEDNOOSOBOWA DZIAŁALNOŚĆ'],
        'PkdGlowny': ['6910Z', '6201Z'],
        'KodPocztowy': ['00-001', '40-001'],
        'Miejscowosc': ['Warszawa', 'Katowice'],
        'Wojewodztwo': ['MAZOWIECKIE', 'ŚLĄSKIE'],
        'DataRozpoczeciaDzialalnosci': ['2019-03-15', '2021-08-20'],
    }

    df_test = pd.DataFrame(test_data)

    print("📥 Input data:")
    print(df_test[['Nazwa', 'PkdGlowny', 'Miejscowosc']])
    print()

    # Process through pipeline
    print("🔄 Processing through Unified Pipeline...")
    print()

    pipeline = UnifiedPipeline()
    df_result, stats = pipeline.process_sync(df_test)

    print("📊 Results:")
    print("-" * 50)
    print(f"Rows processed: {stats.cleaned_rows}")
    print(f"Tier distribution: {stats.tier_counts}")
    print(f"DNA profiles: {stats.dna_profiles_generated}")
    print(f"Avg wealth score: {stats.avg_wealth_score:.1f}/10")
    print(f"Avg total score: {stats.avg_total_score:.1f}/100")
    print(f"Processing time: {stats.processing_time_ms}ms")
    print()

    print("🎯 Enriched leads:")
    result_cols = ['target_tier', 'total_score', 'wealth_tier', 'lead_type']
    for col in result_cols:
        if col not in df_result.columns:
            result_cols.remove(col)

    print(df_result[['Nazwa'] + [c for c in result_cols if c in df_result.columns]])
    print()

    print("=" * 70)
    print("✅ Unified Pipeline Test Complete!")
    print("=" * 70)
