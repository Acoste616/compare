# UNIFIED INTELLIGENCE PLATFORM - Architecture Document
## Project ULTRA v5.0 - Industrial Lead Refinery & Cognitive Analysis Suite

**Date**: 2026-01-07
**Author**: Architecture Audit
**Branch**: claude/unified-intelligence-platform-bj3Pd

---

## 1. AUDIT SUMMARY: Redundancy Analysis

### Files Audited:
| File | Lines | Version | Status |
|------|-------|---------|--------|
| `backend/sniper_module.py` | 1364 | v4.2 | **REDUNDANT** - To be replaced |
| `asset_sniper/gotham_engine.py` | 707 | Palantir | **KEEP** - Advanced M² logic |
| `backend/analysis_engine.py` | 783 | v3.1 | **KEEP** - Ollama/BigDecoder |
| `backend/gotham_module.py` | 839 | v4.0 | **KEEP** - Burning House + CEPiK |
| `asset_sniper/config.py` | 762 | BIBLE v1.0 | **KEEP** - Central config |
| `asset_sniper/scoring_matrix.py` | 562 | Palantir | **KEEP** - 8-tier scoring |
| `asset_sniper/bigdecoder_lite.py` | 318 | BIBLE v1.0 | **KEEP** - Template messages |

### Redundancy Map:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          REDUNDANCY ELIMINATION MAP                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WEALTH SCORING (3 implementations → 1)                                      │
│  ├── backend/sniper_module.py:71-110    WEALTH_MAP dict         ❌ DELETE    │
│  ├── asset_sniper/gotham_engine.py      M²-based calculation    ✅ KEEP      │
│  └── asset_sniper/config.py             REAL_ESTATE_MARKET_DATA ✅ KEEP      │
│                                                                              │
│  TAX CALCULATIONS (3 implementations → 1)                                    │
│  ├── backend/sniper_module.py:183-234   TAX_BENEFIT_MAP         ❌ DELETE    │
│  ├── backend/gotham_module.py           BurningHouseCalculator  ✅ KEEP      │
│  └── asset_sniper/gotham_engine.py      calculate_tax_benefit() ✅ KEEP      │
│                                                                              │
│  PKD INDUSTRY MAPPING (2 implementations → 1)                                │
│  ├── backend/sniper_module.py:113-180   PKD_LEASING_MAP         ❌ DELETE    │
│  └── asset_sniper/config.py             PKD_PROFILES (100+ PKD) ✅ KEEP      │
│                                                                              │
│  TIER CLASSIFICATION (2 implementations → 1)                                 │
│  ├── backend/sniper_module.py:42-68     LeadTier (S/A/B/C)      ❌ DELETE    │
│  └── asset_sniper/config.py             Tier (S-E, 8 tiers)     ✅ KEEP      │
│                                                                              │
│  DNA PROFILING (3 implementations → 1 unified)                               │
│  ├── backend/sniper_module.py:240-324   PalantirTactics simple  ❌ DELETE    │
│  ├── backend/analysis_engine.py         Ollama deep profiling   ✅ KEEP      │
│  └── asset_sniper/scoring_matrix.py     LeadDNA templates       ✅ KEEP      │
│                                                                              │
│  CHARGER DISTANCE (2 implementations → 1)                                    │
│  ├── backend/sniper_module.py:249-275   estimate_charger_dist   ❌ DELETE    │
│  └── asset_sniper/gotham_engine.py      Haversine calculation   ✅ KEEP      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. UNIFIED DATA FLOW ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│                        UNIFIED INTELLIGENCE PLATFORM v5.0                           │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────────────────┐                                                           │
│   │    RAW CSV INPUT    │  100k+ leads from CEIDG/KRS exports                       │
│   │  (Dirty CEIDG Data) │  Fields: NIP, Telefon, Email, PKD, Miasto, etc.          │
│   └──────────┬──────────┘                                                           │
│              │                                                                      │
│              ▼                                                                      │
│   ╔══════════════════════════════════════════════════════════════════════════╗     │
│   ║                     MODULE 1: LEAD FACTORY                               ║     │
│   ║                     (The Orchestrator)                                   ║     │
│   ║                                                                          ║     │
│   ║   ┌─────────────────────────────────────────────────────────────────┐   ║     │
│   ║   │ STAGE 1: INGESTOR (asset_sniper/lead_refinery.py)               │   ║     │
│   ║   │                                                                  │   ║     │
│   ║   │  • NIP validation (10-digit checksum)                           │   ║     │
│   ║   │  • Phone normalization (+48 → 9-digit format)                   │   ║     │
│   ║   │  • Email validation (regex)                                     │   ║     │
│   ║   │  • Postal code cleaning (XX-XXX format)                         │   ║     │
│   ║   │  • Date parsing (multi-format support)                          │   ║     │
│   ║   │  • Chunked processing (10k rows per chunk)                      │   ║     │
│   ║   └──────────────────────────┬──────────────────────────────────────┘   ║     │
│   ║                              │                                          ║     │
│   ║                              ▼                                          ║     │
│   ║   ┌─────────────────────────────────────────────────────────────────┐   ║     │
│   ║   │ STAGE 2: GOTHAM ENGINE (asset_sniper/gotham_engine.py)          │   ║     │
│   ║   │                         ↓                                        │   ║     │
│   ║   │  ┌─────────────────────────────────────────────────────────┐    │   ║     │
│   ║   │  │ LAYER 1: WEALTH PROXY (M² Pricing)                      │    │   ║     │
│   ║   │  │                                                          │    │   ║     │
│   ║   │  │  Formula: (City_M²_Price / National_Avg) + Street_Bonus │    │   ║     │
│   ║   │  │                                                          │    │   ║     │
│   ║   │  │  Input:  postal_code="02-677", city="Warszawa"          │    │   ║     │
│   ║   │  │  ├── REAL_ESTATE_MARKET_DATA["Warszawa"]["avg_m2"]      │    │   ║     │
│   ║   │  │  │   = 17,500 PLN/m²                                    │    │   ║     │
│   ║   │  │  ├── NATIONAL_AVG_M2_PRICE = 11,500 PLN/m²              │    │   ║     │
│   ║   │  │  ├── Ratio = 17,500 / 11,500 = 1.52x                    │    │   ║     │
│   ║   │  │  └── Wealth Score = 10/10 (Tier S)                      │    │   ║     │
│   ║   │  │                                                          │    │   ║     │
│   ║   │  │  Fallbacks:                                              │    │   ║     │
│   ║   │  │  • No city → Check premium street keywords               │    │   ║     │
│   ║   │  │  • No location → PKD_WEALTH_CORRELATION (industry)       │    │   ║     │
│   ║   │  └──────────────────────────────────────────────────────────┘    │   ║     │
│   ║   │                              │                                   │   ║     │
│   ║   │                              ▼                                   │   ║     │
│   ║   │  ┌─────────────────────────────────────────────────────────┐    │   ║     │
│   ║   │  │ LAYER 2: CHARGER INFRASTRUCTURE (Haversine GIS)         │    │   ║     │
│   ║   │  │                                                          │    │   ║     │
│   ║   │  │  Input:  postal_code="40-001"                           │    │   ║     │
│   ║   │  │  ├── POSTAL_PREFIX_COORDINATES["40-0"] = (50.26, 19.02) │    │   ║     │
│   ║   │  │  ├── CHARGER_LOCATIONS[] = 10+ Tesla Superchargers      │    │   ║     │
│   ║   │  │  ├── Haversine(lead_coords, charger_coords)             │    │   ║     │
│   ║   │  │  └── charger_distance_km = 2.3 km                       │    │   ║     │
│   ║   │  └──────────────────────────────────────────────────────────┘    │   ║     │
│   ║   │                              │                                   │   ║     │
│   ║   │                              ▼                                   │   ║     │
│   ║   │  ┌─────────────────────────────────────────────────────────┐    │   ║     │
│   ║   │  │ LAYER 3: TAX ENGINE (EV vs ICE)                         │    │   ║     │
│   ║   │  │                                                          │    │   ║     │
│   ║   │  │  Input:  pkd_code="6910Z", legal_form="SPÓŁKA Z O.O."   │    │   ║     │
│   ║   │  │  ├── EV_AMORTYZACJA_LIMIT = 225,000 PLN                 │    │   ║     │
│   ║   │  │  ├── ICE_AMORTYZACJA_LIMIT = 150,000 PLN                │    │   ║     │
│   ║   │  │  ├── TAX_DIFFERENCE = 75,000 PLN                        │    │   ║     │
│   ║   │  │  ├── Tax Rate (Prawnik) = 32%                           │    │   ║     │
│   ║   │  │  ├── Annual Saving = 75,000 × 0.32 = 24,000 PLN         │    │   ║     │
│   ║   │  │  └── NaszEauto Subsidy = 27,000 PLN                     │    │   ║     │
│   ║   │  └──────────────────────────────────────────────────────────┘    │   ║     │
│   ║   │                              │                                   │   ║     │
│   ║   │                              ▼                                   │   ║     │
│   ║   │  ┌─────────────────────────────────────────────────────────┐    │   ║     │
│   ║   │  │ LAYER 4: LEASING CYCLE (Company Age Analysis)           │    │   ║     │
│   ║   │  │                                                          │    │   ║     │
│   ║   │  │  Input:  start_date="2019-03-15"                        │    │   ║     │
│   ║   │  │  ├── age_years = (today - start_date) / 365 = 6.8 years │    │   ║     │
│   ║   │  │  ├── LEASING_CYCLE_MAP[(6,7)] = RENEWAL_WINDOW          │    │   ║     │
│   ║   │  │  ├── propensity = 0.95 (highest!)                       │    │   ║     │
│   ║   │  │  └── "Okno odnowienia - najlepszy moment"               │    │   ║     │
│   ║   │  └──────────────────────────────────────────────────────────┘    │   ║     │
│   ║   └──────────────────────────┬──────────────────────────────────────┘   ║     │
│   ║                              │                                          ║     │
│   ║                              ▼                                          ║     │
│   ║   ┌─────────────────────────────────────────────────────────────────┐   ║     │
│   ║   │ STAGE 3: SCORING MATRIX (asset_sniper/scoring_matrix.py)        │   ║     │
│   ║   │                                                                  │   ║     │
│   ║   │  5-FACTOR SCORING (100 pts max):                                │   ║     │
│   ║   │                                                                  │   ║     │
│   ║   │  ┌─────────────────────────────────────────────────────────┐    │   ║     │
│   ║   │  │ FACTOR           │ MAX PTS │ CALCULATION                │    │   ║     │
│   ║   │  ├───────────────────┼─────────┼────────────────────────────┤    │   ║     │
│   ║   │  │ PKD Tier          │   30    │ S=30, A=22, B=15, DEF=8   │    │   ║     │
│   ║   │  │ Wealth Proxy      │   25    │ PREM=25, HIGH=20, MED=15  │    │   ║     │
│   ║   │  │ Company Age       │   20    │ 3-6y=20, 7+=18, 2-3y=15   │    │   ║     │
│   ║   │  │ Charger Proximity │   15    │ <5km=15, <10km=12, <20=9  │    │   ║     │
│   ║   │  │ Contact Quality   │   10    │ Phone=5, Email=3, WWW=2   │    │   ║     │
│   ║   │  └───────────────────┴─────────┴────────────────────────────┘    │   ║     │
│   ║   │                                                                  │   ║     │
│   ║   │  TIER ASSIGNMENT:                                                │   ║     │
│   ║   │  • S    (85-100): NATYCHMIAST - Telefon w 24h                   │   ║     │
│   ║   │  • AAA  (75-84):  DZIŚ - Kontakt tego dnia                      │   ║     │
│   ║   │  • AA   (65-74):  TEN TYDZIEŃ                                   │   ║     │
│   ║   │  • A    (50-64):  AUTOMAT - Sekwencja                           │   ║     │
│   ║   │  • B    (35-49):  NISKI - Raz w miesiącu                        │   ║     │
│   ║   │  • C-E  (0-34):   ARCHIWUM                                      │   ║     │
│   ║   └──────────────────────────┬──────────────────────────────────────┘   ║     │
│   ║                              │                                          ║     │
│   ╚══════════════════════════════╪══════════════════════════════════════════╝     │
│                                  │                                                 │
│                                  ▼                                                 │
│   ╔══════════════════════════════════════════════════════════════════════════╗     │
│   ║                     MODULE 2: BIGDECODER                                 ║     │
│   ║                     (The Cognitive Brain)                                ║     │
│   ║                                                                          ║     │
│   ║   ┌────────────────────┬────────────────────┬────────────────────┐      ║     │
│   ║   │                    │                    │                    │      ║     │
│   ║   │    FAST PATH       │    SLOW PATH       │  STRATEGIC SUITE   │      ║     │
│   ║   │   (Templates)      │    (Ollama AI)     │   (AI + Data)      │      ║     │
│   ║   │                    │                    │                    │      ║     │
│   ║   │  For: ALL Tiers    │  For: Tier S/AAA   │  For: Tier S only  │      ║     │
│   ║   │  Time: <100ms      │  Time: 30-90s      │  Time: 60-120s     │      ║     │
│   ║   │                    │                    │                    │      ║     │
│   ║   │  Uses:             │  Uses:             │  Uses:             │      ║     │
│   ║   │  • PKD_PROFILES    │  • AnalysisEngine  │  • Ollama + GOTHAM │      ║     │
│   ║   │  • LeadDNA class   │  • Ollama DeepSeek │  • RAG (Qdrant)    │      ║     │
│   ║   │  • Template hooks  │  • M1-M7 modules   │  • CEPiK data      │      ║     │
│   ║   │                    │                    │                    │      ║     │
│   ║   │  Output:           │  Output:           │  Output:           │      ║     │
│   ║   │  • lead_type       │  • Client DNA      │  • Strategic Q's   │      ║     │
│   ║   │  • best_hook       │  • Psychometrics   │  • AI Responses    │      ║     │
│   ║   │  • tax_weapon      │  • Sales Playbook  │  • Objection Kill  │      ║     │
│   ║   │  • objection_kill  │  • Journey Stage   │  • Closing Script  │      ║     │
│   ║   │                    │                    │                    │      ║     │
│   ║   └────────────────────┴────────────────────┴────────────────────┘      ║     │
│   ║                                                                          ║     │
│   ║   DNA TYPES:                                                             ║     │
│   ║   • ANALYTICAL      - Data-driven, needs ROI proof                       ║     │
│   ║   • VISIONARY       - Innovation-focused, early adopter                  ║     │
│   ║   • COST_DRIVEN     - Price sensitive, TCO focused                       ║     │
│   ║   • STATUS_SEEKER   - Premium/prestige focused                           ║     │
│   ║   • PRAGMATIC       - Practical, reliability focused                     ║     │
│   ║                                                                          ║     │
│   ╚══════════════════════════════╪══════════════════════════════════════════╝     │
│                                  │                                                 │
│                                  ▼                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐     │
│   │                      OUTPUT: ENRICHED CSV                               │     │
│   │                                                                          │     │
│   │  REQUIRED COLUMNS:                                                       │     │
│   │  ├── Imie, Nazwisko, Email, Telefon                                     │     │
│   │  ├── TargetTier (S/AAA/AA/A/B/C/D/E)                                    │     │
│   │  ├── TotalScore (0-100)                                                 │     │
│   │  └── Priority (NATYCHMIAST/DZIŚ/TEN TYDZIEŃ/AUTOMAT/ARCHIWUM)          │     │
│   │                                                                          │     │
│   │  WEALTH COLUMNS:                                                         │     │
│   │  ├── Wealth_Score (1-10)                                                │     │
│   │  ├── Wealth_Tier (S/PREMIUM/HIGH/MEDIUM/STANDARD/LOW)                   │     │
│   │  ├── Wealth_Signal ("Miasto Warszawa - cena m² 17,500 PLN")             │     │
│   │  ├── M2_Price_Estimated (17500)                                         │     │
│   │  └── Resolved_City ("Warszawa")                                         │     │
│   │                                                                          │     │
│   │  FINANCIAL COLUMNS:                                                      │     │
│   │  ├── Potential_Savings_PLN (24000.00)                                   │     │
│   │  ├── Tax_Benefit_First_Year (51000.00)                                  │     │
│   │  └── NaszEauto_Subsidy (27000.00)                                       │     │
│   │                                                                          │     │
│   │  DNA COLUMNS (Tier S/AAA only):                                          │     │
│   │  ├── Lead_Type (ALPHA_LAWYER)                                           │     │
│   │  ├── Decision_Driver (STATUS_AND_TAX)                                   │     │
│   │  ├── Best_Hook ("Panie Mecenasie, do 24 000 PLN rocznie...")           │     │
│   │  ├── Objection_Killer ("Większość kancelarii już...")                   │     │
│   │  └── Closing_Trigger ("Konkretne liczby + prestiż")                     │     │
│   │                                                                          │     │
│   │  INTELLIGENCE COLUMNS:                                                   │     │
│   │  ├── SniperHook (AI-generated cold call opener)                         │     │
│   │  ├── TaxWeapon ("OSZCZĘDNOŚĆ PODATKOWA: do 24,000 PLN/rok...")         │     │
│   │  ├── GothamInsight ("824 premium car leases expiring...")               │     │
│   │  └── Lead_DNA_Summary ("ALPHA_LAWYER|STATUS_AND_TAX|hook...")           │     │
│   │                                                                          │     │
│   └─────────────────────────────────────────────────────────────────────────┘     │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. MODULE INTEGRATION MAP

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          INTEGRATION MAP (How They Talk)                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   main.py (FastAPI)                                                                 │
│       │                                                                             │
│       ├──▶ POST /api/sniper/process-csv                                            │
│       │        │                                                                    │
│       │        └──▶ BackgroundTasks.add_task(lead_factory.process_batch)           │
│       │                    │                                                        │
│       │                    ├──▶ LeadRefinery.clean_data(df)                         │
│       │                    │                                                        │
│       │                    ├──▶ GothamEngine.process(df_clean)                      │
│       │                    │        ├──▶ get_wealth_score(postal, city, pkd)       │
│       │                    │        ├──▶ calculate_charger_distance(postal)         │
│       │                    │        ├──▶ calculate_tax_benefit(pkd, legal_form)     │
│       │                    │        └──▶ calculate_leasing_cycle(start_date)        │
│       │                    │                                                        │
│       │                    ├──▶ ScoringMatrix.score_all(df_enriched)                │
│       │                    │        ├──▶ score_pkd(pkd) → 0-30 pts                  │
│       │                    │        ├──▶ score_wealth(score, tier) → 0-25 pts       │
│       │                    │        ├──▶ score_company_age(age) → 0-20 pts          │
│       │                    │        ├──▶ score_charger_proximity(km) → 0-15 pts     │
│       │                    │        ├──▶ score_contact_quality(phone, email)        │
│       │                    │        └──▶ assign_tier(total) → S/AAA/.../E           │
│       │                    │                                                        │
│       │                    └──▶ BigDecoder.process(df_scored)                       │
│       │                             │                                               │
│       │                             ├──▶ [ALL TIERS] FAST PATH                      │
│       │                             │        └──▶ BigDecoderLite.enrich_messages()  │
│       │                             │                                               │
│       │                             └──▶ [TIER S/AAA] SLOW PATH                     │
│       │                                      └──▶ AnalysisEngine.run_deep_analysis()│
│       │                                               ├──▶ _extract_global_context()│
│       │                                               ├──▶ _call_ollama(prompt)     │
│       │                                               └──▶ M1-M7 JSON response      │
│       │                                                                             │
│       ├──▶ GET /api/sniper/stats                                                    │
│       │        └──▶ Return tier distribution, avg scores, processing metrics        │
│       │                                                                             │
│       ├──▶ GET /api/gotham/market/{region}                                          │
│       │        └──▶ CEPiKConnector.get_regional_data(region)                        │
│       │                                                                             │
│       └──▶ GET /api/gotham/opportunity/{region}                                     │
│                └──▶ CEPiKConnector.get_opportunity_score(region)                    │
│                         └──▶ Real CEPiK API → lease expiry counts                   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. IMPLEMENTATION PLAN

