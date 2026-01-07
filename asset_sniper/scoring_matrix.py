"""
ASSET SNIPER - Scoring Matrix Module (Palantir-Enhanced)
Algorytm klasyfikacji leadów do Tier S-E na podstawie scoringu 0-100

Scoring Components (100 pts max):
- PKD Tier: 0-30 pts
- Wealth Proxy (M²-Based): 0-25 pts
- Company Age: 0-20 pts
- Charger Proximity: 0-15 pts
- Contact Quality: 0-10 pts

New Features:
- LeadDNA profiling for Tier S/AAA leads
- Wealth_Signal explanation column
- Palantir-level asymmetric intelligence

Based on: BIBLE v1.0 + Palantir Upgrade
Author: BigDInc Team
"""

import pandas as pd
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import logging

from .config import (
    PKD_PROFILES,
    TIER_THRESHOLDS,
    SCORING_WEIGHTS,
    CHARGER_DISTANCE_POINTS,
    CONTACT_QUALITY_POINTS,
    Tier,
)

logger = logging.getLogger(__name__)


# === LEAD DNA PROFILING ===

@dataclass
class LeadDNA:
    """
    BigDecoder DNA - Psychographic profile of a high-value lead.
    Generated for Tier S and AAA leads only.
    """
    # Core identifiers
    lead_type: str           # e.g., "ALPHA_LAWYER", "TECH_ENTREPRENEUR"
    decision_driver: str     # e.g., "TAX_OPTIMIZATION", "STATUS", "ECO_CONSCIOUSNESS"
    urgency_trigger: str     # e.g., "LEASING_RENEWAL", "NEW_SUBSIDY", "COMPETITOR_PRESSURE"

    # Psychographic markers
    risk_appetite: str       # LOW, MEDIUM, HIGH
    price_sensitivity: str   # LOW, MEDIUM, HIGH
    tech_adoption: str       # EARLY_ADOPTER, MAINSTREAM, LAGGARD

    # Recommended approach
    best_hook: str           # First-sentence hook for cold call
    objection_killer: str    # Pre-emptive objection handling
    closing_trigger: str     # What will close the deal

    def to_dict(self) -> Dict:
        return {
            "lead_type": self.lead_type,
            "decision_driver": self.decision_driver,
            "urgency_trigger": self.urgency_trigger,
            "risk_appetite": self.risk_appetite,
            "price_sensitivity": self.price_sensitivity,
            "tech_adoption": self.tech_adoption,
            "best_hook": self.best_hook,
            "objection_killer": self.objection_killer,
            "closing_trigger": self.closing_trigger,
        }

    def to_summary(self) -> str:
        """One-line summary for CSV export."""
        return f"{self.lead_type}|{self.decision_driver}|{self.best_hook[:50]}"


