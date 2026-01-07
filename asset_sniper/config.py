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


# === REAL ESTATE MARKET DATA (Palantir-Level Intelligence) ===
# Bazowane na rzeczywistych cenach m² nieruchomości komercyjnych i mieszkalnych (2024-2025)
# Źródła: Otodom, NBP, CBRE Market Reports

# Średnia krajowa cena m² (biura/mieszkania premium) - używana jako benchmark
NATIONAL_AVG_M2_PRICE = 11_500  # PLN/m²

# === GOLDEN CITY SET M² PRICING (v5.0) ===
# Precyzyjne ceny dla kluczowych rynków - używane przez BigDecoder Full Bridge
GOLDEN_CITY_M2_PRICES = {
    "Warszawa": 19_500,   # Premium capital city price
    "Katowice": 10_800,   # Śląsk hub price
    "Kraków": 15_200,     # Second largest market
    "Wrocław": 13_800,    # Tech hub
    "Gdańsk": 14_200,     # Trójmiasto center
    "Poznań": 12_500,     # Western Poland hub
}

# Ceny m² dla top 50 polskich miast (dane 2024-2025)
REAL_ESTATE_MARKET_DATA = {
    # === TIER S CITIES (>15,000 PLN/m²) ===
    "Warszawa": {"avg_m2": 19_500, "office_m2": 24_000, "premium_districts": ["Śródmieście", "Mokotów", "Wilanów"]},
    "Kraków": {"avg_m2": 15_200, "office_m2": 18_500, "premium_districts": ["Stare Miasto", "Kazimierz", "Podgórze"]},

    # === TIER A CITIES (11,000-15,000 PLN/m²) ===
    "Wrocław": {"avg_m2": 13_800, "office_m2": 17_000, "premium_districts": ["Stare Miasto", "Krzyki"]},
    "Gdańsk": {"avg_m2": 14_200, "office_m2": 17_500, "premium_districts": ["Śródmieście", "Wrzeszcz", "Oliwa"]},
    "Gdynia": {"avg_m2": 12_800, "office_m2": 15_500, "premium_districts": ["Śródmieście", "Orłowo"]},
    "Sopot": {"avg_m2": 18_500, "office_m2": 22_000, "premium_districts": ["Centrum", "Dolny Sopot"]},
    "Poznań": {"avg_m2": 12_500, "office_m2": 15_000, "premium_districts": ["Stare Miasto", "Jeżyce"]},
    "Katowice": {"avg_m2": 10_800, "office_m2": 14_000, "premium_districts": ["Śródmieście", "Brynów", "Ligota"]},

    # === TIER B CITIES (8,500-11,000 PLN/m²) ===
    "Łódź": {"avg_m2": 9_200, "office_m2": 11_000, "premium_districts": ["Śródmieście", "Bałuty"]},
    "Szczecin": {"avg_m2": 9_800, "office_m2": 12_000, "premium_districts": ["Centrum", "Żelechowa"]},
    "Lublin": {"avg_m2": 9_500, "office_m2": 11_500, "premium_districts": ["Śródmieście", "Wieniawa"]},
    "Bydgoszcz": {"avg_m2": 8_800, "office_m2": 10_500, "premium_districts": ["Śródmieście", "Fordon"]},
    "Białystok": {"avg_m2": 9_000, "office_m2": 10_800, "premium_districts": ["Centrum", "Antoniuk"]},
    "Gliwice": {"avg_m2": 9_200, "office_m2": 11_000, "premium_districts": ["Centrum", "Sikornik"]},
    "Tychy": {"avg_m2": 8_800, "office_m2": 10_200, "premium_districts": ["Centrum", "Osiedle A"]},
    "Rzeszów": {"avg_m2": 9_400, "office_m2": 11_200, "premium_districts": ["Śródmieście", "Drabinianka"]},
    "Toruń": {"avg_m2": 9_100, "office_m2": 10_800, "premium_districts": ["Stare Miasto", "Bydgoskie"]},
    "Olsztyn": {"avg_m2": 8_900, "office_m2": 10_500, "premium_districts": ["Śródmieście", "Jaroty"]},
    "Opole": {"avg_m2": 8_600, "office_m2": 10_000, "premium_districts": ["Centrum", "Zaodrze"]},
    "Kielce": {"avg_m2": 8_500, "office_m2": 10_200, "premium_districts": ["Centrum", "Czarnów"]},
    "Bielsko-Biała": {"avg_m2": 9_000, "office_m2": 10_800, "premium_districts": ["Centrum", "Straconka"]},

    # === TIER C CITIES (6,500-8,500 PLN/m²) ===
    "Częstochowa": {"avg_m2": 7_800, "office_m2": 9_200, "premium_districts": ["Centrum", "Parkitka"]},
    "Radom": {"avg_m2": 7_200, "office_m2": 8_500, "premium_districts": ["Śródmieście", "Gołębiów"]},
    "Sosnowiec": {"avg_m2": 7_200, "office_m2": 8_600, "premium_districts": ["Centrum", "Pogoń"]},
    "Zabrze": {"avg_m2": 6_800, "office_m2": 8_000, "premium_districts": ["Centrum", "Rokitnica"]},
    "Ruda Śląska": {"avg_m2": 6_500, "office_m2": 7_800, "premium_districts": ["Nowy Bytom", "Wirek"]},
    "Bytom": {"avg_m2": 5_800, "office_m2": 7_000, "premium_districts": ["Centrum", "Szombierki"]},
    "Dąbrowa Górnicza": {"avg_m2": 6_800, "office_m2": 8_000, "premium_districts": ["Centrum", "Gołonóg"]},
    "Elbląg": {"avg_m2": 7_000, "office_m2": 8_200, "premium_districts": ["Stare Miasto", "Zawada"]},
    "Płock": {"avg_m2": 7_500, "office_m2": 8_800, "premium_districts": ["Stare Miasto", "Podolszyce"]},
    "Wałbrzych": {"avg_m2": 5_500, "office_m2": 6_800, "premium_districts": ["Śródmieście", "Szczawienko"]},
    "Włocławek": {"avg_m2": 6_200, "office_m2": 7_500, "premium_districts": ["Centrum", "Południe"]},
    "Tarnów": {"avg_m2": 7_200, "office_m2": 8_500, "premium_districts": ["Stare Miasto", "Grabówka"]},
    "Chorzów": {"avg_m2": 6_400, "office_m2": 7_600, "premium_districts": ["Centrum", "Batory"]},
    "Kalisz": {"avg_m2": 6_800, "office_m2": 8_000, "premium_districts": ["Centrum", "Asnyka"]},
    "Legnica": {"avg_m2": 6_500, "office_m2": 7_800, "premium_districts": ["Stare Miasto", "Tarninów"]},
    "Grudziądz": {"avg_m2": 5_800, "office_m2": 7_000, "premium_districts": ["Stare Miasto", "Kopernika"]},
    "Jaworzno": {"avg_m2": 6_200, "office_m2": 7_400, "premium_districts": ["Centrum", "Szczakowa"]},
    "Słupsk": {"avg_m2": 7_800, "office_m2": 9_000, "premium_districts": ["Centrum", "Zatorze"]},
    "Jastrzębie-Zdrój": {"avg_m2": 5_600, "office_m2": 6_800, "premium_districts": ["Centrum", "Zdrój"]},
    "Nowy Sącz": {"avg_m2": 7_500, "office_m2": 8_800, "premium_districts": ["Stare Miasto", "Helena"]},
    "Jelenia Góra": {"avg_m2": 6_800, "office_m2": 8_000, "premium_districts": ["Cieplice", "Śródmieście"]},
    "Siedlce": {"avg_m2": 7_000, "office_m2": 8_200, "premium_districts": ["Centrum", "Młynarska"]},
    "Mysłowice": {"avg_m2": 6_000, "office_m2": 7_200, "premium_districts": ["Centrum", "Brzęczkowice"]},
    "Piła": {"avg_m2": 6_500, "office_m2": 7_800, "premium_districts": ["Centrum", "Zamość"]},
    "Ostrów Wielkopolski": {"avg_m2": 6_200, "office_m2": 7_400, "premium_districts": ["Centrum", "Pruślin"]},
    "Siemianowice Śląskie": {"avg_m2": 5_800, "office_m2": 7_000, "premium_districts": ["Centrum", "Michałkowice"]},
    "Piekary Śląskie": {"avg_m2": 5_500, "office_m2": 6_600, "premium_districts": ["Centrum", "Szarlej"]},
    "Świętochłowice": {"avg_m2": 5_200, "office_m2": 6_200, "premium_districts": ["Centrum", "Lipiny"]},

    # Fallback dla nieznanych miast
    "DEFAULT": {"avg_m2": 7_000, "office_m2": 8_500, "premium_districts": []},
}

