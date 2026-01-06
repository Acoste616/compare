"""
ASSET SNIPER Module (ULTRA v4.1)
Data Refinery for CEIDG Leads Processing

FEATURES:
- Level 0 (Ingest): Clean dirty CSV data (NIP, Phones)
- Level 1 (Local/Free): Instant segmentation using local logic (ZipCode -> Wealth Mapping, BusinessAge -> LeasingCycle)
- Level 2 (API/Slow): Deep analysis via Ollama for Tier S leads only

WATERFALL ENRICHMENT SYSTEM:
- Zero-Cost First: Prioritize local dictionary lookups over API calls
- Robustness: System must not crash if one row in CSV is malformed
- Privacy: All data processed locally/on-prem

Author: Lead Architect
Version: 1.0.0
"""

import re
import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

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


# === WEALTH MAP (Polish ZIP Code Prefixes -> Estimated Avg Income) ===
# Based on GUS data and real estate market analysis
# Format: ZIP_PREFIX -> (avg_monthly_income_PLN, wealth_tier)

WEALTH_MAP: Dict[str, Tuple[int, str]] = {
    # WARSAW (00-04) - Highest income zone
    "00": (12500, "PREMIUM"),   # Śródmieście (Center)
    "01": (11000, "PREMIUM"),   # Wola
    "02": (13500, "PREMIUM"),   # Mokotów (highest)
    "03": (10500, "HIGH"),      # Praga-Północ
    "04": (9500, "HIGH"),       # Praga-Południe
    
    # KRAKÓW (30-32) - Major tech hub
    "30": (10000, "HIGH"),      # Old Town / Center
    "31": (9500, "HIGH"),       # Krowodrza
    "32": (8500, "MEDIUM"),     # Nowa Huta
    
    # WROCŁAW (50-54) - IT capital
    "50": (9500, "HIGH"),       # Center
    "51": (9000, "HIGH"),       # Krzyki
    "52": (8000, "MEDIUM"),     # Fabryczna
    "53": (8500, "MEDIUM"),     # Psie Pole
    "54": (7500, "MEDIUM"),     # Suburban
    
    # POZNAŃ (60-64)
    "60": (9000, "HIGH"),       # Stare Miasto
    "61": (8500, "MEDIUM"),     # Grunwald
    "62": (7500, "MEDIUM"),     # Suburban
    
    # GDAŃSK-SOPOT-GDYNIA (80-84) - Tri-City
    "80": (9500, "HIGH"),       # Gdańsk Center
    "81": (12000, "PREMIUM"),   # Sopot (resort town)
    "82": (9000, "HIGH"),       # Gdynia Center
    
    # KATOWICE / ŚLĄSK (40-44) - Industrial + EV opportunity
    "40": (8500, "MEDIUM"),     # Katowice Center
    "41": (8000, "MEDIUM"),     # Chorzów, Bytom
    "42": (7500, "MEDIUM"),     # Sosnowiec
    "43": (7000, "MEDIUM"),     # Tychy, Bielsko
    "44": (7500, "MEDIUM"),     # Gliwice
    
    # ŁÓDŹ (90-94)
    "90": (7500, "MEDIUM"),     # Center
    "91": (7000, "MEDIUM"),     # Bałuty
    "92": (6500, "STANDARD"),   # Widzew
    "93": (7000, "MEDIUM"),     # Górna
    "94": (6500, "STANDARD"),   # Polesie
    
    # DEFAULT for unlisted prefixes
    "DEFAULT": (6000, "STANDARD"),
}


# === PKD CODE -> LEASING PROPENSITY MAP ===
# Higher score = more likely to need company cars / fleet

