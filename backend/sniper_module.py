"""
ASSET SNIPER Module (ULTRA v4.2)
Data Refinery for CEIDG Leads Processing

DEEP INTEGRATION:
- GOTHAM Integration: Charger infrastructure, Tax potential, Market opportunity
- BigDecoder Integration: Psychographic DNA profiling via Ollama
- Palantir Tactics: Fallback estimates when APIs fail

FEATURES:
- Level 0 (Ingest): Clean dirty CSV data (NIP, Phones)
- Level 1 (Local/Free): Instant segmentation using local logic
- Level 2 (API/Slow): Deep analysis via Ollama for Tier S leads only
- Level 3 (Intelligence): GOTHAM hard data + BigDecoder DNA profiling

Author: Lead Architect
Version: 4.2.0
"""

import re
import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === ENUMS & CONSTANTS ===

class LeadTier(str, Enum):
    """Lead tier classification"""
    TIER_S = "Tier S"   # VIP - Deep Analysis + API Enrichment
    TIER_A = "Tier A"   # Hot Lead - Local Enrichment Only
    TIER_B = "Tier B"   # Warm Lead - Basic Processing
    TIER_C = "Tier C"   # Cold Lead - Minimal Processing
    UNKNOWN = "Unknown" # Insufficient data


class LeasingCycle(str, Enum):
    """Business leasing cycle stage based on company age"""
    STARTUP = "Startup"          # 0-2 years - unlikely leasing
    GROWTH = "Growth"            # 2-4 years - first leasing cycle
    MATURE = "Mature"            # 4-7 years - leasing renewal likely
    ESTABLISHED = "Established"  # 7+ years - multiple leasing cycles
    UNKNOWN = "Unknown"


class ClientDNAType(str, Enum):
    """Psychographic profile types based on BigDecoder analysis"""
    ANALYTICAL = "Analytical"       # Data-driven, ROI focused
    VISIONARY = "Visionary"         # Innovation-focused, early adopter
    COST_DRIVEN = "Cost-Driven"     # Price sensitive, TCO focused
    STATUS_SEEKER = "Status-Seeker" # Premium/prestige focused
    PRAGMATIC = "Pragmatic"         # Practical, reliability focused
    UNKNOWN = "Unknown"


# === WEALTH MAP (Polish ZIP Code Prefixes -> Estimated Avg Income) ===
WEALTH_MAP: Dict[str, Tuple[int, str]] = {
    # WARSAW (00-04) - Highest income zone
    "00": (12500, "PREMIUM"),
    "01": (11000, "PREMIUM"),
    "02": (13500, "PREMIUM"),
    "03": (10500, "HIGH"),
    "04": (9500, "HIGH"),
    # KRAKÓW (30-32)
    "30": (10000, "HIGH"),
    "31": (9500, "HIGH"),
    "32": (8500, "MEDIUM"),
    # WROCŁAW (50-54)
    "50": (9500, "HIGH"),
    "51": (9000, "HIGH"),
    "52": (8000, "MEDIUM"),
    "53": (8500, "MEDIUM"),
    "54": (7500, "MEDIUM"),
    # POZNAŃ (60-64)
    "60": (9000, "HIGH"),
    "61": (8500, "MEDIUM"),
    "62": (7500, "MEDIUM"),
    # GDAŃSK-SOPOT-GDYNIA (80-84)
    "80": (9500, "HIGH"),
    "81": (12000, "PREMIUM"),
    "82": (9000, "HIGH"),
    # KATOWICE / ŚLĄSK (40-44)
    "40": (8500, "MEDIUM"),
    "41": (8000, "MEDIUM"),
    "42": (7500, "MEDIUM"),
    "43": (7000, "MEDIUM"),
    "44": (7500, "MEDIUM"),
    # ŁÓDŹ (90-94)
    "90": (7500, "MEDIUM"),
    "91": (7000, "MEDIUM"),
    "92": (6500, "STANDARD"),
    "93": (7000, "MEDIUM"),
    "94": (6500, "STANDARD"),
    # DEFAULT
    "DEFAULT": (6000, "STANDARD"),
}


# === PKD CODE -> LEASING PROPENSITY MAP ===
PKD_LEASING_MAP: Dict[str, Tuple[int, str]] = {
    # TRANSPORT & LOGISTICS
    "49": (95, "VERY_HIGH"),
    "50": (90, "VERY_HIGH"),
    "51": (85, "HIGH"),
    "52": (90, "VERY_HIGH"),
    "53": (95, "VERY_HIGH"),
    # SALES & FIELD WORK
    "46": (85, "HIGH"),
    "47": (70, "MEDIUM"),
    "45": (90, "VERY_HIGH"),
    # PROFESSIONAL SERVICES
    "62": (75, "HIGH"),
    "63": (70, "MEDIUM"),
    "64": (80, "HIGH"),
    "69": (75, "HIGH"),
    "70": (80, "HIGH"),
    "71": (75, "HIGH"),
    "72": (65, "MEDIUM"),
    "73": (70, "MEDIUM"),
    # CONSTRUCTION
    "41": (80, "HIGH"),
    "42": (85, "HIGH"),
    "43": (80, "HIGH"),
    # HEALTHCARE
    "86": (70, "MEDIUM"),
    "87": (60, "MEDIUM"),
    # REAL ESTATE
    "68": (85, "HIGH"),
    # MANUFACTURING
    "10": (65, "MEDIUM"),
    "20": (70, "MEDIUM"),
    "25": (70, "MEDIUM"),
    "26": (75, "HIGH"),
    "28": (75, "HIGH"),
    "29": (90, "VERY_HIGH"),
    # DEFAULT
    "DEFAULT": (50, "LOW"),
}


# === PKD CODE -> INDUSTRY NAME (Polish) ===
PKD_INDUSTRY_MAP: Dict[str, str] = {
    "49": "Transport lądowy",
    "50": "Transport wodny",
    "51": "Transport lotniczy",
    "52": "Magazynowanie i logistyka",
    "53": "Usługi pocztowe i kurierskie",
    "46": "Handel hurtowy",
    "47": "Handel detaliczny",
    "45": "Handel samochodami",
    "62": "Usługi IT",
    "63": "Usługi informacyjne",
    "64": "Usługi finansowe",
    "69": "Usługi prawne i księgowe",
    "70": "Doradztwo biznesowe",
    "71": "Architektura i inżynieria",
    "72": "Badania i rozwój",
    "73": "Reklama i marketing",
    "41": "Budownictwo ogólne",
    "42": "Inżynieria lądowa",
    "43": "Budownictwo specjalistyczne",
    "86": "Opieka zdrowotna",
    "87": "Opieka społeczna",
    "68": "Nieruchomości",
    "DEFAULT": "Działalność gospodarcza"
}