# === POSTAL CODE TO CITY MAPPING ===
# Mapa prefiksów kodów pocztowych na miasta (pierwsze 2-3 cyfry)
POSTAL_CODE_CITY_MAP = {
    # Warszawa (00-04)
    "00": "Warszawa", "01": "Warszawa", "02": "Warszawa", "03": "Warszawa", "04": "Warszawa",

    # Kraków (30-32)
    "30": "Kraków", "31": "Kraków", "32": "Kraków",

    # Wrocław (50-54)
    "50": "Wrocław", "51": "Wrocław", "52": "Wrocław", "53": "Wrocław", "54": "Wrocław",

    # Poznań (60-61)
    "60": "Poznań", "61": "Poznań",

    # Gdańsk/Trójmiasto (80-81)
    "80": "Gdańsk", "81": "Gdynia",

    # Sopot (81-8)
    "81-7": "Sopot", "81-8": "Sopot",

    # Łódź (90-94)
    "90": "Łódź", "91": "Łódź", "92": "Łódź", "93": "Łódź", "94": "Łódź",

    # Szczecin (70-71)
    "70": "Szczecin", "71": "Szczecin",

    # Lublin (20)
    "20": "Lublin",

    # Katowice (40)
    "40": "Katowice",

    # Bytom (41-9)
    "41-9": "Bytom",

    # Sosnowiec (41-2)
    "41-2": "Sosnowiec",

    # Ruda Śląska (41-7)
    "41-7": "Ruda Śląska",

    # Zabrze (41-8)
    "41-8": "Zabrze",

    # Chorzów (41-5)
    "41-5": "Chorzów",

    # Gliwice (44)
    "44": "Gliwice",

    # Tychy (43-1)
    "43-1": "Tychy",

    # Bielsko-Biała (43-3)
    "43-3": "Bielsko-Biała",

    # Częstochowa (42)
    "42": "Częstochowa",

    # Rzeszów (35)
    "35": "Rzeszów",

    # Toruń (87)
    "87": "Toruń",

    # Bydgoszcz (85)
    "85": "Bydgoszcz",

    # Białystok (15)
    "15": "Białystok",

    # Kielce (25)
    "25": "Kielce",

    # Olsztyn (10)
    "10": "Olsztyn",

    # Opole (45)
    "45": "Opole",
}