### Phase 1: Create Unified BigDecoder Module
**File**: `asset_sniper/bigdecoder/core.py`

```python
class BigDecoder:
    """Unified cognitive analysis with FAST and SLOW paths"""

    def __init__(self, analysis_engine=None, gotham_engine=None):
        self.fast_path = BigDecoderLite()      # Templates
        self.slow_path = analysis_engine        # Ollama
        self.gotham = gotham_engine             # Market data

    async def process(self, df: pd.DataFrame, tier_threshold: str = "AAA"):
        """
        Process leads through appropriate path based on tier.

        Tier S/AAA → SLOW PATH (Ollama AI)
        Tier AA-E  → FAST PATH (Templates)
        """
```

### Phase 2: Consolidate Gotham Engine
**File**: `asset_sniper/gotham/unified.py`

```python
class UnifiedGothamEngine:
    """Single source of truth for all market intelligence"""

    def __init__(self):
        self.wealth_engine = WealthProxyEngine()     # M² pricing
        self.charger_engine = ChargerInfrastructure() # Haversine
        self.tax_engine = TaxCalculator()            # EV vs ICE
        self.cepik_connector = CEPiKConnector()      # Market data

    def enrich_lead(self, lead: dict) -> EnrichedLead:
        """Complete enrichment pipeline for single lead"""
```