# === TAX BENEFIT MAP ===
TAX_BENEFIT_MAP: Dict[str, Dict[str, Any]] = {
    "SPÓŁKA Z O.O.": {
        "vat_deduction": 100,
        "leasing_kup": 100,
        "ev_bonus": 27000,
        "depreciation_boost": True,
        "score": 95
    },
    "SPÓŁKA AKCYJNA": {
        "vat_deduction": 100,
        "leasing_kup": 100,
        "ev_bonus": 27000,
        "depreciation_boost": True,
        "score": 95
    },
    "JEDNOOSOBOWA DZIAŁALNOŚĆ": {
        "vat_deduction": 50,
        "leasing_kup": 75,
        "ev_bonus": 27000,
        "depreciation_boost": False,
        "score": 70
    },
    "SPÓŁKA CYWILNA": {
        "vat_deduction": 50,
        "leasing_kup": 75,
        "ev_bonus": 27000,
        "depreciation_boost": False,
        "score": 65
    },
    "SPÓŁKA KOMANDYTOWA": {
        "vat_deduction": 100,
        "leasing_kup": 100,
        "ev_bonus": 27000,
        "depreciation_boost": True,
        "score": 85
    },
    "SPÓŁKA JAWNA": {
        "vat_deduction": 100,
        "leasing_kup": 100,
        "ev_bonus": 27000,
        "depreciation_boost": True,
        "score": 80
    },
    "DEFAULT": {
        "vat_deduction": 50,
        "leasing_kup": 50,
        "ev_bonus": 18750,
        "depreciation_boost": False,
        "score": 50
    }
}


# === PALANTIR TACTICS: FALLBACK ESTIMATES ===
# Used when real APIs fail - educated guesses based on data patterns

class PalantirTactics:
    """
    Fallback estimation system when external APIs are unavailable
    
    Strategy: Use statistical patterns and heuristics to provide
    reasonable estimates rather than empty data
    """
    
    @staticmethod
    def estimate_charger_distance(city: str, wealth_tier: str) -> float:
        """Estimate charger distance based on city and wealth tier"""
        # Premium areas have better infrastructure
        base_distances = {
            "PREMIUM": 2.5,
            "HIGH": 5.0,
            "MEDIUM": 8.0,
            "STANDARD": 12.0,
            "UNKNOWN": 10.0
        }
        
        # Major cities have better coverage
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
        """Estimate annual tax savings based on legal form and industry"""
        # Base savings from switching to EV
        fuel_saving_per_km = 0.35  # PLN saved per km (fuel vs electricity)
        base_fuel_saving = estimated_km * fuel_saving_per_km
        
        # VAT recovery estimate
        form_upper = str(legal_form).upper()
        if "SPÓŁKA Z O.O." in form_upper or "SPÓŁKA AKCYJNA" in form_upper:
            vat_recovery = 7980  # Full VAT on lease
        elif "JEDNOOSOBOWA" in form_upper:
            vat_recovery = 3990  # 50% VAT
        else:
            vat_recovery = 5000  # Estimate
        
        # Industry multiplier (high-fleet industries save more)
        pkd_prefix = re.sub(r'\D', '', str(pkd_code))[:2] if pkd_code else ""
        high_fleet_pkd = ["49", "50", "51", "52", "53", "45", "46"]
        industry_multiplier = 1.3 if pkd_prefix in high_fleet_pkd else 1.0
        
        total = (base_fuel_saving + vat_recovery) * industry_multiplier
        return round(total, 0)
    
    @staticmethod
    def estimate_dna_type(pkd_code: str, wealth_tier: str, legal_form: str) -> str:
        """Estimate client DNA type based on industry and profile"""
        pkd_prefix = re.sub(r'\D', '', str(pkd_code))[:2] if pkd_code else ""
        
        # IT, R&D, Innovation sectors -> Visionary
        if pkd_prefix in ["62", "63", "72"]:
            return ClientDNAType.VISIONARY.value
        
        # Finance, Consulting -> Analytical
        if pkd_prefix in ["64", "69", "70", "71"]:
            return ClientDNAType.ANALYTICAL.value
        
        # Transport, Logistics -> Cost-Driven
        if pkd_prefix in ["49", "50", "51", "52", "53"]:
            return ClientDNAType.COST_DRIVEN.value
        
        # Real Estate, Premium areas -> Status-Seeker
        if pkd_prefix == "68" or wealth_tier == "PREMIUM":
            return ClientDNAType.STATUS_SEEKER.value
        
        # Default -> Pragmatic
        return ClientDNAType.PRAGMATIC.value
    
    @staticmethod
    def estimate_market_urgency(tier_score: int, leasing_cycle: str) -> int:
        """Estimate market urgency score (0-100)"""
        base_score = min(tier_score, 100)
        
        # Leasing cycle bonus
        cycle_bonus = {
            LeasingCycle.MATURE.value: 20,
            LeasingCycle.ESTABLISHED.value: 15,
            LeasingCycle.GROWTH.value: 10,
            LeasingCycle.STARTUP.value: 0,
            LeasingCycle.UNKNOWN.value: 5
        }
        
        bonus = cycle_bonus.get(leasing_cycle, 5)
        return min(100, base_score + bonus)


# === DATA CLASSES ===

@dataclass
class EnrichedLead:
    """Single enriched lead with all calculated fields - ULTRA v4.2"""
    # Original data (cleaned)
    nip: str = ""
    phone: str = ""
    email: str = ""
    company_name: str = ""
    legal_form: str = ""
    pkd_code: str = ""
    zip_code: str = ""
    city: str = ""
    voivodeship: str = ""
    start_date: Optional[date] = None
    
    # Level 1: Local Enrichment (Free)
    wealth_score: int = 0
    wealth_tier: str = "UNKNOWN"
    business_age_years: float = 0.0
    leasing_cycle: str = LeasingCycle.UNKNOWN.value
    pkd_leasing_propensity: int = 0
    pkd_leasing_tier: str = "UNKNOWN"
    tax_benefit_score: int = 0
    tax_benefit_details: Dict = field(default_factory=dict)
    
    # Tier Classification
    tier: str = LeadTier.UNKNOWN.value
    tier_score: int = 0
    tier_reasoning: str = ""
    
    # Level 2: API/Deep Enrichment (Tier S only)
    charger_nearby: Optional[bool] = None
    charger_count: int = 0
    estimated_savings: float = 0.0
    sniper_hook: str = ""
    
    # === NEW v4.2: GOTHAM + BigDecoder Integration ===
    # GOTHAM Hard Data
    annual_tax_saving: float = 0.0           # From SniperGateway.calculate_tax_potential
    charger_distance_km: float = 0.0         # From SniperGateway.check_charger_infrastructure
    charger_coverage: str = "UNKNOWN"        # HIGH/MEDIUM/LOW
    vat_recovery: float = 0.0                # Annual VAT recovery potential
    naszeauto_subsidy: float = 0.0           # NaszEauto eligibility amount
    
    # BigDecoder DNA Profile
    client_dna_type: str = ClientDNAType.UNKNOWN.value  # Analytical/Visionary/Cost-Driven/etc
    dna_confidence: int = 0                  # 0-100 confidence in DNA prediction
    dna_reasoning: str = ""                  # AI explanation of DNA type
    
    # Market Intelligence
    market_urgency_score: int = 0            # 0-100 urgency based on market conditions
    opportunity_insight: str = ""            # Human-readable market insight
    
    # Industry Context
    industry_name: str = ""                  # Human-readable industry name
    
    # Metadata
    next_action: str = ""
    processing_errors: List[str] = field(default_factory=list)
    enrichment_level: int = 0
    data_source: str = "local"               # local/api/palantir (fallback)


