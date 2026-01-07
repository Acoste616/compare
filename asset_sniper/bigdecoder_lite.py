"""
ASSET SNIPER - BigDecoder Lite Module
Generator spersonalizowanych komunikatów sprzedażowych

Generates:
- SniperHook: Personalized cold call hook
- TaxWeapon: Concrete tax argument with numbers
- LeadDescription: Short lead summary for salesperson

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import pandas as pd
from typing import Dict
import logging

from .config import PKD_PROFILES, TAX_BENEFITS

logger = logging.getLogger(__name__)


class BigDecoderLite:
    """
    Lightweight version of psychographic profiling and message generation.

    Generates:
    1. SniperHook - Personalized opening line for cold call
    2. TaxWeapon - Concrete tax savings argument
    3. LeadDescription - Brief lead summary for salesperson

    NOTE: This is the "Lite" version using templates.
    Full BigDecoder uses AI for deep psychographic analysis.
    """

    @staticmethod
    def generate_sniper_hook(
        first_name: str,
        pkd_code: str,
        city: str,
        wealth_tier: str,
        tax_benefit: float,
        charger_distance: float
    ) -> str:
        """
        Generate personalized cold call hook.

        Hook structure:
        [Greeting] + [Industry-specific pain point] + [Concrete benefit]

        Args:
            first_name: First name of contact
            pkd_code: PKD industry code
            city: City name
            wealth_tier: Wealth tier (PREMIUM/HIGH/etc.)
            tax_benefit: Annual tax benefit in PLN
            charger_distance: Distance to nearest charger in km

        Returns:
            Personalized hook string
        """
        # Get PKD profile
        profile = PKD_PROFILES.get(pkd_code, PKD_PROFILES["DEFAULT"])

        # Greeting
        greeting = f"Dzień dobry Panie/Pani {first_name}!" if first_name else "Dzień dobry!"

        # Build hook based on profile
        if profile["tier"] == "S" and profile.get("tax_benefit_focus"):
            # Tax-focused hook (lawyers, accountants)
            hook = f"{greeting} {profile['hook_angle']}. "
            hook += f"W przypadku Pana/Pani firmy to {tax_benefit:,.0f} PLN rocznie. "

            if charger_distance > 0 and charger_distance < 10:
                hook += f"A najbliższa ładowarka jest tylko {charger_distance:.1f} km od {city}."
        elif profile["tier"] == "A":
            # Value-focused hook (IT, medical, transport)
            hook = f"{greeting} {profile['hook_angle']}. "

            if tax_benefit > 0:
                hook += f"Konkretnie: {tax_benefit:,.0f} PLN oszczędności rocznie. "

            if charger_distance > 0 and charger_distance < 15:
                hook += f"Plus ładowarka {charger_distance:.1f} km od biura."
        else:
            # Generic hook
            hook = f"{greeting} Chciałbym porozmawiać o oszczędnościach dla Pana/Pani firmy. "
            if tax_benefit > 0:
                hook += f"Tesla może zaoszczędzić {tax_benefit:,.0f} PLN rocznie w kosztach firmowych."

        return hook.strip()

    @staticmethod
    def generate_tax_weapon(
        pkd_code: str,
        legal_form: str,
        tax_benefit_annual: float
    ) -> str:
        """
        Generate concrete tax argument with numbers.

        Format:
        OSZCZĘDNOŚĆ PODATKOWA: do X PLN/rok | EV: limit Y PLN | ICE: limit Z PLN

        Args:
            pkd_code: PKD industry code
            legal_form: Legal form of company
            tax_benefit_annual: Annual tax benefit

        Returns:
            Tax weapon string
        """
        ev_limit = TAX_BENEFITS["EV_AMORTYZACJA_LIMIT"]
        ice_limit = TAX_BENEFITS["ICE_AMORTYZACJA_LIMIT"]

        # Determine tax rate
        profile = PKD_PROFILES.get(pkd_code, PKD_PROFILES["DEFAULT"])
        tax_rate = profile.get("tax_rate", 19)

        weapon = f"OSZCZĘDNOŚĆ PODATKOWA: do {tax_benefit_annual:,.0f} PLN/rok ({tax_rate}% stawka) | "
        weapon += f"EV: pełna amortyzacja do {ev_limit:,.0f} PLN | "
        weapon += f"Spalinowe: tylko do {ice_limit:,.0f} PLN | "
        weapon += f"Dotacja NaszEauto: {TAX_BENEFITS['NASZEAUTO_STANDARD']:,.0f} PLN"

        return weapon

    @staticmethod
    def generate_lead_description(
        profile_name: str,
        city: str,
        charger_distance: float,
        company_age_years: float,
        wealth_tier: str,
        leasing_cycle: str
    ) -> str:
        """
        Generate brief lead summary for salesperson.

        Format:
        [Profile] z [City], [insight1], [insight2], [insight3]

        Args:
            profile_name: Industry profile name (e.g., "Prawnik")
            city: City name
            charger_distance: Distance to charger
            company_age_years: Company age in years
            wealth_tier: Wealth tier
            leasing_cycle: Leasing cycle stage

        Returns:
            Lead description string
        """
        insights = []

        # Insight 1: Charger proximity
        if charger_distance > 0:
            if charger_distance < 5:
                insights.append(f"ładowarka {charger_distance:.1f}km (doskonały dostęp)")
            elif charger_distance < 10:
                insights.append(f"ładowarka {charger_distance:.1f}km")
            elif charger_distance < 20:
                insights.append(f"ładowarka {charger_distance:.1f}km (akceptowalne)")

        # Insight 2: Leasing cycle
        if "RENEWAL" in leasing_cycle or "MATURE" in leasing_cycle:
            insights.append(f"firma {company_age_years:.0f} lat (cykl wymiany)")
        elif company_age_years > 0:
            insights.append(f"firma {company_age_years:.0f} lat")

        # Insight 3: Location quality
        if wealth_tier == "PREMIUM":
            insights.append("lokalizacja premium")
        elif wealth_tier == "HIGH":
            insights.append("dobra lokalizacja")

        # Build description
        desc = f"{profile_name} z {city}"
        if insights:
            desc += ", " + ", ".join(insights)

        return desc

    def enrich_messages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate messages for all leads (Tier S-A only).

        Adds columns:
        - sniper_hook (str)
        - tax_weapon (str)
        - lead_description (str)

        Args:
            df: DataFrame with scored leads

        Returns:
            DataFrame with message columns added
        """
        logger.info(f"[BIGDECODER] Generating messages...")

        df_enriched = df.copy()

        # Initialize message columns
        df_enriched['sniper_hook'] = ""
        df_enriched['tax_weapon'] = ""
        df_enriched['lead_description'] = ""

        # Find relevant columns
        tier_col = self._find_column(df_enriched, ['target_tier', 'Tier'])
        first_name_col = self._find_column(df_enriched, ['first_name_clean', 'Imie', 'imie'])
        pkd_col = self._find_column(df_enriched, ['pkd_clean', 'GlownyKodPkd', 'pkd'])
        city_col = self._find_column(df_enriched, ['city_clean', 'Miejscowosc', 'city'])
        form_col = self._find_column(df_enriched, ['legal_form_clean', 'FormaPrawna'])

        if not tier_col:
            logger.warning("[BIGDECODER] Tier column not found - cannot filter leads")
            return df_enriched

        # Filter to Tier S-A only (high-value leads)
        tier_mask = df_enriched[tier_col].isin(['S', 'AAA', 'AA', 'A'])
        target_indices = df_enriched[tier_mask].index.tolist()

        logger.info(f"[BIGDECODER] Generating messages for {len(target_indices)} Tier S-A leads")

        # Generate messages for each lead
        for idx in target_indices:
            row = df_enriched.loc[idx]

            # Extract data
            first_name = str(row.get(first_name_col, '')) if first_name_col else ''
            pkd_code = str(row.get(pkd_col, '')) if pkd_col else ''
            city = str(row.get(city_col, '')) if city_col else ''
            legal_form = str(row.get(form_col, '')) if form_col else ''
            wealth_tier = str(row.get('wealth_tier', 'STANDARD'))
            charger_distance = float(row.get('charger_distance_km', 0.0))
            tax_benefit = float(row.get('tax_benefit_annual', 0.0))
            company_age = float(row.get('company_age_years', 0.0))
            leasing_cycle = str(row.get('leasing_cycle', ''))

            # Get profile name
            profile = PKD_PROFILES.get(pkd_code, PKD_PROFILES["DEFAULT"])
            profile_name = profile.get("name", "Przedsiębiorca")

            # Generate messages
            try:
                sniper_hook = self.generate_sniper_hook(
                    first_name, pkd_code, city, wealth_tier, tax_benefit, charger_distance
                )
                tax_weapon = self.generate_tax_weapon(pkd_code, legal_form, tax_benefit)
                lead_desc = self.generate_lead_description(
                    profile_name, city, charger_distance, company_age, wealth_tier, leasing_cycle
                )

                df_enriched.at[idx, 'sniper_hook'] = sniper_hook
                df_enriched.at[idx, 'tax_weapon'] = tax_weapon
                df_enriched.at[idx, 'lead_description'] = lead_desc

            except Exception as e:
                logger.error(f"[BIGDECODER] Error generating messages for row {idx}: {e}")

        logger.info(f"[BIGDECODER] Message generation complete")
        return df_enriched

    @staticmethod
    def _find_column(df: pd.DataFrame, possible_names: list):
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
    print("=== BigDecoder Lite Test ===\n")

    # Test message generation
    hook = BigDecoderLite.generate_sniper_hook(
        first_name="Jan",
        pkd_code="6910Z",
        city="Katowice",
        wealth_tier="PREMIUM",
        tax_benefit=24000.0,
        charger_distance=2.5
    )

    tax_weapon = BigDecoderLite.generate_tax_weapon(
        pkd_code="6910Z",
        legal_form="SPÓŁKA Z O.O.",
        tax_benefit_annual=24000.0
    )

    lead_desc = BigDecoderLite.generate_lead_description(
        profile_name="Prawnik",
        city="Katowice",
        charger_distance=2.5,
        company_age_years=5.2,
        wealth_tier="PREMIUM",
        leasing_cycle="RENEWAL_WINDOW"
    )

    print("Sniper Hook:")
    print(hook)
    print()

    print("Tax Weapon:")
    print(tax_weapon)
    print()

    print("Lead Description:")
    print(lead_desc)
    print()

    print("✅ BigDecoder Lite Test Complete!")
