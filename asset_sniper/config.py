"""
ASSET SNIPER - Configuration Module
Centralna konfiguracja systemu: PKD profiles, wagi scoringowe, progi tier'ów

Based on: BIBLE v1.0
Author: BigDInc Team
"""

from typing import Dict, List, Tuple
from enum import Enum


# === ENUMS ===

class Tier(str, Enum):
    """Lead tier classification"""
    S = "S"
    AAA = "AAA"
    AA = "AA"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class Priority(str, Enum):
    """Action priority for each tier"""
    IMMEDIATE = "NATYCHMIAST"
    TODAY = "DZIŚ"
    THIS_WEEK = "TEN TYDZIEŃ"
    AUTOMATE = "AUTOMAT"
    LOW = "NISKI"
    ARCHIVE = "ARCHIWUM"


# === TIER THRESHOLDS ===

TIER_THRESHOLDS = {
    Tier.S: (85, 100, Priority.IMMEDIATE, "Telefon w ciągu 24h"),
    Tier.AAA: (75, 84, Priority.TODAY, "Kontakt tego dnia"),
    Tier.AA: (65, 74, Priority.THIS_WEEK, "Kontakt w tym tygodniu"),
    Tier.A: (50, 64, Priority.AUTOMATE, "Sekwencja automatyczna"),
    Tier.B: (35, 49, Priority.LOW, "Raz w miesiącu"),
    Tier.C: (25, 34, Priority.ARCHIVE, "Ignoruj"),
    Tier.D: (15, 24, Priority.ARCHIVE, "Ignoruj"),
    Tier.E: (0, 14, Priority.ARCHIVE, "Ignoruj"),
}


# === SCORING WEIGHTS ===

SCORING_WEIGHTS = {
    "pkd_tier": 30,           # Max 30 points for industry tier
    "wealth_proxy": 25,       # Max 25 points for region wealth
    "company_age": 20,        # Max 20 points for leasing cycle
    "charger_proximity": 15,  # Max 15 points for charger distance
    "contact_quality": 10,    # Max 10 points for contact completeness
}


# === PKD PROFILES ===
# Tier S-B industries with psychographic profiles