PKD_LEASING_MAP: Dict[str, Tuple[int, str]] = {
    # TRANSPORT & LOGISTICS (Highest propensity)
    "49": (95, "VERY_HIGH"),    # Land transport
    "50": (90, "VERY_HIGH"),    # Water transport
    "51": (85, "HIGH"),         # Air transport
    "52": (90, "VERY_HIGH"),    # Warehousing & logistics
    "53": (95, "VERY_HIGH"),    # Postal & courier
    
    # SALES & FIELD WORK
    "46": (85, "HIGH"),         # Wholesale trade
    "47": (70, "MEDIUM"),       # Retail trade
    "45": (90, "VERY_HIGH"),    # Car trade & repair (!)
    
    # PROFESSIONAL SERVICES (Fleet for managers)
    "62": (75, "HIGH"),         # IT services
    "63": (70, "MEDIUM"),       # Information services
    "64": (80, "HIGH"),         # Financial services
    "69": (75, "HIGH"),         # Legal & accounting
    "70": (80, "HIGH"),         # Consulting
    "71": (75, "HIGH"),         # Architecture & engineering
    "72": (65, "MEDIUM"),       # R&D
    "73": (70, "MEDIUM"),       # Advertising & marketing
    
    # CONSTRUCTION (Fleet need)
    "41": (80, "HIGH"),         # Building construction
    "42": (85, "HIGH"),         # Civil engineering
    "43": (80, "HIGH"),         # Specialized construction
    
    # HEALTHCARE (Doctors, medical reps)
    "86": (70, "MEDIUM"),       # Healthcare
    "87": (60, "MEDIUM"),       # Social care
    
    # REAL ESTATE (High income, fleet likely)
    "68": (85, "HIGH"),         # Real estate
    
    # MANUFACTURING (Fleet for sales/logistics)
    "10": (65, "MEDIUM"),       # Food
    "20": (70, "MEDIUM"),       # Chemicals
    "25": (70, "MEDIUM"),       # Metal products
    "26": (75, "HIGH"),         # Electronics
    "28": (75, "HIGH"),         # Machinery
    "29": (90, "VERY_HIGH"),    # Automotive (!)
    
    # DEFAULT
    "DEFAULT": (50, "LOW"),
}


# === TAX BENEFIT MAP (Legal form -> EV tax benefits) ===

TAX_BENEFIT_MAP: Dict[str, Dict[str, Any]] = {
    "SPÓŁKA Z O.O.": {
        "vat_deduction": 100,      # Full VAT deduction for company cars
        "leasing_kup": 100,        # Full lease as cost
        "ev_bonus": 27000,         # NaszEauto max (without KDR)
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
        "vat_deduction": 50,       # 50% VAT for mixed use
        "leasing_kup": 75,         # Partial cost recognition
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
        "ev_bonus": 18750,         # Standard NaszEauto
        "depreciation_boost": False,
        "score": 50
    }
}


# === DATA CLASSES ===

@dataclass
class EnrichedLead:
    """Single enriched lead with all calculated fields"""
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
    sniper_hook: str = ""  # AI-generated cold call hook
    
    # Metadata
    next_action: str = ""
    processing_errors: List[str] = field(default_factory=list)
    enrichment_level: int = 0  # 0=raw, 1=local, 2=full


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
    top_voivodeships: Dict[str, int] = field(default_factory=dict)
    processing_time_ms: int = 0


# === ASSET SNIPER CLASS ===