def generate_lead_dna(pkd_code: str, wealth_tier: str, wealth_signal: str, leasing_cycle: str) -> Optional[LeadDNA]:
    """
    Generate LeadDNA profile based on PKD, wealth, and leasing cycle.

    Only generates DNA for high-value leads (PKD in Tier S/A or wealth_tier in S/PREMIUM/HIGH).

    Args:
        pkd_code: PKD industry code
        wealth_tier: Wealth tier from Gotham engine
        wealth_signal: Explanation of wealth score
        leasing_cycle: Current leasing cycle stage

    Returns:
        LeadDNA object or None for low-value leads
    """
    # === LAWYERS (6910Z) ===
    if pkd_code == "6910Z":
        return LeadDNA(
            lead_type="ALPHA_LAWYER",
            decision_driver="STATUS_AND_TAX" if wealth_tier in ["S", "PREMIUM"] else "TAX_OPTIMIZATION",
            urgency_trigger="LEASING_RENEWAL" if leasing_cycle in ["RENEWAL_WINDOW", "PRIME_LEASING"] else "TAX_YEAR_END",
            risk_appetite="LOW",
            price_sensitivity="LOW",
            tech_adoption="MAINSTREAM",
            best_hook="Panie Mecenasie, do 24 000 PLN rocznie więcej w kosztach firmowych - i prestiż który buduje zaufanie klientów",
            objection_killer="Większość kancelarii już to rozważa - ale Ci którzy działają pierwsi, zyskują przewagę wizerunkową",
            closing_trigger="Konkretne liczby + prestiż marki"
        )

    # === ACCOUNTANTS (6920Z) ===
    elif pkd_code == "6920Z":
        return LeadDNA(
            lead_type="ANALYTICAL_CFO",
            decision_driver="ROI_OPTIMIZATION",
            urgency_trigger="TAX_YEAR_PLANNING" if leasing_cycle == "UNKNOWN" else "LEASING_RENEWAL",
            risk_appetite="LOW",
            price_sensitivity="MEDIUM",
            tech_adoption="MAINSTREAM",
            best_hook="Jako specjalista od optymalizacji - 75 000 PLN wyższa amortyzacja, 14 250 PLN/rok w kieszeni",
            objection_killer="Te liczby są proste - sprawdzi Pan w 5 minut. Mogę wysłać kalkulator?",
            closing_trigger="Excel z TCO vs ICE"
        )

    # === IT / PROGRAMMERS (6201Z) ===
    elif pkd_code == "6201Z":
        return LeadDNA(
            lead_type="TECH_ENTREPRENEUR",
            decision_driver="TECHNOLOGY_AND_ECO",
            urgency_trigger="NEW_MODEL_LAUNCH" if wealth_tier in ["S", "PREMIUM", "HIGH"] else "FUEL_PRICE_SPIKE",
            risk_appetite="HIGH",
            price_sensitivity="MEDIUM",
            tech_adoption="EARLY_ADOPTER",
            best_hook="OTA updates, 0-100 w 3.5s, i technologia która się dosłownie zwraca - dla IT to naturalny wybór",
            objection_killer="Większość programistów którzy testują, kupuje - bo rozumieją technologię",
            closing_trigger="Jazda testowa + demo aplikacji Tesla"
        )

    # === DOCTORS (8621Z) ===
    elif pkd_code == "8621Z":
        return LeadDNA(
            lead_type="TIME_POOR_PROFESSIONAL",
            decision_driver="TIME_SAVINGS_AND_TAX",
            urgency_trigger="LEASING_RENEWAL",
            risk_appetite="MEDIUM",
            price_sensitivity="LOW",
            tech_adoption="MAINSTREAM",
            best_hook="Panie Doktorze, czas to pieniądz - Supercharger 15 minut, Autopilot w korkach, 24 000 PLN/rok w podatkach",
            objection_killer="Lekarze są drugą grupą po prawnikach która najczęściej wybiera EV - wiedzą jak liczyć",
            closing_trigger="Oszczędność czasu + konkretne liczby"
        )

    # === TRANSPORT (4941Z) ===
    elif pkd_code == "4941Z":
        return LeadDNA(
            lead_type="FLEET_OPERATOR",
            decision_driver="COST_REDUCTION",
            urgency_trigger="FUEL_PRICE_SPIKE",
            risk_appetite="MEDIUM",
            price_sensitivity="HIGH",
            tech_adoption="LAGGARD",
            best_hook="Paliwo zjada marżę - mogę pokazać jak obniżyć koszty floty o 40%",
            objection_killer="Semi-Truck Tesla to przyszłość, ale zaczynamy od aut osobowych dla zarządu",
            closing_trigger="Kalkulator TCO floty"
        )

    # === HIGH-WEALTH NON-SPECIFIC ===
    elif wealth_tier in ["S", "PREMIUM"]:
        return LeadDNA(
            lead_type="AFFLUENT_ENTREPRENEUR",
            decision_driver="STATUS" if "premium" in wealth_signal.lower() else "TAX_AND_STATUS",
            urgency_trigger="SOCIAL_PROOF",
            risk_appetite="MEDIUM",
            price_sensitivity="LOW",
            tech_adoption="MAINSTREAM",
            best_hook="W Pana lokalizacji Tesla to standard wśród przedsiębiorców - mogę pokazać dlaczego",
            objection_killer="To nie jest wydatek, to inwestycja w wizerunek i oszczędności",
            closing_trigger="Social proof + jazda testowa"
        )

    # === HIGH-WEALTH STREET SIGNAL ===
    elif "prestiżowa" in wealth_signal.lower() or "premium" in wealth_signal.lower():
        return LeadDNA(
            lead_type="LOCATION_PREMIUM",
            decision_driver="STATUS",
            urgency_trigger="COMPETITOR_PRESSURE",
            risk_appetite="MEDIUM",
            price_sensitivity="LOW",
            tech_adoption="MAINSTREAM",
            best_hook="W Państwa lokalizacji Tesla to już standard - i jest powód dlaczego",
            objection_killer="Sąsiedzi już jeżdżą - pytanie czy chce Pan być następny czy ostatni",
            closing_trigger="Local social proof"
        )

    return None