PKD_PROFILES = {
    # TIER S - Lawyers & Legal (30 pts)
    "6910Z": {
        "tier": "S",
        "score": 30,
        "name": "Prawnik",
        "full_name": "Usługi prawne",
        "pain_points": [
            "Prestiż i wizerunek zawodowy",
            "Koszty podatkowe - szukają optymalizacji",
            "Wysokie koszty operacyjne firmy",
        ],
        "motivators": [
            "Status społeczny i zawodowy",
            "Oszczędności podatkowe (32% stawka)",
            "Premium brand jako inwestycja w wizerunek",
        ],
        "hook_angle": "Tesla to nie tylko prestiż - to konkretne oszczędności podatkowe",
        "tax_benefit_focus": True,
        "tax_rate": 32,  # High tax bracket
    },

    # TIER S - Accountants (30 pts)
    "6920Z": {
        "tier": "S",
        "score": 30,
        "name": "Księgowy",
        "full_name": "Usługi księgowe",
        "pain_points": [
            "ROI i zwrot z inwestycji",
            "Optymalizacja kosztów firmowych",
            "Precyzyjne kalkulacje finansowe",
        ],
        "motivators": [
            "Konkretne liczby i oszczędności",
            "Korzyści podatkowe do 14 250 PLN/rok",
            "Przewidywalny TCO",
        ],
        "hook_angle": "Jako specjalista od podatków doceni Pan ten kalkulator: do 14 250 PLN rocznie więcej w kosztach",
        "tax_benefit_focus": True,
        "tax_rate": 19,
    },

    # TIER A - IT (22 pts)
    "6201Z": {
        "tier": "A",
        "score": 22,
        "name": "IT",
        "full_name": "Programowanie komputerowe",
        "pain_points": [
            "Technologia powinna się zwracać",
            "Ekologia jako wartość",
            "Nowoczesność i innowacyjność",
        ],
        "motivators": [
            "Technologia OTA updates",
            "Ekosystem digital (aplikacja Tesla)",
            "Early adopter prestige",
        ],
        "hook_angle": "Dla branży IT Tesla to naturalny wybór. Technologia, która się zwraca - dosłownie",
        "tax_benefit_focus": False,
        "tax_rate": 19,
    },

    # TIER A - Medical (22 pts)
    "8621Z": {
        "tier": "A",
        "score": 22,
        "name": "Lekarz",
        "full_name": "Praktyka lekarska",
        "pain_points": [
            "Brak czasu (czas to pieniądz)",
            "Wysokie koszty podatkowe",
            "Prestiż zawodowy",
        ],
        "motivators": [
            "Oszczędność czasu (Autopilot, Supercharger)",
            "Korzyści podatkowe dla lekarzy (32%)",
            "Prestiż i status",
        ],
        "hook_angle": "Dla lekarzy czas to pieniądz - a Tesla oszczędza jedno i drugie",
        "tax_benefit_focus": True,
        "tax_rate": 32,
    },

    # TIER A - Transport & Logistics (22 pts)
    "4941Z": {
        "tier": "A",
        "score": 22,
        "name": "Transport",
        "full_name": "Transport drogowy towarów",
        "pain_points": [
            "Wysokie koszty paliwa",
            "Opłaty za emisje CO2",
            "Niskie marże",
        ],
        "motivators": [
            "Drastyczne obniżenie kosztów operacyjnych",
            "Zwolnienia z opłat środowiskowych",
            "Długoterminowe oszczędności",
        ],
        "hook_angle": "W logistyce paliwo zjada marżę - mogę pokazać jak obniżyć koszty floty",
        "tax_benefit_focus": False,
        "tax_rate": 19,
    },

    # TIER B - Consulting (15 pts)
    "7022Z": {
        "tier": "B",
        "score": 15,
        "name": "Konsultant",
        "full_name": "Doradztwo biznesowe",
        "pain_points": [
            "Wizerunek profesjonalny",
            "Mobilność zawodowa",
            "Optymalizacja kosztów",
        ],
        "motivators": [
            "Premium brand jako narzędzie sprzedaży",
            "Niskie koszty użytkowania",
            "Status i innowacyjność",
        ],
        "hook_angle": "Konsultanci wybierają Teslę - to inwestycja w wizerunek profesjonalisty",
        "tax_benefit_focus": True,
        "tax_rate": 19,
    },

    # DEFAULT - Other (8 pts)
    "DEFAULT": {
        "tier": "B",
        "score": 8,
        "name": "Przedsiębiorca",
        "full_name": "Działalność gospodarcza",
        "pain_points": [
            "Wysokie koszty operacyjne",
            "Niepewność rynkowa",
            "Zarządzanie budżetem",
        ],
        "motivators": [
            "Oszczędności finansowe",
            "Przewidywalny TCO",
            "Nowoczesność firmy",
        ],
        "hook_angle": "Tesla to konkretne oszczędności dla Twojej firmy",
        "tax_benefit_focus": True,
        "tax_rate": 19,
    },
}


# === WEALTH PROXY MAP (Silesia Focus) ===
# Kod pocztowy -> (wealth_score 1-10, tier_name)