class AssetSniper:
    """
    Data Refinery for CEIDG Leads Processing
    
    Waterfall Enrichment System:
    1. Level 0 (Ingest): Clean dirty CSV data
    2. Level 1 (Local/Free): Instant segmentation using local logic
    3. Level 2 (API/Slow): Deep analysis via Ollama for Tier S leads only
    """
    
    def __init__(self, analysis_engine=None, gotham_module=None):
        """
        Initialize Asset Sniper
        
        Args:
            analysis_engine: Optional AnalysisEngine instance for Ollama integration
            gotham_module: Optional GothamIntelligence for tax/charger lookups
        """
        self.analysis_engine = analysis_engine
        self.gotham_module = gotham_module
        logger.info("[ASSET SNIPER] Initialized")
    
    # === LEVEL 0: DATA CLEANING ===
    
    @staticmethod
    def clean_nip(nip: Any) -> str:
        """
        Clean and validate Polish NIP number
        
        Rules:
        - Remove all non-digits
        - Must be exactly 10 digits
        - Validate checksum (modulo 11)
        """
        if pd is None or pd.isna(nip):
            return ""
        
        # Convert to string and remove non-digits
        nip_str = re.sub(r'\D', '', str(nip))
        
        # Must be 10 digits
        if len(nip_str) != 10:
            return ""
        
        # NIP checksum validation (weights: 6,5,7,2,3,4,5,6,7)
        weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(nip_str[i]) * weights[i] for i in range(9)) % 11
        
        if checksum != int(nip_str[9]):
            return ""  # Invalid NIP
        
        return nip_str
    
    @staticmethod
    def clean_phone(phone: Any) -> str:
        """
        Clean and normalize Polish phone number
        
        Rules:
        - Remove all non-digits
        - Handle +48 prefix
        - Must be 9 digits (Polish mobile/landline)
        """
        if pd is None or pd.isna(phone):
            return ""
        
        # Convert to string and remove non-digits
        phone_str = re.sub(r'\D', '', str(phone))
        
        # Remove Polish country code if present
        if phone_str.startswith('48') and len(phone_str) == 11:
            phone_str = phone_str[2:]
        elif phone_str.startswith('048') and len(phone_str) == 12:
            phone_str = phone_str[3:]
        
        # Must be 9 digits
        if len(phone_str) != 9:
            return ""
        
        # Format as XXX-XXX-XXX
        return f"{phone_str[:3]}-{phone_str[3:6]}-{phone_str[6:]}"
    
    @staticmethod
    def clean_zip_code(zip_code: Any) -> str:
        """
        Clean Polish postal code
        
        Format: XX-XXX
        """
        if pd is None or pd.isna(zip_code):
            return ""
        
        # Remove non-digits
        zip_str = re.sub(r'\D', '', str(zip_code))
        
        # Must be 5 digits
        if len(zip_str) != 5:
            return ""
        
        return f"{zip_str[:2]}-{zip_str[2:]}"
    
    @staticmethod
    def clean_email(email: Any) -> str:
        """Clean and validate email address"""
        if pd is None or pd.isna(email):
            return ""
        
        email_str = str(email).strip().lower()
        
        # Basic email validation
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email_str):
            return email_str
        
        return ""
    
    @staticmethod
    def parse_date(date_val: Any) -> Optional[date]:
        """Parse date from various formats"""
        if pd is None or pd.isna(date_val):
            return None
        
        date_str = str(date_val).strip()
        
        # Try common Polish date formats
        formats = [
            "%Y-%m-%d",      # 2020-01-15
            "%d-%m-%Y",      # 15-01-2020
            "%d.%m.%Y",      # 15.01.2020
            "%Y/%m/%d",      # 2020/01/15
            "%d/%m/%Y",      # 15/01/2020
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def clean_data(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """
        Level 0: Clean raw CSV data
        
        Operations:
        - Normalize phone numbers
        - Validate NIP numbers
        - Clean postal codes
        - Validate emails
        - Parse dates
        - Strip whitespace from all text fields
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for AssetSniper. Install with: pip install pandas")
        
        logger.info(f"[SNIPER L0] Cleaning {len(df)} rows...")
        
        # Create copy to avoid modifying original
        df_clean = df.copy()
        
        # Column mapping (handle various CSV column names)
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
        
        # Normalize column names
        df_columns_lower = {col.lower(): col for col in df_clean.columns}
        
        # Apply cleaners to matched columns
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
                    # Strip whitespace for text fields
                    df_clean[f'{target_col}_clean'] = df_clean[matched_col].astype(str).str.strip()
        
        logger.info(f"[SNIPER L0] Cleaning complete. Added {sum(1 for c in df_clean.columns if '_clean' in c or '_parsed' in c)} new columns.")
        
        return df_clean
    
    # === LEVEL 1: LOCAL ENRICHMENT ===
    
    @staticmethod
    def get_wealth_score(zip_code: str) -> Tuple[int, str]:
        """
        Get wealth score from ZIP code prefix
        
        Returns:
            Tuple of (avg_income, wealth_tier)
        """
        if not zip_code or len(zip_code) < 2:
            return WEALTH_MAP["DEFAULT"]
        
        prefix = zip_code[:2].replace("-", "")
        return WEALTH_MAP.get(prefix, WEALTH_MAP["DEFAULT"])
    
    @staticmethod
    def calculate_business_age(start_date: Optional[date]) -> Tuple[float, str]:
        """
        Calculate business age and determine leasing cycle stage
        
        Returns:
            Tuple of (age_years, leasing_cycle)
        """
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
        """
        Get leasing propensity from PKD code
        
        Returns:
            Tuple of (propensity_score, propensity_tier)
        """
        if not pkd_code or len(pkd_code) < 2:
            return PKD_LEASING_MAP["DEFAULT"]
        
        # PKD format: XX.XX.Z - use first 2 digits
        prefix = re.sub(r'\D', '', str(pkd_code))[:2]
        return PKD_LEASING_MAP.get(prefix, PKD_LEASING_MAP["DEFAULT"])
    
    @staticmethod
    def get_tax_benefit_score(legal_form: str) -> Tuple[int, Dict]:
        """
        Get tax benefit score and details from legal form
        
        Returns:
            Tuple of (score, details_dict)
        """
        if not legal_form:
            return TAX_BENEFIT_MAP["DEFAULT"]["score"], TAX_BENEFIT_MAP["DEFAULT"]
        
        # Normalize legal form
        form_upper = str(legal_form).upper().strip()
        
        # Try exact match
        if form_upper in TAX_BENEFIT_MAP:
            benefits = TAX_BENEFIT_MAP[form_upper]
            return benefits["score"], benefits
        
        # Try partial match
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
        """
        Segment lead into tier based on enrichment data
        
        Logic:
        - Tier S: Premium wealth + Mature/Established business + High PKD propensity
        - Tier A: High wealth OR strong leasing indicators
        - Tier B: Medium indicators
        - Tier C: Low indicators
        
        Returns:
            Tuple of (tier, score, reasoning)
        """
        # Calculate composite score (0-100)
        score = 0
        reasons = []
        
        # Wealth factor (0-30 points)
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
        
        # Business age / leasing cycle (0-25 points)
        if leasing_cycle == LeasingCycle.MATURE.value:
            score += 25
            reasons.append("Leasing renewal cycle (4-7yr)")
        elif leasing_cycle == LeasingCycle.ESTABLISHED.value:
            score += 20
            reasons.append("Established business (7yr+)")
        elif leasing_cycle == LeasingCycle.GROWTH.value:
            score += 15
            reasons.append("Growth phase (first leasing)")
        elif leasing_cycle == LeasingCycle.STARTUP.value:
            score += 5
            reasons.append("Startup (unlikely leasing)")
        
        # PKD propensity (0-25 points)
        pkd_points = int(pkd_propensity * 0.25)
        score += pkd_points
        if pkd_propensity >= 80:
            reasons.append(f"High fleet need industry (PKD: {pkd_propensity})")
        elif pkd_propensity >= 60:
            reasons.append(f"Medium fleet need (PKD: {pkd_propensity})")
        
        # Tax benefit factor (0-20 points)
        tax_points = int(tax_score * 0.20)
        score += tax_points
        if tax_score >= 80:
            reasons.append("Strong EV tax benefits")
        
        # Determine tier
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
        """
        Level 1: Local enrichment using dictionaries (Zero cost)
        
        Adds columns:
        - Wealth_Score, Wealth_Tier (from ZIP code)
        - Business_Age_Years, Leasing_Cycle (from start date)
        - PKD_Propensity, PKD_Tier (from PKD code)
        - Tax_Benefit_Score (from legal form)
        - Tier, Tier_Score, Tier_Reasoning
        - Next_Action
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for AssetSniper")
        
        logger.info(f"[SNIPER L1] Local enrichment for {len(df)} rows...")
        
        df_enriched = df.copy()
        
        # Get column names (use cleaned if available)
        zip_col = 'zip_code_clean' if 'zip_code_clean' in df_enriched.columns else None
        date_col = 'start_date_parsed' if 'start_date_parsed' in df_enriched.columns else None
        pkd_col = 'pkd_clean' if 'pkd_clean' in df_enriched.columns else None
        form_col = 'legal_form_clean' if 'legal_form_clean' in df_enriched.columns else None
        
        # Find original columns if cleaned not available
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
        
        # Business age (handle date column)
        if date_col:
            if date_col == 'start_date_parsed':
                # Already parsed
                age_data = df_enriched[date_col].apply(self.calculate_business_age)
            else:
                # Parse first
                age_data = df_enriched[date_col].apply(self.parse_date).apply(self.calculate_business_age)
        else:
            age_data = pd.Series([(0.0, LeasingCycle.UNKNOWN.value)] * len(df_enriched))
        
        df_enriched['Business_Age_Years'] = age_data.apply(lambda x: x[0])
        df_enriched['Leasing_Cycle'] = age_data.apply(lambda x: x[1])
        
        # PKD propensity
        pkd_data = df_enriched[pkd_col].apply(self.get_pkd_leasing_propensity) if pkd_col else pd.Series([(50, "LOW")] * len(df_enriched))
        df_enriched['PKD_Propensity'] = pkd_data.apply(lambda x: x[0])
        df_enriched['PKD_Tier'] = pkd_data.apply(lambda x: x[1])
        
        # Tax benefits
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
        
        # Determine next action based on tier
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
        
        # Log stats
        tier_counts = df_enriched['Tier'].value_counts()
        logger.info(f"[SNIPER L1] Enrichment complete. Tier distribution:")
        for tier, count in tier_counts.items():
            logger.info(f"  - {tier}: {count} ({count/len(df_enriched)*100:.1f}%)")
        
        return df_enriched
    
    # === LEVEL 2: DEEP ENRICHMENT (API/Ollama) ===
    
    async def generate_sniper_hook(
        self,
        company_name: str,
        pkd_code: str,
        city: str,
        tier_reasoning: str,
        wealth_tier: str
    ) -> str:
        """
        Generate AI-powered cold call hook for Tier S leads
        
        Uses Ollama to create personalized opening line
        """
        if not self.analysis_engine:
            return "AI hook unavailable - analysis engine not configured"
        
        prompt = f"""You are an expert B2B sales copywriter specializing in Tesla fleet sales.

Generate a 1-sentence personalized cold call opening hook for this company:

COMPANY: {company_name}
INDUSTRY (PKD): {pkd_code}
LOCATION: {city}
PROFILE: {tier_reasoning}
WEALTH TIER: {wealth_tier}

RULES:
1. Be specific to their industry
2. Mention a relevant benefit (cost savings, image, sustainability)
3. Create urgency but not pushy
4. Polish language
5. Maximum 25 words

EXAMPLE GOOD HOOKS:
- "Dzień dobry, widzę że w branży logistycznej koszty paliwa zjadają marżę - mamy rozwiązanie które obniży je o 70%."
- "Zauważyłem że Państwa firma działa w Mokotowie - tam właśnie stawiamy stacje ładowania dla flot premium."

YOUR HOOK:
"""
        try:
            # Call Ollama via analysis engine
            result = await self.analysis_engine._call_ollama(prompt)
            
            if result:
                # Extract text from JSON response if needed
                if isinstance(result, dict):
                    hook = result.get('hook', result.get('response', str(result)))
                else:
                    hook = str(result)
                
                # Clean up
                hook = hook.strip().strip('"').strip()
                return hook[:200]  # Limit length
            
            return "AI hook generation failed"
            
        except Exception as e:
            logger.error(f"[SNIPER L2] Hook generation error: {e}")
            return f"Error: {str(e)[:50]}"
    
    async def enrich_tier_s(self, df: 'pd.DataFrame', batch_size: int = 5) -> 'pd.DataFrame':
        """
        Level 2: Deep enrichment for Tier S leads only
        
        Operations:
        - Generate AI cold call hooks via Ollama
        - Check charger infrastructure (via Gotham)
        - Calculate tax potential (via Gotham)
        
        Note: This is async and batched to prevent timeouts
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for AssetSniper")
        
        df_enriched = df.copy()
        
        # Initialize new columns
        df_enriched['Sniper_Hook'] = ""
        df_enriched['Enrichment_Level'] = df_enriched['Enrichment_Level'].fillna(1)
        
        # Get Tier S leads
        tier_s_mask = df_enriched['Tier'] == LeadTier.TIER_S.value
        tier_s_indices = df_enriched[tier_s_mask].index.tolist()
        
        if not tier_s_indices:
            logger.info("[SNIPER L2] No Tier S leads to enrich")
            return df_enriched
        
        logger.info(f"[SNIPER L2] Deep enriching {len(tier_s_indices)} Tier S leads...")
        
        # Find relevant columns
        name_col = None
        pkd_col = None
        city_col = None
        
        for col in df_enriched.columns:
            if 'name' in col.lower() or 'nazwa' in col.lower():
                name_col = col
            if 'pkd' in col.lower():
                pkd_col = col
            if 'city' in col.lower() or 'miasto' in col.lower():
                city_col = col
        
        # Process in batches
        for i in range(0, len(tier_s_indices), batch_size):
            batch_indices = tier_s_indices[i:i + batch_size]
            
            tasks = []
            for idx in batch_indices:
                row = df_enriched.loc[idx]
                
                company_name = row.get(name_col, "Unknown Company") if name_col else "Unknown"
                pkd_code = row.get(pkd_col, "") if pkd_col else ""
                city = row.get(city_col, "") if city_col else ""
                tier_reasoning = row.get('Tier_Reasoning', "")
                wealth_tier = row.get('Wealth_Tier', "STANDARD")
                
                task = self.generate_sniper_hook(
                    company_name=str(company_name),
                    pkd_code=str(pkd_code),
                    city=str(city),
                    tier_reasoning=str(tier_reasoning),
                    wealth_tier=str(wealth_tier)
                )
                tasks.append((idx, task))
            
            # Execute batch
            for idx, task in tasks:
                try:
                    hook = await task
                    df_enriched.at[idx, 'Sniper_Hook'] = hook
                    df_enriched.at[idx, 'Enrichment_Level'] = 2
                except Exception as e:
                    logger.error(f"[SNIPER L2] Error enriching row {idx}: {e}")
                    df_enriched.at[idx, 'Sniper_Hook'] = f"Error: {str(e)[:30]}"
            
            logger.info(f"[SNIPER L2] Processed batch {i//batch_size + 1}/{(len(tier_s_indices) + batch_size - 1)//batch_size}")
        
        return df_enriched
    
    # === MAIN PIPELINE ===
    
    async def process_csv(
        self,
        df: 'pd.DataFrame',
        enable_deep_enrichment: bool = True,
        chunk_size: int = 1000
    ) -> Tuple['pd.DataFrame', SniperStats]:
        """
        Main processing pipeline
        
        Steps:
        1. Level 0: Clean data
        2. Level 1: Local enrichment (all leads)
        3. Level 2: Deep enrichment (Tier S only, if enabled)
        
        Args:
            df: Input DataFrame from CSV
            enable_deep_enrichment: Whether to run Ollama enrichment for Tier S
            chunk_size: Process in chunks for large files
            
        Returns:
            Tuple of (enriched_dataframe, statistics)
        """
        import time
        start_time = time.time()
        
        stats = SniperStats(total_rows=len(df))
        
        logger.info(f"[ASSET SNIPER] Starting pipeline for {len(df)} rows")
        
        # Process in chunks if large file
        if len(df) > chunk_size:
            logger.info(f"[ASSET SNIPER] Processing in chunks of {chunk_size}")
            chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
            processed_chunks = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"[ASSET SNIPER] Processing chunk {i+1}/{len(chunks)}")
                
                # Level 0 + 1
                chunk_clean = self.clean_data(chunk)
                chunk_enriched = self.enrich_local(chunk_clean)
                
                processed_chunks.append(chunk_enriched)
            
            df_enriched = pd.concat(processed_chunks, ignore_index=True)
        else:
            # Level 0: Clean
            df_clean = self.clean_data(df)
            
            # Level 1: Local enrichment
            df_enriched = self.enrich_local(df_clean)
        
        # Level 2: Deep enrichment (Tier S only)
        if enable_deep_enrichment and self.analysis_engine:
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
        
        # Get voivodeship distribution
        for col in df_enriched.columns:
            if 'wojewod' in col.lower() or 'voivode' in col.lower():
                stats.top_voivodeships = df_enriched[col].value_counts().head(5).to_dict()
                break
        
        stats.processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"[ASSET SNIPER] Pipeline complete in {stats.processing_time_ms}ms")
        logger.info(f"[ASSET SNIPER] Results: Tier S={stats.tier_s_count}, Tier A={stats.tier_a_count}, Tier B={stats.tier_b_count}, Tier C={stats.tier_c_count}")
        
        return df_enriched, stats
    
    def process_csv_sync(
        self,
        df: 'pd.DataFrame',
        enable_deep_enrichment: bool = False
    ) -> Tuple['pd.DataFrame', SniperStats]:
        """
        Synchronous wrapper for process_csv
        
        Note: Deep enrichment disabled by default in sync mode
        """
        import time
        start_time = time.time()
        
        stats = SniperStats(total_rows=len(df))
        
        # Level 0: Clean
        df_clean = self.clean_data(df)
        
        # Level 1: Local enrichment
        df_enriched = self.enrich_local(df_clean)
        
        # Calculate stats
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
    print("=== ASSET SNIPER Module Test ===\n")
    
    if not PANDAS_AVAILABLE:
        print("ERROR: pandas not installed. Run: pip install pandas")
        exit(1)
    
    # Create test data
    test_data = {
        'NIP': ['5272829917', '123-456-78-90', 'invalid', '5261040828'],
        'Telefon': ['+48 500 100 200', '500100200', '48500100200', 'bad'],
        'Email': ['test@example.com', 'invalid', 'hello@firma.pl', ''],
        'Nazwa': ['Tech Solutions Sp. z o.o.', 'Auto-Trans', 'StartupXYZ', 'Konsulting Pro'],
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
    
    # Process
    sniper = AssetSniper()
    df_result, stats = sniper.process_csv_sync(df_test)
    
    print("Enriched data (key columns):")
    key_cols = ['Nazwa', 'Tier', 'Tier_Score', 'Wealth_Tier', 'Leasing_Cycle', 'Next_Action']
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
    print("\n✅ ASSET SNIPER Test Complete!")
