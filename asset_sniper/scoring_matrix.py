"""
ASSET SNIPER - Scoring Matrix Module
Algorytm klasyfikacji leadów do Tier S-E na podstawie scoringu 0-100

Scoring Components (100 pts max):
- PKD Tier: 0-30 pts
- Wealth Proxy: 0-25 pts
- Company Age: 0-20 pts
- Charger Proximity: 0-15 pts
- Contact Quality: 0-10 pts

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import pandas as pd
from typing import Dict, Tuple
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
        Calculate complete score for single lead.

        Args:
            row: pandas Series with lead data

        Returns:
            Dictionary with score breakdown
        """
        # Extract data
        pkd_code = row.get('pkd_clean', '')
        wealth_score = row.get('wealth_score', 5)
        wealth_tier = row.get('wealth_tier', 'STANDARD')
        age_years = row.get('company_age_years', 0.0)
        leasing_propensity = row.get('leasing_propensity', 0.0)
        charger_distance = row.get('charger_distance_km', 0.0)
        has_phone = bool(row.get('telefon_clean', ''))
        has_email = bool(row.get('email_clean', ''))
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
        }

    def score_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Score all leads in DataFrame.

        Adds columns:
        - total_score (int 0-100)
        - target_tier (str: S/AAA/AA/A/B/C/D/E)
        - priority (str)
        - next_action (str)

        Args:
            df: DataFrame with Gotham-enriched data

        Returns:
            DataFrame with scoring columns added
        """
        logger.info(f"[SCORING] Scoring {len(df)} leads...")

        df_scored = df.copy()

        # Score each row
        score_results = df_scored.apply(self.score_lead, axis=1)

        # Extract results
        df_scored['total_score'] = score_results.apply(lambda x: x['total_score'])
        df_scored['target_tier'] = score_results.apply(lambda x: x['target_tier'])
        df_scored['priority'] = score_results.apply(lambda x: x['priority'])
        df_scored['next_action'] = score_results.apply(lambda x: x['next_action'])

        # Log tier distribution
        tier_counts = df_scored['target_tier'].value_counts()
        logger.info("[SCORING] Tier distribution:")
        for tier, count in tier_counts.items():
            pct = count / len(df_scored) * 100
            logger.info(f"  {tier}: {count} ({pct:.1f}%)")

        logger.info(f"[SCORING] Scoring complete.")
        return df_scored


# === CLI TEST ===

if __name__ == "__main__":
    print("=== Scoring Matrix Test ===\n")

    # Test data
    test_data = {
        'pkd_clean': ['6910Z', '6201Z', '4941Z', '7022Z'],
        'wealth_score': [9, 8, 5, 7],
        'wealth_tier': ['PREMIUM', 'HIGH', 'STANDARD', 'MEDIUM'],
        'company_age_years': [5.2, 2.5, 0.8, 8.1],
        'leasing_propensity': [0.95, 0.50, 0.15, 0.90],
        'charger_distance_km': [2.5, 8.3, 15.0, 25.0],
        'telefon_clean': ['48500100200', '48501200300', '', '48502300400'],
        'email_clean': ['jan@kancelaria.pl', 'anna@it.pl', '', 'tomasz@consulting.pl'],
        'AdresWWW': ['www.kancelaria.pl', '', '', 'www.consulting.pl'],
    }

    df_test = pd.DataFrame(test_data)

    print("Input data:")
    print(df_test[['pkd_clean', 'wealth_tier', 'company_age_years', 'charger_distance_km']])
    print()

    # Score leads
    scoring = ScoringMatrix()
    df_result = scoring.score_all(df_test)

    print("Scored data:")
    score_cols = ['total_score', 'target_tier', 'priority', 'next_action']
    print(df_result[score_cols])
    print()

    print("✅ Scoring Matrix Test Complete!")
