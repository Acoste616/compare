"""
ASSET SNIPER - Main Orchestrator
CLI i programowy interfejs do całego pipeline

Usage:
    python -m asset_sniper.main --input leads.csv --output enriched.csv
    python -m asset_sniper.main --input leads.csv --output enriched.csv --all-tiers

Programmatic:
    from asset_sniper import AssetSniper
    sniper = AssetSniper()
    df = sniper.process('input.csv', 'output.csv')

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import argparse
import pandas as pd
from pathlib import Path
from typing import Optional
import logging
import time

from .lead_refinery import LeadRefinery
from .gotham_engine import GothamEngine
from .scoring_matrix import ScoringMatrix
from .bigdecoder_lite import BigDecoderLite
from .config import OUTPUT_COLUMNS_REQUIRED, OUTPUT_COLUMNS_OPTIONAL

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class AssetSniper:
    """
    Main Asset Sniper orchestrator.

    Pipeline stages:
    1. Lead Refinery - Data cleaning & normalization
    2. Gotham Engine - Market intelligence layers
    3. Scoring Matrix - Tier classification (S-E)
    4. BigDecoder Lite - Message generation

    Output: Enriched CSV ready for CRM bot import
    """

    def __init__(self):
        """Initialize Asset Sniper with all components."""
        self.refinery = LeadRefinery()
        self.gotham = GothamEngine()
        self.scoring = ScoringMatrix()
        self.bigdecoder = BigDecoderLite()

        logger.info("=== ASSET SNIPER v1.0 ===")
        logger.info("Data Refinery for B2B Tesla Leads")
        logger.info("")

    def process(
        self,
        input_path: str,
        output_path: str,
        require_phone: bool = True,
        require_email: bool = False,
        all_tiers: bool = False
    ) -> pd.DataFrame:
        """
        Process CSV through complete Asset Sniper pipeline.

        Args:
            input_path: Path to input CSV file
            output_path: Path to output CSV file
            require_phone: Filter out leads without phone
            require_email: Filter out leads without email
            all_tiers: If False, output only Tier S-A. If True, output all tiers.

        Returns:
            Enriched DataFrame
        """
        start_time = time.time()

        logger.info(f"📂 Input file: {input_path}")
        logger.info(f"📂 Output file: {output_path}")
        logger.info("")

        # === STAGE 1: LOAD CSV ===
        logger.info("=== STAGE 1: Loading CSV ===")
        try:
            df = pd.read_csv(input_path)
            logger.info(f"✅ Loaded {len(df)} rows")
        except Exception as e:
            logger.error(f"❌ Failed to load CSV: {e}")
            raise

        # === STAGE 2: LEAD REFINERY ===
        logger.info("")
        logger.info("=== STAGE 2: Lead Refinery (Data Cleaning) ===")
        df = self.refinery.refine(df, require_phone=require_phone, require_email=require_email)
        logger.info(f"✅ Refined: {len(df)} rows")

        # === STAGE 3: GOTHAM ENGINE ===
        logger.info("")
        logger.info("=== STAGE 3: Gotham Engine (Market Intelligence) ===")
        df = self.gotham.process(df)
        logger.info(f"✅ Enriched with Gotham layers")

        # === STAGE 4: SCORING MATRIX ===
        logger.info("")
        logger.info("=== STAGE 4: Scoring Matrix (Tier Classification) ===")
        df = self.scoring.score_all(df)
        logger.info(f"✅ Scored and tiered")

        # === STAGE 5: BIGDECODER LITE ===
        logger.info("")
        logger.info("=== STAGE 5: BigDecoder Lite (Message Generation) ===")
        df = self.bigdecoder.enrich_messages(df)
        logger.info(f"✅ Messages generated")

        # === STAGE 6: FILTER & EXPORT ===
        logger.info("")
        logger.info("=== STAGE 6: Export to CSV ===")

        # Filter by tier if needed
        if not all_tiers:
            tier_mask = df['target_tier'].isin(['S', 'AAA', 'AA', 'A'])
            df_output = df[tier_mask].copy()
            logger.info(f"📊 Filtered to Tier S-A: {len(df_output)} leads")
        else:
            df_output = df.copy()
            logger.info(f"📊 Exporting all tiers: {len(df_output)} leads")

        # Prepare output columns (compatible with CRM bot)
        output_df = self._prepare_output(df_output)

        # Save to CSV
        try:
            output_df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"✅ Saved to: {output_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save CSV: {e}")
            raise

        # === SUMMARY ===
        elapsed = time.time() - start_time
        logger.info("")
        logger.info("=== PIPELINE COMPLETE ===")
        logger.info(f"⏱️  Processing time: {elapsed:.2f}s")
        logger.info(f"📊 Output rows: {len(output_df)}")
        logger.info(f"🎯 Ready for CRM import!")
        logger.info("")

        return output_df

    def _prepare_output(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare output DataFrame for CRM bot.

        Required columns:
        - Email, Imie, Nazwisko, Telefon, TargetTier, TotalScore

        Optional columns:
        - LeadDescription, SniperHook, TaxWeapon, GothamInsight

        Args:
            df: Processed DataFrame

        Returns:
            DataFrame with CRM-compatible columns
        """
        output_data = {}

        # Map columns to CRM format
        column_mapping = {
            'Imie': 'first_name_clean',
            'Nazwisko': 'last_name_clean',
            'Email': 'email_clean',
            'Telefon': 'telefon_clean',
            'TargetTier': 'target_tier',
            'TotalScore': 'total_score',
            'LeadDescription': 'lead_description',
            'SniperHook': 'sniper_hook',
            'TaxWeapon': 'tax_weapon',
        }

        for output_col, source_col in column_mapping.items():
            if source_col in df.columns:
                output_data[output_col] = df[source_col]
            else:
                output_data[output_col] = ""

        # Gotham Insight (combine multiple fields)
        if 'wealth_tier' in df.columns and 'charger_distance_km' in df.columns:
            gotham_insight = df.apply(
                lambda row: f"Wealth: {row.get('wealth_tier', 'N/A')}, "
                            f"Charger: {row.get('charger_distance_km', 0):.1f}km, "
                            f"Tax benefit: {row.get('tax_benefit_annual', 0):,.0f} PLN/rok",
                axis=1
            )
            output_data['GothamInsight'] = gotham_insight
        else:
            output_data['GothamInsight'] = ""

        return pd.DataFrame(output_data)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Asset Sniper - Data Refinery for B2B Tesla Leads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input leads.csv --output enriched.csv
  %(prog)s --input leads.csv --output enriched.csv --all-tiers
  %(prog)s --input leads.csv --output enriched.csv --no-phone-required
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input CSV file path'
    )

    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output CSV file path'
    )

    parser.add_argument(
        '--all-tiers',
        action='store_true',
        help='Export all tiers (default: only S-A)'
    )

    parser.add_argument(
        '--no-phone-required',
        action='store_true',
        help='Do not require phone number'
    )

    parser.add_argument(
        '--require-email',
        action='store_true',
        help='Require email address'
    )

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input).exists():
        logger.error(f"❌ Input file not found: {args.input}")
        return 1

    # Run pipeline
    try:
        sniper = AssetSniper()
        sniper.process(
            input_path=args.input,
            output_path=args.output,
            require_phone=not args.no_phone_required,
            require_email=args.require_email,
            all_tiers=args.all_tiers
        )
        return 0
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
