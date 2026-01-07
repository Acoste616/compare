"""
End-to-End Pipeline Tests for Asset Sniper

Tests complete processing pipeline from CSV input to enriched output.

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import pytest
import pandas as pd
import tempfile
import os
from datetime import date

# Import modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from asset_sniper.lead_refinery import LeadRefinery
from asset_sniper.gotham_engine import GothamEngine
from asset_sniper.scoring_matrix import ScoringMatrix
from asset_sniper.bigdecoder_lite import BigDecoderLite
from asset_sniper.main import AssetSniper


# === FIXTURES ===

@pytest.fixture
def sample_data():
    """Sample CEIDG data for testing."""
    return pd.DataFrame({
        'Nip': ['5272829917', '5261040828'],
        'Nazwisko': ['Kowalski', 'Nowak'],
        'Imie': ['Jan', 'Anna'],
        'Telefon': ['500100200', '501200300'],
        'Email': ['jan@kancelaria.pl', 'anna@firma.pl'],
        'KodPocztowy': ['40-001', '44-100'],
        'Miejscowosc': ['Katowice', 'Gliwice'],
        'GlownyKodPkd': ['6910Z', '6201Z'],
        'StatusDzialalnoci': ['Aktywny', 'Aktywny'],
        'DataRozpoczeciaDzialalnoci': ['01/01/2019', '15/06/2021'],
        'FormaPrawna': ['SPÓŁKA Z O.O.', 'JEDNOOSOBOWA DZIAŁALNOŚĆ'],
    })


# === TESTS ===

def test_refinery_cleans_data(sample_data):
    """Test: Lead Refinery cleans and validates data."""
    refinery = LeadRefinery()
    result = refinery.refine(sample_data, require_phone=False)

    # Check cleaned columns exist
    assert 'telefon_clean' in result.columns
    assert 'email_clean' in result.columns
    assert 'nip_clean' in result.columns
    assert 'kod_pocztowy_clean' in result.columns

    # Check phone normalization
    assert result['telefon_clean'].iloc[0] == '48500100200'

    # Check postal code format
    assert result['kod_pocztowy_clean'].iloc[0] == '40-001'

    print("✓ Lead Refinery test passed")


def test_gotham_adds_layers(sample_data):
    """Test: Gotham Engine adds market intelligence layers."""
    refinery = LeadRefinery()
    df = refinery.refine(sample_data, require_phone=False)

    gotham = GothamEngine()
    result = gotham.process(df)

    # Check Gotham columns
    assert 'wealth_score' in result.columns
    assert 'wealth_tier' in result.columns
    assert 'charger_distance_km' in result.columns
    assert 'tax_benefit_annual' in result.columns
    assert 'leasing_cycle' in result.columns

    # Check wealth scoring
    assert result['wealth_tier'].iloc[0] in ['PREMIUM', 'HIGH', 'MEDIUM', 'STANDARD', 'LOW']

    print("✓ Gotham Engine test passed")


def test_scoring_assigns_tiers(sample_data):
    """Test: Scoring Matrix assigns tiers correctly."""
    refinery = LeadRefinery()
    df = refinery.refine(sample_data, require_phone=False)

    gotham = GothamEngine()
    df = gotham.process(df)

    scoring = ScoringMatrix()
    result = scoring.score_all(df)

    # Check scoring columns
    assert 'total_score' in result.columns
    assert 'target_tier' in result.columns
    assert 'priority' in result.columns
    assert 'next_action' in result.columns

    # Check tier values
    valid_tiers = ['S', 'AAA', 'AA', 'A', 'B', 'C', 'D', 'E']
    assert all(result['target_tier'].isin(valid_tiers))

    # Check score range
    assert all(result['total_score'] >= 0)
    assert all(result['total_score'] <= 100)

    print("✓ Scoring Matrix test passed")


def test_bigdecoder_generates_messages(sample_data):
    """Test: BigDecoder Lite generates personalized messages."""
    refinery = LeadRefinery()
    df = refinery.refine(sample_data, require_phone=False)

    gotham = GothamEngine()
    df = gotham.process(df)

    scoring = ScoringMatrix()
    df = scoring.score_all(df)

    bigdecoder = BigDecoderLite()
    result = bigdecoder.enrich_messages(df)

    # Check message columns
    assert 'sniper_hook' in result.columns
    assert 'tax_weapon' in result.columns
    assert 'lead_description' in result.columns

    # For Tier S-A leads, messages should be generated
    tier_s_a = result[result['target_tier'].isin(['S', 'AAA', 'AA', 'A'])]
    if len(tier_s_a) > 0:
        # At least some should have hooks
        assert any(tier_s_a['sniper_hook'] != "")

    print("✓ BigDecoder Lite test passed")


def test_full_pipeline():
    """Test: Complete Asset Sniper pipeline end-to-end."""
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Nip,Nazwisko,Imie,Telefon,Email,KodPocztowy,Miejscowosc,GlownyKodPkd,StatusDzialalnoci,DataRozpoczeciaDzialalnoci,FormaPrawna\n")
        f.write("5272829917,Kowalski,Jan,500100200,jan@firma.pl,40-001,Katowice,6910Z,Aktywny,01/01/2019,SPÓŁKA Z O.O.\n")
        f.write("5261040828,Nowak,Anna,501200300,anna@it.pl,44-100,Gliwice,6201Z,Aktywny,15/06/2021,JEDNOOSOBOWA DZIAŁALNOŚĆ\n")
        input_path = f.name

    output_path = input_path.replace('.csv', '_output.csv')

    try:
        # Run pipeline
        sniper = AssetSniper()
        result = sniper.process(input_path, output_path, all_tiers=True)

        # Check result
        assert len(result) >= 0
        assert os.path.exists(output_path)

        # Check output format (CRM-compatible)
        df_output = pd.read_csv(output_path)
        required_cols = ['Email', 'Imie', 'Nazwisko', 'Telefon', 'TargetTier', 'TotalScore']
        for col in required_cols:
            assert col in df_output.columns, f"Missing required column: {col}"

        print("✓ Full pipeline test passed")
        print(f"  Output rows: {len(df_output)}")
        print(f"  Tier distribution: {df_output['TargetTier'].value_counts().to_dict()}")

    finally:
        # Cleanup
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


# === RUN TESTS ===

if __name__ == "__main__":
    print("=== Asset Sniper Pipeline Tests ===\n")

    # Create sample data
    sample = pd.DataFrame({
        'Nip': ['5272829917', '5261040828'],
        'Nazwisko': ['Kowalski', 'Nowak'],
        'Imie': ['Jan', 'Anna'],
        'Telefon': ['500100200', '501200300'],
        'Email': ['jan@kancelaria.pl', 'anna@firma.pl'],
        'KodPocztowy': ['40-001', '44-100'],
        'Miejscowosc': ['Katowice', 'Gliwice'],
        'GlownyKodPkd': ['6910Z', '6201Z'],
        'StatusDzialalnoci': ['Aktywny', 'Aktywny'],
        'DataRozpoczeciaDzialalnoci': ['01/01/2019', '15/06/2021'],
        'FormaPrawna': ['SPÓŁKA Z O.O.', 'JEDNOOSOBOWA DZIAŁALNOŚĆ'],
    })

    # Run tests
    print("Test 1: Lead Refinery")
    test_refinery_cleans_data(sample)
    print()

    print("Test 2: Gotham Engine")
    test_gotham_adds_layers(sample)
    print()

    print("Test 3: Scoring Matrix")
    test_scoring_assigns_tiers(sample)
    print()

    print("Test 4: BigDecoder Lite")
    test_bigdecoder_generates_messages(sample)
    print()

    print("Test 5: Full Pipeline")
    test_full_pipeline()
    print()

    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