# === HIGH-WEALTH STREET KEYWORDS (Palantir Correlation) ===
# Ulice kojarzące się z zamożnością - użyte gdy brak danych m²
HIGH_WEALTH_STREET_KEYWORDS = [
    # Biznesowe
    "Rynek", "Plac", "Aleja", "Aleje", "Centrum", "Śródmieście",
    "Business", "Park", "Tower", "Plaza", "Office",
    # Prestiżowe dzielnice
    "Ujazdowskie", "Nowy Świat", "Marszałkowska", "Grodzka",
    "Floriańska", "Długa", "Szeroka", "Wawel",
    # Corporate zones
    "Chorzowska", "Roździeńskiego", "Korfantego", "Sienkiewicza",
    # IT/Tech hubs
    "Armii Krajowej", "Warszawska", "Krakowska", "Gdańska",
]

# === PKD-BASED WEALTH CORRELATION (Palantir Fallback) ===
# Jeśli brak danych lokalizacji, użyj PKD do estymacji zamożności
PKD_WEALTH_CORRELATION = {
    # PREMIUM (implicit wealth tier)
    "6910Z": 9,  # Prawnicy - zawsze zamożni
    "6920Z": 8,  # Księgowi - dobry wskaźnik
    "6201Z": 8,  # IT/Programiści - high-income
    "8621Z": 9,  # Lekarze - premium
    "6621Z": 9,  # Brokerzy/Doradcy finansowi
    "6622Z": 8,  # Agenci ubezpieczeniowi
    "7010Z": 8,  # Zarządzanie holdingami
    "7022Z": 7,  # Konsultanci biznesowi
    "7311Z": 7,  # Agencje reklamowe

    # HIGH
    "4941Z": 6,  # Transport - flota = kapitał
    "4520Z": 6,  # Warsztaty samochodowe - często premium
    "4511Z": 7,  # Dealerzy samochodów

    # MEDIUM
    "4711Z": 5,  # Sklepy spożywcze
    "4771Z": 5,  # Sklepy odzieżowe
    "5610A": 5,  # Restauracje

    # DEFAULT
    "DEFAULT": 5,
}