WEALTH_PROXY_SILESIA = {
    # Katowice - Premium zones
    "40-001": (9, "PREMIUM"),  # Śródmieście
    "40-007": (9, "PREMIUM"),  # Kościuszki
    "40-012": (8, "HIGH"),     # Brynów
    "40-024": (9, "PREMIUM"),  # Ochojec
    "40-049": (8, "HIGH"),     # Kostuchna
    "40-055": (7, "MEDIUM"),   # Panewniki
    "40-074": (6, "MEDIUM"),   # Podlesie
    "40-086": (8, "HIGH"),     # Ligota
    "40-101": (7, "MEDIUM"),   # Zawodzie
    "40-203": (5, "STANDARD"), # Szopienice
    "40-285": (4, "LOW"),      # Dąb
    "40-534": (6, "MEDIUM"),   # Giszowiec
    "40-601": (7, "MEDIUM"),   # Murcki
    "40-750": (5, "STANDARD"), # Kostuchna Przemysłowa

    # Gliwice
    "44-100": (8, "HIGH"),     # Centrum
    "44-102": (7, "MEDIUM"),   # Śródmieście
    "44-103": (8, "HIGH"),     # Sikornik
    "44-109": (6, "MEDIUM"),   # Łabędy
    "44-114": (7, "MEDIUM"),   # Wojska Polskiego

    # Bytom
    "41-902": (4, "LOW"),      # Centrum
    "41-907": (3, "LOW"),      # Miechowice
    "41-914": (4, "LOW"),      # Stroszek

    # Sosnowiec
    "41-200": (6, "MEDIUM"),   # Centrum
    "41-205": (5, "STANDARD"), # Pogoń
    "41-219": (5, "STANDARD"), # Środula

    # Tychy
    "43-100": (7, "MEDIUM"),   # Centrum
    "43-110": (6, "MEDIUM"),   # Osiedle A

    # Ruda Śląska
    "41-700": (4, "LOW"),      # Centrum
    "41-710": (3, "LOW"),      # Halemba

    # Zabrze
    "41-800": (5, "STANDARD"), # Centrum
    "41-808": (4, "LOW"),      # Biskupice

    # Bielsko-Biała
    "43-300": (7, "MEDIUM"),   # Centrum
    "43-309": (8, "HIGH"),     # Straconka

    # Częstochowa
    "42-200": (6, "MEDIUM"),   # Centrum
    "42-217": (5, "STANDARD"), # Tysiąclecie

    # Fallback
    "DEFAULT": (5, "STANDARD"),
}


# === CHARGER LOCATIONS (Static - to be replaced by OpenChargeMap API) ===

CHARGER_LOCATIONS = [
    # Tesla Superchargers
    {"name": "Tesla Supercharger Katowice", "lat": 50.2649, "lon": 19.0238, "power": 250, "type": "Supercharger"},
    {"name": "Tesla Supercharger Gliwice", "lat": 50.2945, "lon": 18.6714, "power": 250, "type": "Supercharger"},
    {"name": "Tesla Supercharger Tychy", "lat": 50.1078, "lon": 18.9985, "power": 150, "type": "Supercharger"},

    # IONITY
    {"name": "IONITY Katowice A4", "lat": 50.2313, "lon": 19.0847, "power": 350, "type": "HPC"},
    {"name": "IONITY Gliwice A1", "lat": 50.3246, "lon": 18.7234, "power": 350, "type": "HPC"},

    # Orlen Charge
    {"name": "Orlen Charge Katowice", "lat": 50.2657, "lon": 19.0179, "power": 50, "type": "DC Fast"},
    {"name": "Orlen Charge Sosnowiec", "lat": 50.2865, "lon": 19.1044, "power": 50, "type": "DC Fast"},
    {"name": "Orlen Charge Bytom", "lat": 50.3483, "lon": 18.9115, "power": 50, "type": "DC Fast"},

    # Greenway
    {"name": "Greenway Bielsko-Biała", "lat": 49.8224, "lon": 19.0445, "power": 50, "type": "DC Fast"},
    {"name": "Greenway Częstochowa", "lat": 50.8118, "lon": 19.1203, "power": 50, "type": "DC Fast"},
]


# === TAX BENEFITS MAP ===