@dataclass
class SniperStats:
    """Processing statistics"""
    total_rows: int = 0
    processed_rows: int = 0
    error_rows: int = 0
    tier_s_count: int = 0
    tier_a_count: int = 0
    tier_b_count: int = 0
    tier_c_count: int = 0
    unknown_tier_count: int = 0
    avg_wealth_score: float = 0.0
    avg_tax_saving: float = 0.0
    avg_charger_distance: float = 0.0
    top_voivodeships: Dict[str, int] = field(default_factory=dict)
    top_dna_types: Dict[str, int] = field(default_factory=dict)
    processing_time_ms: int = 0
    api_calls_made: int = 0
    palantir_fallbacks: int = 0


# === ASSET SNIPER CLASS ===

class AssetSniper:
    """
    Data Refinery for CEIDG Leads Processing - ULTRA v4.2
    
    DEEP INTEGRATION:
    - GOTHAM: Hard financial data (tax, chargers, market)
    - BigDecoder: Psychographic DNA profiling via Ollama
    - Palantir Tactics: Intelligent fallbacks when APIs fail
    """
    
    def __init__(self, analysis_engine=None, gotham_gateway=None):
        """
        Initialize Asset Sniper with optional integrations
        
        Args:
            analysis_engine: AnalysisEngine instance for Ollama/BigDecoder
            gotham_gateway: SniperGateway class for GOTHAM data
        """
        self.analysis_engine = analysis_engine
        self.gotham_gateway = gotham_gateway
        self._api_calls = 0
        self._palantir_fallbacks = 0
        logger.info("[ASSET SNIPER v4.2] Initialized with GOTHAM + BigDecoder integration")
    
    # === LEVEL 0: DATA CLEANING ===
    
    @staticmethod
    def clean_nip(nip: Any) -> str:
        """Clean and validate Polish NIP number"""
        if pd is None or pd.isna(nip):
            return ""
        nip_str = re.sub(r'\D', '', str(nip))
        if len(nip_str) != 10:
            return ""
        weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(nip_str[i]) * weights[i] for i in range(9)) % 11
        if checksum != int(nip_str[9]):
            return ""
        return nip_str
    
    @staticmethod
    def clean_phone(phone: Any) -> str:
        """Clean and normalize Polish phone number"""
        if pd is None or pd.isna(phone):
            return ""
        phone_str = re.sub(r'\D', '', str(phone))
        if phone_str.startswith('48') and len(phone_str) == 11:
            phone_str = phone_str[2:]
        elif phone_str.startswith('048') and len(phone_str) == 12:
            phone_str = phone_str[3:]
        if len(phone_str) != 9:
            return ""
        return f"{phone_str[:3]}-{phone_str[3:6]}-{phone_str[6:]}"
    
    @staticmethod
    def clean_zip_code(zip_code: Any) -> str:
        """Clean Polish postal code"""
        if pd is None or pd.isna(zip_code):
            return ""
        zip_str = re.sub(r'\D', '', str(zip_code))
        if len(zip_str) != 5:
            return ""
        return f"{zip_str[:2]}-{zip_str[2:]}"
    
    @staticmethod
    def clean_email(email: Any) -> str:
        """Clean and validate email address"""
        if pd is None or pd.isna(email):
            return ""
        email_str = str(email).strip().lower()
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email_str):
            return email_str
        return ""
    
    @staticmethod
    def parse_date(date_val: Any) -> Optional[date]:
        """Parse date from various formats"""
        if pd is None or pd.isna(date_val):
            return None
        date_str = str(date_val).strip()
        formats = ["%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None
    
    def clean_data(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Level 0: Clean raw CSV data"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for AssetSniper")
        
        logger.info(f"[SNIPER L0] Cleaning {len(df)} rows...")
        df_clean = df.copy()
        
        column_mappings = {
            'nip': ['nip', 'NIP', 'Nip', 'numer_nip', 'tax_id'],
            'phone': ['phone', 'telefon', 'Telefon', 'tel', 'phone_number'],
            'email': ['email', 'Email', 'e-mail', 'E-mail', 'mail'],
            'company_name': ['company_name', 'nazwa', 'Nazwa', 'firma', 'name', 'NazwaSkrocona'],
            'legal_form': ['legal_form', 'forma_prawna', 'FormaPrawna', 'form'],
            'pkd': ['pkd', 'PKD', 'pkd_code', 'PkdGlowny', 'pkd_glowny'],
            'zip_code': ['zip_code', 'kod_pocztowy', 'KodPocztowy', 'postal_code', 'zip'],
            'city': ['city', 'miasto', 'Miasto', 'miejscowosc', 'Miejscowosc'],
            'voivodeship': ['voivodeship', 'wojewodztwo', 'Wojewodztwo', 'region'],
            'start_date': ['start_date', 'data_rozpoczecia', 'DataRozpoczeciaDzialalnosci', 'data_start']
        }
        
        df_columns_lower = {col.lower(): col for col in df_clean.columns}
        
        for target_col, possible_names in column_mappings.items():
            matched_col = None
            for name in possible_names:
                if name in df_clean.columns:
                    matched_col = name
                    break
                if name.lower() in df_columns_lower:
                    matched_col = df_columns_lower[name.lower()]
                    break
            
            if matched_col:
                if target_col == 'nip':
                    df_clean[f'{target_col}_clean'] = df_clean[matched_col].apply(self.clean_nip)
                elif target_col == 'phone':
                    df_clean[f'{target_col}_clean'] = df_clean[matched_col].apply(self.clean_phone)
                elif target_col == 'email':
                    df_clean[f'{target_col}_clean'] = df_clean[matched_col].apply(self.clean_email)
                elif target_col == 'zip_code':
                    df_clean[f'{target_col}_clean'] = df_clean[matched_col].apply(self.clean_zip_code)
                elif target_col == 'start_date':
                    df_clean[f'{target_col}_parsed'] = df_clean[matched_col].apply(self.parse_date)
                else:
                    df_clean[f'{target_col}_clean'] = df_clean[matched_col].astype(str).str.strip()
        
        logger.info(f"[SNIPER L0] Cleaning complete.")
        return df_clean
    
    # === LEVEL 1: LOCAL ENRICHMENT ===
    
    @staticmethod
    def get_wealth_score(zip_code: str) -> Tuple[int, str]:
        """Get wealth score from ZIP code prefix"""
        if not zip_code or len(zip_code) < 2:
            return WEALTH_MAP["DEFAULT"]
        prefix = zip_code[:2].replace("-", "")
        return WEALTH_MAP.get(prefix, WEALTH_MAP["DEFAULT"])
    
    @staticmethod
    def calculate_business_age(start_date: Optional[date]) -> Tuple[float, str]:
        """Calculate business age and leasing cycle stage"""
        if not start_date:
            return 0.0, LeasingCycle.UNKNOWN.value
        today = date.today()
        age_years = (today - start_date).days / 365.25
        if age_years < 2:
            cycle = LeasingCycle.STARTUP.value
        elif age_years < 4:
            cycle = LeasingCycle.GROWTH.value
        elif age_years < 7:
            cycle = LeasingCycle.MATURE.value
        else:
            cycle = LeasingCycle.ESTABLISHED.value
        return round(age_years, 2), cycle
    
    @staticmethod
    def get_pkd_leasing_propensity(pkd_code: str) -> Tuple[int, str]:
        """Get leasing propensity from PKD code"""
        if not pkd_code or len(pkd_code) < 2:
            return PKD_LEASING_MAP["DEFAULT"]
        prefix = re.sub(r'\D', '', str(pkd_code))[:2]
        return PKD_LEASING_MAP.get(prefix, PKD_LEASING_MAP["DEFAULT"])
    
    @staticmethod
    def get_industry_name(pkd_code: str) -> str:
        """Get human-readable industry name from PKD code"""
        if not pkd_code:
            return PKD_INDUSTRY_MAP["DEFAULT"]
        prefix = re.sub(r'\D', '', str(pkd_code))[:2]
        return PKD_INDUSTRY_MAP.get(prefix, PKD_INDUSTRY_MAP["DEFAULT"])
    
    @staticmethod
    def get_tax_benefit_score(legal_form: str) -> Tuple[int, Dict]:
        """Get tax benefit score and details from legal form"""
        if not legal_form:
            return TAX_BENEFIT_MAP["DEFAULT"]["score"], TAX_BENEFIT_MAP["DEFAULT"]
        form_upper = str(legal_form).upper().strip()
        if form_upper in TAX_BENEFIT_MAP:
            benefits = TAX_BENEFIT_MAP[form_upper]
            return benefits["score"], benefits
        for key in TAX_BENEFIT_MAP:
            if key in form_upper or form_upper in key:
                benefits = TAX_BENEFIT_MAP[key]
                return benefits["score"], benefits
        return TAX_BENEFIT_MAP["DEFAULT"]["score"], TAX_BENEFIT_MAP["DEFAULT"]
    
    @staticmethod
    def segment_tier(
        wealth_score: int,
        wealth_tier: str,
        business_age: float,
        leasing_cycle: str,
        pkd_propensity: int,
        tax_score: int
    ) -> Tuple[str, int, str]:
        """Segment lead into tier based on enrichment data"""
        score = 0
        reasons = []
        
        if wealth_tier == "PREMIUM":
            score += 30
            reasons.append("Premium location")
        elif wealth_tier == "HIGH":
            score += 22
            reasons.append("High-income area")
        elif wealth_tier == "MEDIUM":
            score += 14
            reasons.append("Medium-income area")
        else:
            score += 6
            reasons.append("Standard area")
        
        if leasing_cycle == LeasingCycle.MATURE.value:
            score += 25
            reasons.append("Leasing renewal cycle")
        elif leasing_cycle == LeasingCycle.ESTABLISHED.value:
            score += 20
            reasons.append("Established business")
        elif leasing_cycle == LeasingCycle.GROWTH.value:
            score += 15
            reasons.append("Growth phase")
        elif leasing_cycle == LeasingCycle.STARTUP.value:
            score += 5
            reasons.append("Startup")
        
        pkd_points = int(pkd_propensity * 0.25)
        score += pkd_points
        if pkd_propensity >= 80:
            reasons.append(f"High fleet need (PKD: {pkd_propensity})")
        elif pkd_propensity >= 60:
            reasons.append(f"Medium fleet need")
        
        tax_points = int(tax_score * 0.20)
        score += tax_points
        if tax_score >= 80:
            reasons.append("Strong EV tax benefits")
        
        if score >= 75:
            tier = LeadTier.TIER_S.value
        elif score >= 55:
            tier = LeadTier.TIER_A.value
        elif score >= 35:
            tier = LeadTier.TIER_B.value
        else:
            tier = LeadTier.TIER_C.value
        
        reasoning = " | ".join(reasons)
        return tier, score, reasoning
    
    def enrich_local(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Level 1: Local enrichment using dictionaries (Zero cost)"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for AssetSniper")
        
        logger.info(f"[SNIPER L1] Local enrichment for {len(df)} rows...")
        df_enriched = df.copy()
        
        # Find columns
        zip_col = 'zip_code_clean' if 'zip_code_clean' in df_enriched.columns else None
        date_col = 'start_date_parsed' if 'start_date_parsed' in df_enriched.columns else None
        pkd_col = 'pkd_clean' if 'pkd_clean' in df_enriched.columns else None
        form_col = 'legal_form_clean' if 'legal_form_clean' in df_enriched.columns else None
        
        if not zip_col:
            for col in df_enriched.columns:
                if 'zip' in col.lower() or 'kod' in col.lower() or 'postal' in col.lower():
                    zip_col = col
                    break
        
        if not pkd_col:
            for col in df_enriched.columns:
                if 'pkd' in col.lower():
                    pkd_col = col
                    break
        
        if not form_col:
            for col in df_enriched.columns:
                if 'form' in col.lower() or 'prawna' in col.lower():
                    form_col = col
                    break
        
        if not date_col:
            for col in df_enriched.columns:
                if 'data' in col.lower() and 'rozpocz' in col.lower():
                    date_col = col
                    break
        
        # Apply enrichment
        wealth_data = df_enriched[zip_col].apply(self.get_wealth_score) if zip_col else pd.Series([(6000, "STANDARD")] * len(df_enriched))
        df_enriched['Wealth_Score'] = wealth_data.apply(lambda x: x[0])
        df_enriched['Wealth_Tier'] = wealth_data.apply(lambda x: x[1])
        
        if date_col:
            if date_col == 'start_date_parsed':
                age_data = df_enriched[date_col].apply(self.calculate_business_age)
            else:
                age_data = df_enriched[date_col].apply(self.parse_date).apply(self.calculate_business_age)
        else:
            age_data = pd.Series([(0.0, LeasingCycle.UNKNOWN.value)] * len(df_enriched))
        
        df_enriched['Business_Age_Years'] = age_data.apply(lambda x: x[0])
        df_enriched['Leasing_Cycle'] = age_data.apply(lambda x: x[1])
        
        pkd_data = df_enriched[pkd_col].apply(self.get_pkd_leasing_propensity) if pkd_col else pd.Series([(50, "LOW")] * len(df_enriched))
        df_enriched['PKD_Propensity'] = pkd_data.apply(lambda x: x[0])
        df_enriched['PKD_Tier'] = pkd_data.apply(lambda x: x[1])
        
        # Industry name
        df_enriched['Industry_Name'] = df_enriched[pkd_col].apply(self.get_industry_name) if pkd_col else PKD_INDUSTRY_MAP["DEFAULT"]
        
        tax_data = df_enriched[form_col].apply(self.get_tax_benefit_score) if form_col else pd.Series([(50, {})] * len(df_enriched))
        df_enriched['Tax_Benefit_Score'] = tax_data.apply(lambda x: x[0])
        
        # Segment into tiers
        def segment_row(row):
            return self.segment_tier(
                wealth_score=row.get('Wealth_Score', 6000),
                wealth_tier=row.get('Wealth_Tier', 'STANDARD'),
                business_age=row.get('Business_Age_Years', 0),
                leasing_cycle=row.get('Leasing_Cycle', 'Unknown'),
                pkd_propensity=row.get('PKD_Propensity', 50),
                tax_score=row.get('Tax_Benefit_Score', 50)
            )
        
        tier_data = df_enriched.apply(segment_row, axis=1)
        df_enriched['Tier'] = tier_data.apply(lambda x: x[0])
        df_enriched['Tier_Score'] = tier_data.apply(lambda x: x[1])
        df_enriched['Tier_Reasoning'] = tier_data.apply(lambda x: x[2])
        
        def get_next_action(tier: str) -> str:
            actions = {
                LeadTier.TIER_S.value: "PRIORITY: Schedule discovery call within 24h",
                LeadTier.TIER_A.value: "HOT: Add to weekly outreach campaign",
                LeadTier.TIER_B.value: "WARM: Include in nurture sequence",
                LeadTier.TIER_C.value: "COLD: Add to newsletter list",
                LeadTier.UNKNOWN.value: "REVIEW: Manual data enrichment needed"
            }
            return actions.get(tier, "REVIEW: Unknown tier")
        
        df_enriched['Next_Action'] = df_enriched['Tier'].apply(get_next_action)
        df_enriched['Enrichment_Level'] = 1
        df_enriched['Data_Source'] = 'local'
        
        # Initialize v4.2 columns with defaults
        df_enriched['Annual_Tax_Saving'] = 0.0
        df_enriched['Charger_Distance_KM'] = 0.0
        df_enriched['Charger_Coverage'] = 'UNKNOWN'
        df_enriched['VAT_Recovery'] = 0.0
        df_enriched['NaszEauto_Subsidy'] = 0.0
        df_enriched['Client_DNA_Type'] = ClientDNAType.UNKNOWN.value
        df_enriched['DNA_Confidence'] = 0
        df_enriched['DNA_Reasoning'] = ''
        df_enriched['Market_Urgency_Score'] = 0
        df_enriched['Opportunity_Insight'] = ''
        df_enriched['Sniper_Hook'] = ''
        
        tier_counts = df_enriched['Tier'].value_counts()
        logger.info(f"[SNIPER L1] Enrichment complete. Tier distribution:")
        for tier, count in tier_counts.items():
            logger.info(f"  - {tier}: {count} ({count/len(df_enriched)*100:.1f}%)")
        
        return df_enriched
    
    # === LEVEL 2: DEEP ENRICHMENT WITH GOTHAM + BIGDECODER ===
    
    async def generate_dna_profile(
        self,
        company_name: str,
        pkd_code: str,
        industry_name: str,
        wealth_tier: str,
        legal_form: str
    ) -> Tuple[str, int, str]:
        """
        Generate psychographic DNA profile using BigDecoder (AnalysisEngine)
        
        Returns:
            Tuple of (dna_type, confidence, reasoning)
        """
        if not self.analysis_engine:
            # Palantir Fallback
            self._palantir_fallbacks += 1
            dna_type = PalantirTactics.estimate_dna_type(pkd_code, wealth_tier, legal_form)
            return dna_type, 50, f"[PALANTIR] Estimated from industry pattern: {industry_name}"
        
        prompt = f"""You are a B2B Sales Psychologist specializing in client profiling.

Analyze this company and determine their PRIMARY decision-making style:

COMPANY: {company_name}
INDUSTRY: {industry_name} (PKD: {pkd_code})
LOCATION TIER: {wealth_tier}
LEGAL FORM: {legal_form}

DECISION-MAKING STYLES:
1. ANALYTICAL - Data-driven, needs ROI proof, spreadsheets, comparisons
2. VISIONARY - Innovation-focused, early adopter, wants to be first
3. COST_DRIVEN - Price sensitive, TCO focused, needs savings proof
4. STATUS_SEEKER - Prestige focused, wants premium/exclusivity
5. PRAGMATIC - Practical, reliability focused, needs proven solutions

Based on the industry and profile, determine the MOST LIKELY style.

OUTPUT (JSON only, no other text):
{{
  "dna_type": "ANALYTICAL|VISIONARY|COST_DRIVEN|STATUS_SEEKER|PRAGMATIC",
  "confidence": 70,
  "reasoning": "Short explanation in Polish"
}}

JSON:
"""
        try:
            self._api_calls += 1
            result = await self.analysis_engine._call_ollama(prompt)
            
            if result and isinstance(result, dict):
                dna_type = result.get('dna_type', 'PRAGMATIC')
                confidence = result.get('confidence', 60)
                reasoning = result.get('reasoning', 'AI analysis')
                
                # Normalize dna_type to enum value
                dna_map = {
                    'ANALYTICAL': ClientDNAType.ANALYTICAL.value,
                    'VISIONARY': ClientDNAType.VISIONARY.value,
                    'COST_DRIVEN': ClientDNAType.COST_DRIVEN.value,
                    'COST-DRIVEN': ClientDNAType.COST_DRIVEN.value,
                    'STATUS_SEEKER': ClientDNAType.STATUS_SEEKER.value,
                    'STATUS-SEEKER': ClientDNAType.STATUS_SEEKER.value,
                    'PRAGMATIC': ClientDNAType.PRAGMATIC.value
                }
                dna_type = dna_map.get(dna_type.upper(), ClientDNAType.PRAGMATIC.value)
                
                return dna_type, min(100, max(0, confidence)), reasoning
            
            # Fallback if parsing fails
            self._palantir_fallbacks += 1
            dna_type = PalantirTactics.estimate_dna_type(pkd_code, wealth_tier, legal_form)
            return dna_type, 50, f"[PALANTIR] Fallback estimation"
            
        except Exception as e:
            logger.error(f"[SNIPER DNA] Error: {e}")
            self._palantir_fallbacks += 1
            dna_type = PalantirTactics.estimate_dna_type(pkd_code, wealth_tier, legal_form)
            return dna_type, 40, f"[PALANTIR] Error fallback: {str(e)[:30]}"
    
    async def generate_sniper_hook(
        self,
        company_name: str,
        pkd_code: str,
        industry_name: str,
        city: str,
        dna_type: str,
        annual_tax_saving: float,
        charger_distance_km: float,
        wealth_tier: str
    ) -> str:
        """
        Generate AI-powered cold call hook with GOTHAM hard data + DNA profile
        
        The hook MUST include:
        1. Specific hard data (tax savings, charger distance)
        2. Language adapted to DNA type
        3. Polish language
        """
        if not self.analysis_engine:
            # Palantir Fallback - Generate template-based hook
            self._palantir_fallbacks += 1
            return self._generate_fallback_hook(
                company_name, industry_name, city, dna_type, 
                annual_tax_saving, charger_distance_km
            )
        
        # DNA-specific language guidance
        dna_language = {
            ClientDNAType.ANALYTICAL.value: "Use numbers, ROI, data. Be precise and factual.",
            ClientDNAType.VISIONARY.value: "Focus on innovation, being first, technology leadership.",
            ClientDNAType.COST_DRIVEN.value: "Lead with savings, TCO reduction, efficiency.",
            ClientDNAType.STATUS_SEEKER.value: "Emphasize prestige, exclusivity, premium positioning.",
            ClientDNAType.PRAGMATIC.value: "Focus on reliability, proven solutions, practicality."
        }
        
        language_guide = dna_language.get(dna_type, dna_language[ClientDNAType.PRAGMATIC.value])
        
        prompt = f"""Jesteś ekspertem B2B copywriterem specjalizującym się w sprzedaży flot Tesla.

Wygeneruj 1-zdaniowy, spersonalizowany hook do cold call dla tej firmy:

DANE FIRMY:
- Nazwa: {company_name}
- Branża: {industry_name} (PKD: {pkd_code})
- Lokalizacja: {city}
- Poziom zamożności: {wealth_tier}

TWARDE DANE GOTHAM:
- Roczne oszczędności podatkowe: {annual_tax_saving:,.0f} PLN
- Najbliższa ładowarka: {charger_distance_km:.1f} km od biura

PROFIL DNA KLIENTA: {dna_type}
STYL KOMUNIKACJI: {language_guide}

ZASADY:
1. MUSI zawierać przynajmniej jedną konkretną liczbę (oszczędności LUB odległość ładowarki)
2. MUSI być dopasowany do profilu DNA
3. Maksymalnie 30 słów
4. Polski język
5. Brzmi naturalnie, nie jak skrypt

PRZYKŁADY DOBRYCH HOOKÓW:
- [ANALYTICAL] "Dzień dobry, jako firma IT z Katowic możecie odliczyć 42 000 PLN podatku rocznie, a ładowarkę macie 300 metrów od biura."
- [COST_DRIVEN] "Widzę że w logistyce paliwo zjada marżę - mogę pokazać jak obniżyć koszty floty o 38 000 PLN rocznie?"
- [VISIONARY] "Jako innowacyjna firma technologiczna z Warszawy, chcielibyście być pierwszymi z flotą Tesla w branży?"

TWÓJ HOOK (JSON):
{{"hook": "Twój hook tutaj"}}

JSON:
"""
        try:
            self._api_calls += 1
            result = await self.analysis_engine._call_ollama(prompt)
            
            if result:
                if isinstance(result, dict):
                    hook = result.get('hook', str(result))
                else:
                    hook = str(result)
                
                hook = hook.strip().strip('"').strip()
                
                # Validate hook contains data
                if str(int(annual_tax_saving)) not in hook and str(charger_distance_km) not in hook:
                    # Add data if missing
                    hook = f"{hook} (oszczędność {annual_tax_saving:,.0f} PLN/rok)"
                
                return hook[:300]
            
            return self._generate_fallback_hook(
                company_name, industry_name, city, dna_type,
                annual_tax_saving, charger_distance_km
            )
            
        except Exception as e:
            logger.error(f"[SNIPER HOOK] Error: {e}")
            self._palantir_fallbacks += 1
            return self._generate_fallback_hook(
                company_name, industry_name, city, dna_type,
                annual_tax_saving, charger_distance_km
            )
    
    def _generate_fallback_hook(
        self,
        company_name: str,
        industry_name: str,
        city: str,
        dna_type: str,
        annual_tax_saving: float,
        charger_distance_km: float
    ) -> str:
        """Generate template-based hook when AI unavailable (Palantir Tactics)"""
        templates = {
            ClientDNAType.ANALYTICAL.value: f"Dzień dobry, według naszej analizy firma z branży {industry_name} może zaoszczędzić {annual_tax_saving:,.0f} PLN rocznie na flocie elektrycznej. Najbliższa ładowarka jest {charger_distance_km:.1f} km od {city}.",
            ClientDNAType.VISIONARY.value: f"Dzień dobry, czy {company_name} chce być liderem innowacji w {industry_name}? Tesla oferuje oszczędności {annual_tax_saving:,.0f} PLN/rok.",
            ClientDNAType.COST_DRIVEN.value: f"Dzień dobry, mogę pokazać jak obniżyć koszty floty o {annual_tax_saving:,.0f} PLN rocznie? Ładowarka tylko {charger_distance_km:.1f} km od biura.",
            ClientDNAType.STATUS_SEEKER.value: f"Dzień dobry, Tesla to prestiż i {annual_tax_saving:,.0f} PLN oszczędności rocznie. Ładowarka premium {charger_distance_km:.1f} km od {city}.",
            ClientDNAType.PRAGMATIC.value: f"Dzień dobry, Tesla to sprawdzone rozwiązanie z oszczędnością {annual_tax_saving:,.0f} PLN/rok. Ładowarka {charger_distance_km:.1f} km od biura."
        }
        
        return templates.get(dna_type, templates[ClientDNAType.PRAGMATIC.value])
    
    async def enrich_tier_s(self, df: 'pd.DataFrame', batch_size: int = 3) -> 'pd.DataFrame':
        """
        Level 2: Deep enrichment for Tier S (and Tier A) leads
        
        GOTHAM Integration:
        - Charger infrastructure lookup
        - Tax potential calculation
        - Market opportunity score
        
        BigDecoder Integration:
        - Psychographic DNA profiling
        - Personalized hook generation
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for AssetSniper")
        
        df_enriched = df.copy()
        
        # Get Tier S and Tier A leads (both get deep enrichment)
        tier_mask = (df_enriched['Tier'] == LeadTier.TIER_S.value) | (df_enriched['Tier'] == LeadTier.TIER_A.value)
        target_indices = df_enriched[tier_mask].index.tolist()
        
        if not target_indices:
            logger.info("[SNIPER L2] No Tier S/A leads to enrich")
            return df_enriched
        
        logger.info(f"[SNIPER L2] Deep enriching {len(target_indices)} Tier S/A leads...")
        
        # Find relevant columns
        name_col = None
        pkd_col = None
        city_col = None
        form_col = None
        voiv_col = None
        
        for col in df_enriched.columns:
            col_lower = col.lower()
            if 'name' in col_lower or 'nazwa' in col_lower:
                name_col = col
            if 'pkd' in col_lower:
                pkd_col = col
            if 'city' in col_lower or 'miasto' in col_lower or 'miejscow' in col_lower:
                city_col = col
            if 'form' in col_lower or 'prawna' in col_lower:
                form_col = col
            if 'wojewod' in col_lower or 'voivode' in col_lower or 'region' in col_lower:
                voiv_col = col
        
        # Import SniperGateway if not provided
        if not self.gotham_gateway:
            try:
                from backend.gotham_module import SniperGateway
                self.gotham_gateway = SniperGateway
            except ImportError:
                logger.warning("[SNIPER L2] SniperGateway not available - using Palantir Tactics only")
        
        # Process in batches
        for i in range(0, len(target_indices), batch_size):
            batch_indices = target_indices[i:i + batch_size]
            logger.info(f"[SNIPER L2] Processing batch {i//batch_size + 1}/{(len(target_indices) + batch_size - 1)//batch_size}")
            
            for idx in batch_indices:
                row = df_enriched.loc[idx]
                
                # Extract row data
                company_name = str(row.get(name_col, "Unknown")) if name_col else "Unknown"
                pkd_code = str(row.get(pkd_col, "")) if pkd_col else ""
                city = str(row.get(city_col, "")) if city_col else ""
                legal_form = str(row.get(form_col, "")) if form_col else ""
                voivodeship = str(row.get(voiv_col, "ŚLĄSKIE")) if voiv_col else "ŚLĄSKIE"
                wealth_tier = str(row.get('Wealth_Tier', 'STANDARD'))
                tier_score = row.get('Tier_Score', 50)
                leasing_cycle = str(row.get('Leasing_Cycle', 'Unknown'))
                industry_name = str(row.get('Industry_Name', 'Działalność gospodarcza'))
                
                try:
                    # === GOTHAM INTEGRATION ===
                    if self.gotham_gateway:
                        try:
                            # Get charger infrastructure
                            self._api_calls += 1
                            charger_data = self.gotham_gateway.check_charger_infrastructure(city=city)
                            charger_distance = charger_data.get('nearest_supercharger_km', 0) or 0
                            charger_coverage = charger_data.get('coverage_level', 'UNKNOWN')
                            charger_count = charger_data.get('charger_count', 0)
                            
                            # Get tax potential
                            self._api_calls += 1
                            tax_data = self.gotham_gateway.calculate_tax_potential(
                                pkd_code=pkd_code,
                                legal_form=legal_form,
                                estimated_annual_km=25000
                            )
                            annual_tax_saving = tax_data.get('total_first_year_benefit', 0)
                            vat_recovery = tax_data.get('vat_recovery', 0)
                            naszeauto = tax_data.get('naszeauto_subsidy', 18750)
                            
                            # Get market opportunity
                            self._api_calls += 1
                            opportunity_data = self.gotham_gateway.get_lead_context(
                                city=city,
                                pkd_code=pkd_code,
                                legal_form=legal_form,
                                region=voivodeship
                            )
                            market_urgency = int(opportunity_data.get('combined_score', 50))
                            opportunity_insight = opportunity_data.get('opportunity_score', {}).get('insight', '')
                            
                            data_source = 'api'
                            
                        except Exception as gotham_error:
                            logger.warning(f"[SNIPER L2] GOTHAM error for {company_name}: {gotham_error}")
                            # Palantir Fallback
                            self._palantir_fallbacks += 1
                            charger_distance = PalantirTactics.estimate_charger_distance(city, wealth_tier)
                            charger_coverage = 'MEDIUM'
                            charger_count = 10
                            annual_tax_saving = PalantirTactics.estimate_annual_tax_saving(legal_form, pkd_code)
                            vat_recovery = annual_tax_saving * 0.15
                            naszeauto = 27000 if 'SPÓŁKA' in legal_form.upper() else 18750
                            market_urgency = PalantirTactics.estimate_market_urgency(tier_score, leasing_cycle)
                            opportunity_insight = f"[PALANTIR] Szacunkowe dane dla {city}"
                            data_source = 'palantir'
                    else:
                        # Full Palantir mode
                        self._palantir_fallbacks += 1
                        charger_distance = PalantirTactics.estimate_charger_distance(city, wealth_tier)
                        charger_coverage = 'MEDIUM'
                        charger_count = 10
                        annual_tax_saving = PalantirTactics.estimate_annual_tax_saving(legal_form, pkd_code)
                        vat_recovery = annual_tax_saving * 0.15
                        naszeauto = 27000 if 'SPÓŁKA' in legal_form.upper() else 18750
                        market_urgency = PalantirTactics.estimate_market_urgency(tier_score, leasing_cycle)
                        opportunity_insight = f"[PALANTIR] Szacunkowe dane dla {city}"
                        data_source = 'palantir'
                    
                    # === BIGDECODER DNA PROFILING ===
                    dna_type, dna_confidence, dna_reasoning = await self.generate_dna_profile(
                        company_name=company_name,
                        pkd_code=pkd_code,
                        industry_name=industry_name,
                        wealth_tier=wealth_tier,
                        legal_form=legal_form
                    )
                    
                    # === SNIPER HOOK GENERATION ===
                    # Only for Tier S leads
                    if row['Tier'] == LeadTier.TIER_S.value:
                        sniper_hook = await self.generate_sniper_hook(
                            company_name=company_name,
                            pkd_code=pkd_code,
                            industry_name=industry_name,
                            city=city,
                            dna_type=dna_type,
                            annual_tax_saving=annual_tax_saving,
                            charger_distance_km=charger_distance,
                            wealth_tier=wealth_tier
                        )
                    else:
                        sniper_hook = ""
                    
                    # Update DataFrame
                    df_enriched.at[idx, 'Annual_Tax_Saving'] = annual_tax_saving
                    df_enriched.at[idx, 'Charger_Distance_KM'] = charger_distance
                    df_enriched.at[idx, 'Charger_Coverage'] = charger_coverage
                    df_enriched.at[idx, 'VAT_Recovery'] = vat_recovery
                    df_enriched.at[idx, 'NaszEauto_Subsidy'] = naszeauto
                    df_enriched.at[idx, 'Client_DNA_Type'] = dna_type
                    df_enriched.at[idx, 'DNA_Confidence'] = dna_confidence
                    df_enriched.at[idx, 'DNA_Reasoning'] = dna_reasoning
                    df_enriched.at[idx, 'Market_Urgency_Score'] = market_urgency
                    df_enriched.at[idx, 'Opportunity_Insight'] = opportunity_insight
                    df_enriched.at[idx, 'Sniper_Hook'] = sniper_hook
                    df_enriched.at[idx, 'Enrichment_Level'] = 2
                    df_enriched.at[idx, 'Data_Source'] = data_source
                    
                    logger.info(f"[SNIPER L2] ✓ {company_name[:30]} | DNA: {dna_type} | Tax: {annual_tax_saving:,.0f} PLN | Charger: {charger_distance}km")
                    
                except Exception as e:
                    logger.error(f"[SNIPER L2] Error enriching {company_name}: {e}")
                    df_enriched.at[idx, 'Sniper_Hook'] = f"[ERROR] {str(e)[:50]}"
                    df_enriched.at[idx, 'Data_Source'] = 'error'
            
            # Small delay between batches to avoid overloading
            await asyncio.sleep(0.5)
        
        logger.info(f"[SNIPER L2] Deep enrichment complete. API calls: {self._api_calls}, Palantir fallbacks: {self._palantir_fallbacks}")
        return df_enriched
    
    # === MAIN PIPELINE ===
    
    async def process_csv(
        self,
        df: 'pd.DataFrame',
        enable_deep_enrichment: bool = True,
        chunk_size: int = 1000
    ) -> Tuple['pd.DataFrame', SniperStats]:
        """Main processing pipeline with GOTHAM + BigDecoder integration"""
        import time
        start_time = time.time()
        
        self._api_calls = 0
        self._palantir_fallbacks = 0
        
        stats = SniperStats(total_rows=len(df))
        
        logger.info(f"[ASSET SNIPER v4.2] Starting pipeline for {len(df)} rows")
        
        # Process in chunks if large file
        if len(df) > chunk_size:
            logger.info(f"[ASSET SNIPER] Processing in chunks of {chunk_size}")
            chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
            processed_chunks = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"[ASSET SNIPER] Processing chunk {i+1}/{len(chunks)}")
                chunk_clean = self.clean_data(chunk)
                chunk_enriched = self.enrich_local(chunk_clean)
                processed_chunks.append(chunk_enriched)
            
            df_enriched = pd.concat(processed_chunks, ignore_index=True)
        else:
            df_clean = self.clean_data(df)
            df_enriched = self.enrich_local(df_clean)
        
        # Level 2: Deep enrichment (Tier S and Tier A)
        if enable_deep_enrichment:
            df_enriched = await self.enrich_tier_s(df_enriched)
        
        # Calculate stats
        stats.processed_rows = len(df_enriched)
        stats.tier_s_count = len(df_enriched[df_enriched['Tier'] == LeadTier.TIER_S.value])
        stats.tier_a_count = len(df_enriched[df_enriched['Tier'] == LeadTier.TIER_A.value])
        stats.tier_b_count = len(df_enriched[df_enriched['Tier'] == LeadTier.TIER_B.value])
        stats.tier_c_count = len(df_enriched[df_enriched['Tier'] == LeadTier.TIER_C.value])
        stats.unknown_tier_count = len(df_enriched[df_enriched['Tier'] == LeadTier.UNKNOWN.value])
        
        if 'Wealth_Score' in df_enriched.columns:
            stats.avg_wealth_score = df_enriched['Wealth_Score'].mean()
        
        if 'Annual_Tax_Saving' in df_enriched.columns:
            tier_s_df = df_enriched[df_enriched['Tier'] == LeadTier.TIER_S.value]
            if len(tier_s_df) > 0:
                stats.avg_tax_saving = tier_s_df['Annual_Tax_Saving'].mean()
                stats.avg_charger_distance = tier_s_df['Charger_Distance_KM'].mean()
        
        if 'Client_DNA_Type' in df_enriched.columns:
            stats.top_dna_types = df_enriched[df_enriched['Client_DNA_Type'] != ClientDNAType.UNKNOWN.value]['Client_DNA_Type'].value_counts().head(5).to_dict()
        
        for col in df_enriched.columns:
            if 'wojewod' in col.lower() or 'voivode' in col.lower():
                stats.top_voivodeships = df_enriched[col].value_counts().head(5).to_dict()
                break
        
        stats.processing_time_ms = int((time.time() - start_time) * 1000)
        stats.api_calls_made = self._api_calls
        stats.palantir_fallbacks = self._palantir_fallbacks
        
        logger.info(f"[ASSET SNIPER v4.2] Pipeline complete in {stats.processing_time_ms}ms")
        logger.info(f"[ASSET SNIPER] Tier S={stats.tier_s_count}, Tier A={stats.tier_a_count}")
        logger.info(f"[ASSET SNIPER] API calls={stats.api_calls_made}, Palantir fallbacks={stats.palantir_fallbacks}")
        
        return df_enriched, stats
    
    def process_csv_sync(
        self,
        df: 'pd.DataFrame',
        enable_deep_enrichment: bool = False
    ) -> Tuple['pd.DataFrame', SniperStats]:
        """Synchronous wrapper for process_csv (local enrichment only)"""
        import time
        start_time = time.time()
        
        stats = SniperStats(total_rows=len(df))
        
        df_clean = self.clean_data(df)
        df_enriched = self.enrich_local(df_clean)
        
        stats.processed_rows = len(df_enriched)
        stats.tier_s_count = len(df_enriched[df_enriched['Tier'] == LeadTier.TIER_S.value])
        stats.tier_a_count = len(df_enriched[df_enriched['Tier'] == LeadTier.TIER_A.value])
        stats.tier_b_count = len(df_enriched[df_enriched['Tier'] == LeadTier.TIER_B.value])
        stats.tier_c_count = len(df_enriched[df_enriched['Tier'] == LeadTier.TIER_C.value])
        stats.unknown_tier_count = len(df_enriched[df_enriched['Tier'] == LeadTier.UNKNOWN.value])
        
        if 'Wealth_Score' in df_enriched.columns:
            stats.avg_wealth_score = df_enriched['Wealth_Score'].mean()
        
        stats.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return df_enriched, stats


# === SINGLETON INSTANCE ===

asset_sniper = AssetSniper()


# === CLI TEST ===

if __name__ == "__main__":
    print("=== ASSET SNIPER v4.2 Module Test ===\n")
    
    if not PANDAS_AVAILABLE:
        print("ERROR: pandas not installed. Run: pip install pandas")
        exit(1)
    
    # Create test data
    test_data = {
        'NIP': ['5272829917', '123-456-78-90', 'invalid', '5261040828'],
        'Telefon': ['+48 500 100 200', '500100200', '48500100200', 'bad'],
        'Email': ['test@example.com', 'invalid', 'hello@firma.pl', ''],
        'Nazwa': ['Tech Solutions Sp. z o.o.', 'Auto-Trans Logistics', 'StartupXYZ', 'Premium Consulting'],
        'FormaPrawna': ['SPÓŁKA Z O.O.', 'JEDNOOSOBOWA DZIAŁALNOŚĆ', 'SPÓŁKA Z O.O.', 'SPÓŁKA KOMANDYTOWA'],
        'PkdGlowny': ['62.01.Z', '49.41.Z', '73.11.Z', '70.22.Z'],
        'KodPocztowy': ['02-677', '40-001', '90-001', '81-300'],
        'Miejscowosc': ['Warszawa', 'Katowice', 'Łódź', 'Sopot'],
        'Wojewodztwo': ['MAZOWIECKIE', 'ŚLĄSKIE', 'ŁÓDZKIE', 'POMORSKIE'],
        'DataRozpoczeciaDzialalnosci': ['2019-03-15', '2015-08-20', '2023-01-10', '2018-06-01']
    }
    
    df_test = pd.DataFrame(test_data)
    
    print("Input data:")
    print(df_test)
    print("\n" + "="*60 + "\n")
    
    # Test Palantir Tactics
    print("Testing Palantir Tactics (fallback estimations):")
    print(f"  - Charger distance (Warszawa, PREMIUM): {PalantirTactics.estimate_charger_distance('Warszawa', 'PREMIUM')} km")
    print(f"  - Tax saving (Sp. z o.o., IT): {PalantirTactics.estimate_annual_tax_saving('SPÓŁKA Z O.O.', '62.01.Z'):,.0f} PLN")
    print(f"  - DNA type (IT, PREMIUM): {PalantirTactics.estimate_dna_type('62', 'PREMIUM', 'SPÓŁKA Z O.O.')}")
    print()
    
    # Process
    sniper = AssetSniper()
    df_result, stats = sniper.process_csv_sync(df_test)
    
    print("Enriched data (key columns):")
    key_cols = ['Nazwa', 'Tier', 'Tier_Score', 'Wealth_Tier', 'Industry_Name', 'Next_Action']
    print(df_result[[c for c in key_cols if c in df_result.columns]])
    
    print("\n" + "="*60)
    print(f"\nStatistics:")
    print(f"  - Total rows: {stats.total_rows}")
    print(f"  - Processed: {stats.processed_rows}")
    print(f"  - Tier S: {stats.tier_s_count}")
    print(f"  - Tier A: {stats.tier_a_count}")
    print(f"  - Tier B: {stats.tier_b_count}")
    print(f"  - Tier C: {stats.tier_c_count}")
    print(f"  - Avg Wealth Score: {stats.avg_wealth_score:,.0f} PLN")
    print(f"  - Processing time: {stats.processing_time_ms}ms")
    print("\n✅ ASSET SNIPER v4.2 Test Complete!")