# === LEGACY COMPATIBILITY ===
# Stara mapa dla kompatybilności wstecznej - DEPRECATED
WEALTH_PROXY_SILESIA = {
    "40-001": (9, "PREMIUM"),
    "44-100": (8, "HIGH"),
    "DEFAULT": (5, "STANDARD"),
}


# === ZIP CODE PREFIX COORDINATES (Geo-Precision Upgrade) ===
# Precyzyjne koordynaty dla prefiksów kodów pocztowych (3-cyfrowe gdzie możliwe)
# Używane do obliczania odległości do ładowarek z większą precyzją
POSTAL_PREFIX_COORDINATES = {
    # === WARSZAWA (00-04) ===
    "00-0": (52.2319, 21.0067),  # Śródmieście Północne
    "00-1": (52.2297, 21.0122),  # Śródmieście Centrum
    "00-2": (52.2250, 21.0200),  # Śródmieście Południe
    "00-3": (52.2350, 21.0050),  # Muranów
    "00-4": (52.2400, 21.0100),  # Mirów
    "00-5": (52.2280, 21.0180),  # Powiśle
    "00-6": (52.2220, 21.0250),  # Solec
    "00-7": (52.2180, 21.0150),  # Czerniaków
    "00-8": (52.2400, 20.9900),  # Wola Centrum
    "00-9": (52.2500, 21.0000),  # Wola Północ
    "01": (52.2600, 21.0100),    # Wola/Bemowo
    "02-0": (52.2100, 21.0000),  # Mokotów Dolny
    "02-1": (52.2050, 21.0100),  # Mokotów Górny
    "02-2": (52.1950, 21.0050),  # Ursynów
    "02-5": (52.1900, 21.0200),  # Ursynów Południe
    "02-6": (52.2000, 21.0350),  # Kabaty
    "02-7": (52.2100, 21.0400),  # Wilanów
    "02-8": (52.2200, 21.0500),  # Powsin
    "03": (52.2700, 21.0300),    # Praga Północ
    "04": (52.2400, 21.0600),    # Praga Południe

    # === KRAKÓW (30-32) ===
    "30-0": (50.0614, 19.9372),  # Stare Miasto
    "30-1": (50.0580, 19.9450),  # Kazimierz
    "30-2": (50.0520, 19.9400),  # Podgórze Centrum
    "30-3": (50.0450, 19.9500),  # Podgórze Południe
    "30-4": (50.0680, 19.9600),  # Grzegórzki
    "30-5": (50.0750, 19.9450),  # Prądnik
    "30-6": (50.0850, 19.9300),  # Krowodrza
    "30-7": (50.0900, 19.9100),  # Bronowice
    "30-8": (50.0600, 19.8900),  # Zwierzyniec
    "30-9": (50.0500, 19.9200),  # Dębniki
    "31-0": (50.0650, 19.9350),  # Nowa Huta Centrum
    "31-1": (50.0700, 19.9700),  # Czyżyny
    "31-2": (50.0800, 19.9800),  # Nowa Huta
    "31-4": (50.0900, 19.9500),  # Mistrzejowice
    "31-5": (50.0950, 19.9200),  # Prądnik Biały
    "31-8": (50.0550, 19.9100),  # Skotniki
    "31-9": (50.0480, 19.9000),  # Tyniec
    "32": (50.0350, 19.9350),    # Wieliczka/Okolice

    # === WROCŁAW (50-54) ===
    "50-0": (51.1079, 17.0385),  # Stare Miasto
    "50-1": (51.1130, 17.0300),  # Nadodrze
    "50-2": (51.1050, 17.0450),  # Śródmieście Południe
    "50-3": (51.1000, 17.0550),  # Przedmieście Oławskie
    "50-4": (51.0950, 17.0400),  # Huby
    "50-5": (51.0900, 17.0500),  # Gaj
    "51-1": (51.1100, 17.0700),  # Psie Pole
    "51-2": (51.1200, 17.0800),  # Różanka
    "51-5": (51.1300, 17.0600),  # Sołtysowice
    "51-6": (51.1400, 17.0500),  # Widawa
    "52-1": (51.0850, 17.0200),  # Krzyki
    "52-2": (51.0800, 17.0100),  # Borek
    "52-4": (51.0700, 17.0000),  # Wojszyce
    "53-1": (51.1200, 17.0100),  # Biskupin
    "53-4": (51.1300, 17.0200),  # Zacisze
    "54-1": (51.1350, 17.0000),  # Karłowice
    "54-5": (51.1400, 16.9800),  # Osobowice

    # === POZNAŃ (60-61) ===
    "60-1": (52.4064, 16.9252),  # Stare Miasto
    "60-2": (52.4100, 16.9300),  # Jeżyce
    "60-3": (52.4150, 16.9400),  # Sołacz
    "60-4": (52.4000, 16.9350),  # Wilda
    "60-5": (52.3950, 16.9400),  # Dębiec
    "60-6": (52.4200, 16.9500),  # Winogrady
    "60-7": (52.4250, 16.9200),  # Grunwald
    "60-8": (52.4300, 16.9100),  # Ogrody
    "61-1": (52.3900, 16.9600),  # Rataje
    "61-3": (52.3850, 16.9700),  # Chartowo
    "61-5": (52.4350, 16.9600),  # Piątkowo
    "61-6": (52.4400, 16.9300),  # Strzeszyn

    # === GDAŃSK/TRÓJMIASTO (80-81) ===
    "80-0": (54.3520, 18.6466),  # Śródmieście
    "80-1": (54.3600, 18.6400),  # Stare Miasto
    "80-2": (54.3700, 18.6300),  # Wrzeszcz Dolny
    "80-3": (54.3800, 18.6200),  # Wrzeszcz Górny
    "80-4": (54.3550, 18.6600),  # Nowy Port
    "80-5": (54.3450, 18.6700),  # Letnica
    "80-6": (54.3900, 18.6100),  # Oliwa
    "80-7": (54.4000, 18.5900),  # Przymorze
    "80-8": (54.4100, 18.5700),  # Brzeźno
    "81-0": (54.5189, 18.5305),  # Gdynia Centrum
    "81-1": (54.5100, 18.5400),  # Gdynia Śródmieście
    "81-3": (54.5000, 18.5500),  # Gdynia Chylonia
    "81-5": (54.4950, 18.5600),  # Gdynia Cisowa
    "81-7": (54.4412, 18.5601),  # Sopot Centrum
    "81-8": (54.4350, 18.5650),  # Sopot Dolny

    # === ŁÓDŹ (90-94) ===
    "90-0": (51.7769, 19.4547),  # Śródmieście Północ
    "90-1": (51.7700, 19.4600),  # Śródmieście Centrum
    "90-2": (51.7650, 19.4700),  # Śródmieście Południe
    "90-3": (51.7800, 19.4400),  # Stare Polesie
    "90-4": (51.7850, 19.4300),  # Nowe Polesie
    "90-5": (51.7600, 19.4500),  # Centrum Handlowe
    "90-7": (51.7550, 19.4400),  # Karolew
    "91": (51.8000, 19.4700),    # Bałuty
    "92": (51.7500, 19.5000),    # Widzew
    "93": (51.7300, 19.4300),    # Górna
    "94": (51.7900, 19.5200),    # Polesie Wschodnie

    # === SZCZECIN (70-71) ===
    "70-0": (53.4289, 14.5530),  # Śródmieście
    "70-1": (53.4350, 14.5450),  # Centrum
    "70-2": (53.4400, 14.5600),  # Łasztownia
    "70-4": (53.4200, 14.5700),  # Niebuszewo
    "70-5": (53.4150, 14.5400),  # Pogodno
    "70-7": (53.4100, 14.5300),  # Gumieńce
    "71-0": (53.4500, 14.5800),  # Dąbie
    "71-2": (53.4600, 14.5500),  # Warszewo
    "71-4": (53.4700, 14.5300),  # Głębokie

    # === ŚLĄSK (40-44) ===
    # Katowice (40)
    "40-0": (50.2649, 19.0238),  # Śródmieście
    "40-1": (50.2580, 19.0300),  # Centrum Południe
    "40-2": (50.2500, 19.0400),  # Załęże
    "40-3": (50.2450, 19.0200),  # Dąb
    "40-4": (50.2700, 19.0100),  # Koszutka
    "40-5": (50.2750, 19.0000),  # Wełnowiec
    "40-6": (50.2800, 18.9900),  # Józefowiec
    "40-7": (50.2400, 19.0500),  # Brynów
    "40-8": (50.2350, 19.0300),  # Ligota
    "40-9": (50.2300, 19.0100),  # Piotrowice

    # Bytom (41-9)
    "41-9": (50.3484, 18.9152),  # Bytom Centrum

    # Sosnowiec (41-2)
    "41-2": (50.2865, 19.1044),  # Sosnowiec Centrum

    # Ruda Śląska (41-7)
    "41-7": (50.2559, 18.8558),  # Ruda Śląska Centrum

    # Zabrze (41-8)
    "41-8": (50.3249, 18.7857),  # Zabrze Centrum

    # Chorzów (41-5)
    "41-5": (50.2974, 18.9545),  # Chorzów Centrum

    # Gliwice (44)
    "44-1": (50.2945, 18.6714),  # Gliwice Centrum
    "44-2": (50.3000, 18.6800),  # Gliwice Wschód
    "44-3": (50.2900, 18.6600),  # Gliwice Zachód

    # Tychy (43-1)
    "43-1": (50.1078, 18.9985),  # Tychy Centrum

    # Bielsko-Biała (43-3)
    "43-3": (49.8224, 19.0444),  # Bielsko-Biała Centrum

    # Częstochowa (42)
    "42-2": (50.8118, 19.1203),  # Częstochowa Centrum
    "42-3": (50.8200, 19.1100),  # Częstochowa Północ

    # === INNE DUŻE MIASTA ===
    # Lublin (20)
    "20-0": (51.2465, 22.5684),  # Lublin Centrum

    # Rzeszów (35)
    "35-0": (50.0412, 21.9991),  # Rzeszów Centrum

    # Białystok (15)
    "15-0": (53.1325, 23.1688),  # Białystok Centrum

    # Bydgoszcz (85)
    "85-0": (53.1235, 18.0084),  # Bydgoszcz Centrum

    # Toruń (87)
    "87-1": (53.0138, 18.5984),  # Toruń Centrum

    # Kielce (25)
    "25-0": (50.8661, 20.6286),  # Kielce Centrum

    # Olsztyn (10)
    "10-0": (53.7784, 20.4801),  # Olsztyn Centrum

    # Opole (45)
    "45-0": (50.6751, 17.9213),  # Opole Centrum
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


# === OUTPUT CSV REQUIRED COLUMNS (Palantir-Enhanced) ===

OUTPUT_COLUMNS_REQUIRED = [
    "Imie",
    "Nazwisko",
    "Email",
    "Telefon",
    "TargetTier",
    "TotalScore",
    "Priority",
]

OUTPUT_COLUMNS_WEALTH = [
    "Wealth_Score",
    "Wealth_Tier",
    "Wealth_Signal",          # NEW: Explanation of WHY this score
    "M2_Price_Estimated",     # NEW: Estimated m² price
    "Resolved_City",          # NEW: City resolved from postal code
]

OUTPUT_COLUMNS_FINANCIAL = [
    "Potential_Savings_PLN",  # Renamed from Annual_Tax_Saving
    "Tax_Benefit_First_Year",
    "NaszEauto_Subsidy",
]

OUTPUT_COLUMNS_DNA = [
    "Lead_Type",              # NEW: Psychographic type (e.g., ALPHA_LAWYER)
    "Decision_Driver",        # NEW: What motivates this lead
    "Best_Hook",              # NEW: Recommended opening line
    "Objection_Killer",       # NEW: Pre-emptive objection handling
    "Closing_Trigger",        # NEW: What will close the deal
]

OUTPUT_COLUMNS_OPTIONAL = [
    "LeadDescription",
    "SniperHook",
    "TaxWeapon",
    "GothamInsight",
    "Lead_DNA_Summary",       # NEW: One-line DNA summary
]

# Full export columns in order
OUTPUT_COLUMNS_FULL = (
    OUTPUT_COLUMNS_REQUIRED +
    OUTPUT_COLUMNS_WEALTH +
    OUTPUT_COLUMNS_FINANCIAL +
    OUTPUT_COLUMNS_DNA +
    OUTPUT_COLUMNS_OPTIONAL
)


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