TAX_BENEFITS = {
    "EV_AMORTYZACJA_LIMIT": 225_000,  # PLN - EV depreciation limit
    "ICE_AMORTYZACJA_LIMIT": 150_000,  # PLN - ICE depreciation limit
    "TAX_DIFFERENCE": 75_000,          # PLN - difference
    "OSZCZEDNOSC_19PCT": 14_250,       # PLN/year - savings at 19% tax rate
    "OSZCZEDNOSC_32PCT": 24_000,       # PLN/year - savings at 32% tax rate (doctors, lawyers)
    "NASZEAUTO_STANDARD": 27_000,      # PLN - NaszEauto subsidy standard
    "NASZEAUTO_FAMILY": 40_000,        # PLN - NaszEauto subsidy with Karta Dużej Rodziny
}


# === COMPANY AGE -> LEASING CYCLE MAPPING ===

LEASING_CYCLE_MAP = {
    (0, 1): {"cycle": "STARTUP", "propensity": 0.15, "description": "Firma rozpoczynająca - niskie prawdopodobieństwo leasingu"},
    (1, 2): {"cycle": "EARLY_GROWTH", "propensity": 0.30, "description": "Wzrost - pierwsze rozważanie leasingu"},
    (2, 3): {"cycle": "GROWTH", "propensity": 0.50, "description": "Rozwój - aktywne poszukiwanie leasingu"},
    (3, 4): {"cycle": "PRIME_LEASING", "propensity": 0.80, "description": "Pierwsze odnowienie leasingu 3-letniego"},
    (4, 5): {"cycle": "MATURE", "propensity": 0.90, "description": "Dojrzała - pełny cykl leasingowy"},
    (5, 6): {"cycle": "RENEWAL_WINDOW", "propensity": 0.95, "description": "Okno odnowienia - najlepszy moment"},
    (6, 7): {"cycle": "ESTABLISHED", "propensity": 0.90, "description": "Ugruntowana - regularny leasing"},
    (7, 100): {"cycle": "VETERAN", "propensity": 0.85, "description": "Weteran - wieloletnie doświadczenie z leasingiem"},
}


# === CONTACT QUALITY SCORING ===

CONTACT_QUALITY_POINTS = {
    "phone": 5,   # Has valid phone number
    "email": 3,   # Has valid email
    "www": 2,     # Has website (indicates professionalism)
}


# === CHARGER DISTANCE SCORING ===

CHARGER_DISTANCE_POINTS = {
    5: 15,    # <5km - excellent
    10: 12,   # <10km - very good
    20: 9,    # <20km - good
    30: 6,    # <30km - acceptable
    50: 3,    # <50km - marginal
    100: 0,   # 50km+ - poor
}


# === OUTPUT CSV REQUIRED COLUMNS ===

OUTPUT_COLUMNS_REQUIRED = [
    "Imie",
    "Nazwisko",
    "Email",
    "Telefon",
    "TargetTier",
    "TotalScore",
]

OUTPUT_COLUMNS_OPTIONAL = [
    "LeadDescription",
    "SniperHook",
    "TaxWeapon",
    "GothamInsight",
]


# === API CONFIGURATION ===

API_CONFIG = {
    "cepik": {
        "base_url": "https://api.cepik.gov.pl",
        "timeout": 30,
        "retry_count": 3,
    },
    "krs": {
        "base_url": "https://api-krs.ms.gov.pl",
        "timeout": 30,
        "retry_count": 3,
    },
    "opencharge": {
        "base_url": "https://api.openchargemap.io/v3",
        "api_key_env": "OPENCHARGE_API_KEY",  # Optional - higher rate limits with key
        "timeout": 30,
        "retry_count": 3,
    },
}


# === BATCH PROCESSING CONFIG ===

BATCH_CONFIG = {
    "chunk_size": 10_000,      # Rows per chunk for large files
    "parallel_workers": 4,      # Number of parallel workers
    "api_rate_limit": 100,      # Max API calls per minute
    "cache_ttl": 86400,         # Cache TTL in seconds (24h)
}