### Phase 3: Delete Redundant Code
**File**: `backend/sniper_module.py`

- DELETE: `WEALTH_MAP` (lines 71-110) → Use GothamEngine.get_wealth_score()
- DELETE: `PKD_LEASING_MAP` (lines 113-152) → Use config.PKD_PROFILES
- DELETE: `PKD_INDUSTRY_MAP` (lines 155-180) → Use config.PKD_PROFILES
- DELETE: `TAX_BENEFIT_MAP` (lines 183-234) → Use GothamEngine.calculate_tax_benefit()
- DELETE: `PalantirTactics` class (lines 240-340) → Move to asset_sniper/
- KEEP: `AssetSniper` class but import from asset_sniper/ modules

### Phase 4: Update Frontend Integration
**File**: `components/AssetSniperTab.tsx`

- Add real-time progress bar for batch processing
- Add "Intelligence Cards" for top Tier S leads
- Add DNA profile visualization

---

## 5. FILE CHANGES SUMMARY

| Action | File | Description |
|--------|------|-------------|
| CREATE | `asset_sniper/bigdecoder/core.py` | Unified BigDecoder |
| CREATE | `asset_sniper/gotham/unified.py` | Consolidated Gotham |
| MODIFY | `backend/sniper_module.py` | Delete redundant code |
| MODIFY | `backend/main.py` | Update imports |
| MODIFY | `components/AssetSniperTab.tsx` | Add Intelligence Cards |

---

## 6. APPROVAL REQUIRED

Before implementing these changes, please confirm:

1. ✅ Delete redundant hardcoded data from `backend/sniper_module.py`?
2. ✅ Create unified BigDecoder with FAST/SLOW paths?
3. ✅ Consolidate Gotham Engine under `asset_sniper/` package?
4. ✅ Update frontend to show Intelligence Cards?

**Awaiting approval to proceed with implementation.**