class ScoringMatrix:
    """
    Lead scoring and tier classification engine.

    Calculates score 0-100 based on:
    1. PKD industry tier (S/A/B/default)
    2. Wealth proxy (region wealth)
    3. Company age (leasing cycle)
    4. Charger proximity
    5. Contact quality (phone/email/www)

    Output: Tier assignment (S/AAA/AA/A/B/C/D/E)
    """

    @staticmethod
    def score_pkd(pkd_code: str) -> Tuple[int, str]:
        """
        Score based on PKD industry code.

        Scoring:
        - Tier S industries (lawyers, accountants): 30 pts
        - Tier A industries (IT, medical, transport): 22 pts
        - Tier B industries (consulting, etc.): 15 pts
        - Default: 8 pts

        Args:
            pkd_code: PKD code (e.g., "6910Z")

        Returns:
            Tuple of (score, tier_name)
        """
        if not pkd_code:
            return 8, "DEFAULT"

        # Exact match
        if pkd_code in PKD_PROFILES:
            profile = PKD_PROFILES[pkd_code]
            return profile["score"], profile["tier"]

        # Fallback
        return PKD_PROFILES["DEFAULT"]["score"], "DEFAULT"

    @staticmethod
    def score_wealth(wealth_score: int, wealth_tier: str) -> int:
        """
        Score based on region wealth.

        Scoring:
        - PREMIUM (9-10): 25 pts
        - HIGH (7-8): 20 pts
        - MEDIUM (5-6): 15 pts
        - STANDARD (3-4): 10 pts
        - LOW (1-2): 5 pts

        Args:
            wealth_score: Wealth score 1-10
            wealth_tier: Tier name (PREMIUM/HIGH/MEDIUM/STANDARD/LOW)

        Returns:
            Score 0-25
        """
        if wealth_tier == "PREMIUM":
            return 25
        elif wealth_tier == "HIGH":
            return 20
        elif wealth_tier == "MEDIUM":
            return 15
        elif wealth_tier == "STANDARD":
            return 10
        else:  # LOW
            return 5

    @staticmethod
    def score_company_age(age_years: float, leasing_propensity: float) -> int:
        """
        Score based on company age and leasing cycle.

        Scoring logic:
        - Prime leasing window (3-6 years): 20 pts
        - Established (7+ years): 18 pts
        - Growth phase (2-3 years): 15 pts
        - Early (1-2 years): 10 pts
        - Startup (0-1 years): 5 pts

        Args:
            age_years: Company age in years
            leasing_propensity: Leasing propensity 0-1

        Returns:
            Score 0-20
        """
        if 3 <= age_years < 6:
            return 20  # Prime leasing window
        elif age_years >= 7:
            return 18  # Established
        elif 2 <= age_years < 3:
            return 15  # Growth
        elif 1 <= age_years < 2:
            return 10  # Early
        else:
            return 5   # Startup

    @staticmethod
    def score_charger_proximity(distance_km: float) -> int:
        """
        Score based on charger distance.

        Scoring:
        - <5km: 15 pts (excellent)
        - <10km: 12 pts (very good)
        - <20km: 9 pts (good)
        - <30km: 6 pts (acceptable)
        - <50km: 3 pts (marginal)
        - 50km+: 0 pts (poor)

        Args:
            distance_km: Distance to nearest charger in km

        Returns:
            Score 0-15
        """
        if distance_km == 0:
            return 0  # No data

        for threshold, points in sorted(CHARGER_DISTANCE_POINTS.items()):
            if distance_km < threshold:
                return points

        return 0  # 50km+

    @staticmethod
    def score_contact_quality(has_phone: bool, has_email: bool, has_www: bool) -> int:
        """
        Score based on contact information completeness.

        Scoring:
        - Phone: +5 pts
        - Email: +3 pts
        - Website: +2 pts
        - Max: 10 pts

        Args:
            has_phone: Has valid phone number
            has_email: Has valid email
            has_www: Has website

        Returns:
            Score 0-10
        """
        score = 0
        if has_phone:
            score += CONTACT_QUALITY_POINTS["phone"]
        if has_email:
            score += CONTACT_QUALITY_POINTS["email"]
        if has_www:
            score += CONTACT_QUALITY_POINTS["www"]
        return score

    @staticmethod
    def assign_tier(total_score: int) -> Tuple[str, str, str]:
        """
        Assign tier based on total score.

        Tier thresholds:
        - S (85-100): NATYCHMIAST - Telefon w ciągu 24h
        - AAA (75-84): DZIŚ - Kontakt tego dnia
        - AA (65-74): TEN TYDZIEŃ - Kontakt w tym tygodniu
        - A (50-64): AUTOMAT - Sekwencja automatyczna
        - B (35-49): NISKI - Raz w miesiącu
        - C-E (0-34): ARCHIWUM - Ignoruj

        Args:
            total_score: Total score 0-100

        Returns:
            Tuple of (tier, priority, action)
        """
        for tier, (min_score, max_score, priority, action) in TIER_THRESHOLDS.items():
            if min_score <= total_score <= max_score:
                return tier.value, priority.value, action

        # Fallback
        return Tier.E.value, "ARCHIWUM", "Ignoruj"

    def score_lead(self, row: pd.Series) -> Dict:
        """
        Calculate complete score for single lead with Palantir intelligence.

        Args:
            row: pandas Series with lead data

        Returns:
            Dictionary with score breakdown and LeadDNA
        """
        # Extract data (handle both old and new column names)
        pkd_code = row.get('pkd_clean', '') or row.get('PkdGlowny', '') or ''
        wealth_score = row.get('wealth_score', 5)
        wealth_tier = row.get('wealth_tier', 'STANDARD')
        wealth_signal = row.get('wealth_signal', '')
        age_years = row.get('company_age_years', 0.0)
        leasing_propensity = row.get('leasing_propensity', 0.0)
        leasing_cycle = row.get('leasing_cycle', 'UNKNOWN')
        charger_distance = row.get('charger_distance_km', 0.0)
        has_phone = bool(row.get('telefon_clean', '') or row.get('Telefon', ''))
        has_email = bool(row.get('email_clean', '') or row.get('Email', ''))
        has_www = bool(row.get('AdresWWW', ''))

        # Calculate component scores
        pkd_score, pkd_tier = self.score_pkd(pkd_code)
        wealth_score_pts = self.score_wealth(wealth_score, wealth_tier)
        age_score = self.score_company_age(age_years, leasing_propensity)
        charger_score = self.score_charger_proximity(charger_distance)
        contact_score = self.score_contact_quality(has_phone, has_email, has_www)

        # Calculate total
        total_score = pkd_score + wealth_score_pts + age_score + charger_score + contact_score

        # Assign tier
        tier, priority, action = self.assign_tier(total_score)

        # Generate LeadDNA for high-value leads (Tier S, AAA, or high wealth)
        lead_dna = None
        lead_dna_summary = None
        if tier in ["S", "AAA"] or wealth_tier in ["S", "PREMIUM"]:
            lead_dna = generate_lead_dna(pkd_code, wealth_tier, wealth_signal, leasing_cycle)
            if lead_dna:
                lead_dna_summary = lead_dna.to_summary()

        return {
            'total_score': total_score,
            'target_tier': tier,
            'priority': priority,
            'next_action': action,
            'score_breakdown': {
                'pkd': pkd_score,
                'wealth': wealth_score_pts,
                'age': age_score,
                'charger': charger_score,
                'contact': contact_score,
            },
            'lead_dna': lead_dna,
            'lead_dna_summary': lead_dna_summary,
        }

    def score_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Score all leads in DataFrame with Palantir-enhanced intelligence.

        Adds columns:
        - total_score (int 0-100)
        - target_tier (str: S/AAA/AA/A/B/C/D/E)
        - priority (str)
        - next_action (str)
        - lead_dna_summary (str) - For Tier S/AAA leads only
        - lead_type (str) - Psychographic type
        - best_hook (str) - Recommended opening line
        - decision_driver (str) - What motivates this lead

        Args:
            df: DataFrame with Gotham-enriched data

        Returns:
            DataFrame with scoring columns and LeadDNA profiles added
        """
        logger.info(f"[SCORING-PALANTIR] Scoring {len(df)} leads with DNA profiling...")

        df_scored = df.copy()

        # Score each row
        score_results = df_scored.apply(self.score_lead, axis=1)

        # Extract core results
        df_scored['total_score'] = score_results.apply(lambda x: x['total_score'])
        df_scored['target_tier'] = score_results.apply(lambda x: x['target_tier'])
        df_scored['priority'] = score_results.apply(lambda x: x['priority'])
        df_scored['next_action'] = score_results.apply(lambda x: x['next_action'])

        # Extract LeadDNA for high-value leads
        df_scored['lead_dna_summary'] = score_results.apply(lambda x: x.get('lead_dna_summary', ''))

        # Extract individual DNA components for Tier S/AAA leads
        def extract_dna_field(result, field):
            dna = result.get('lead_dna')
            if dna:
                return getattr(dna, field, '')
            return ''

        df_scored['lead_type'] = score_results.apply(lambda x: extract_dna_field(x, 'lead_type'))
        df_scored['decision_driver'] = score_results.apply(lambda x: extract_dna_field(x, 'decision_driver'))
        df_scored['best_hook'] = score_results.apply(lambda x: extract_dna_field(x, 'best_hook'))
        df_scored['objection_killer'] = score_results.apply(lambda x: extract_dna_field(x, 'objection_killer'))
        df_scored['closing_trigger'] = score_results.apply(lambda x: extract_dna_field(x, 'closing_trigger'))

        # Log tier distribution
        tier_counts = df_scored['target_tier'].value_counts()
        logger.info("[SCORING-PALANTIR] Tier distribution:")
        for tier, count in sorted(tier_counts.items(), key=lambda x: ['S', 'AAA', 'AA', 'A', 'B', 'C', 'D', 'E'].index(x[0]) if x[0] in ['S', 'AAA', 'AA', 'A', 'B', 'C', 'D', 'E'] else 99):
            pct = count / len(df_scored) * 100
            logger.info(f"  {tier}: {count} ({pct:.1f}%)")

        # Log DNA generation stats
        dna_count = df_scored['lead_dna_summary'].apply(lambda x: x != '').sum()
        logger.info(f"[SCORING-PALANTIR] LeadDNA profiles generated: {dna_count} ({dna_count/len(df_scored)*100:.1f}%)")

        logger.info(f"[SCORING-PALANTIR] Scoring complete.")
        return df_scored


# === CLI TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("SCORING MATRIX - Palantir-Enhanced Test")
    print("=" * 60 + "\n")

    # Test data with wealth_signal for LeadDNA profiling
    test_data = {
        'pkd_clean': ['6910Z', '6201Z', '4941Z', '7022Z', '8621Z', '6920Z'],
        'wealth_score': [10, 8, 5, 7, 9, 8],
        'wealth_tier': ['S', 'HIGH', 'STANDARD', 'MEDIUM', 'PREMIUM', 'HIGH'],
        'wealth_signal': [
            'Miasto Warszawa - cena m² 17,500 PLN | Dzielnica premium: Śródmieście',
            'Miasto Katowice - cena m² 10,500 PLN',
            'Brak danych lokalizacji - użyto średniej krajowej',
            'Miasto Częstochowa - cena m² 7,800 PLN',
            'Miasto Gdańsk - cena m² 13,800 PLN | Ulica prestiżowa: Długa',
            'Miasto Kraków - cena m² 14,800 PLN',
        ],
        'company_age_years': [5.2, 2.5, 0.8, 8.1, 4.0, 3.5],
        'leasing_propensity': [0.95, 0.50, 0.15, 0.90, 0.80, 0.80],
        'leasing_cycle': ['RENEWAL_WINDOW', 'GROWTH', 'STARTUP', 'VETERAN', 'PRIME_LEASING', 'PRIME_LEASING'],
        'charger_distance_km': [2.5, 8.3, 15.0, 25.0, 5.0, 3.0],
        'telefon_clean': ['48500100200', '48501200300', '', '48502300400', '48503400500', '48504500600'],
        'email_clean': ['jan@kancelaria.pl', 'anna@it.pl', '', 'tomasz@consulting.pl', 'dr.kowalski@med.pl', 'biuro@ksiegowi.pl'],
        'AdresWWW': ['www.kancelaria.pl', '', '', 'www.consulting.pl', 'www.klinika.pl', 'www.ksiegowi.pl'],
    }

    df_test = pd.DataFrame(test_data)

    print("📊 Input data:")
    print(df_test[['pkd_clean', 'wealth_tier', 'company_age_years']])
    print()

    # Score leads
    scoring = ScoringMatrix()
    df_result = scoring.score_all(df_test)

    print("\n📈 Scoring Results:")
    score_cols = ['total_score', 'target_tier', 'priority', 'next_action']
    print(df_result[score_cols])
    print()

    print("🧬 LeadDNA Profiles (Tier S/AAA only):")
    dna_cols = ['target_tier', 'lead_type', 'decision_driver', 'best_hook']
    df_dna = df_result[df_result['lead_type'] != ''][dna_cols]
    if not df_dna.empty:
        for idx, row in df_dna.iterrows():
            print(f"\n  [{row['target_tier']}] {row['lead_type']}")
            print(f"      Driver: {row['decision_driver']}")
            print(f"      Hook: {row['best_hook'][:60]}...")
    else:
        print("  No high-value leads with DNA profiles in test data")
    print()

    print("=" * 60)
    print("✅ Scoring Matrix Palantir Test Complete!")
    print("=" * 60)
