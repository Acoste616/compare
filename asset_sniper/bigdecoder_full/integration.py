"""
BigDecoder Full Integration Module

Most (bridge) do pełnego systemu UltraBigDecoder.

UltraBigDecoder to istniejący system analizy psychologicznej klientów.
Ten moduł integruje go z Asset Sniper dla głębszej personalizacji.

ARCHITECTURE:
- Lite Mode (default): Template-based message generation
- Full Mode: AI-powered psychographic profiling via UltraBigDecoder

Based on: BIBLE v1.0
Author: BigDInc Team
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BigDecoderIntegration:
    """
    Integration bridge to full UltraBigDecoder system.

    Usage:
        # With UltraBigDecoder instance
        bigdecoder = SomeUltraBigDecoderClass()
        integration = BigDecoderIntegration(bigdecoder_instance=bigdecoder)
        result = integration.analyze_lead(lead_data)

        # Without (falls back to Lite mode)
        integration = BigDecoderIntegration()
        result = integration.analyze_lead(lead_data)
    """

    def __init__(self, bigdecoder_instance=None):
        """
        Initialize BigDecoder integration.

        Args:
            bigdecoder_instance: Instance of UltraBigDecoder or None
                                If None, uses Lite mode (templates)
        """
        self.bigdecoder = bigdecoder_instance
        self.use_full = bigdecoder_instance is not None

        if self.use_full:
            logger.info("[BIGDECODER] Full mode enabled - using AI analysis")
        else:
            logger.info("[BIGDECODER] Lite mode - using template-based generation")

    def analyze_lead(self, lead_data: Dict) -> Dict:
        """
        Analyze lead through BigDecoder.

        Args:
            lead_data: Dictionary with lead information:
            {
                'nazwa_firmy': str,
                'pkd': str,
                'imie': str,
                'nazwisko': str,
                'lokalizacja': str,
                'wiek_firmy': int,
                'wealth_tier': str
            }

        Returns:
            Analysis result:
            {
                'cognitive_profile': str,      # Typ osobowości
                'pain_points': list[str],      # Główne bolączki
                'motivators': list[str],       # Motywatory zakupowe
                'communication_style': str,    # Styl komunikacji
                'recommended_approach': str,   # Zalecane podejście
                'personalized_hook': str,      # Spersonalizowany hook
                'confidence_score': float      # Pewność analizy 0-1
            }
        """
        if self.use_full:
            return self._analyze_with_full_bigdecoder(lead_data)
        else:
            return self._analyze_lite(lead_data)

    def _analyze_with_full_bigdecoder(self, lead_data: Dict) -> Dict:
        """
        Use full BigDecoder for deep analysis.

        NOTE: This is a placeholder. Adapt to your actual UltraBigDecoder API.

        Args:
            lead_data: Lead information

        Returns:
            Analysis result from UltraBigDecoder
        """
        logger.info(f"[BIGDECODER] Analyzing {lead_data.get('nazwa_firmy', 'Unknown')} with AI...")

        try:
            # TODO: Adapt to actual UltraBigDecoder API
            # Example (pseudocode):
            # result = self.bigdecoder.analyze(
            #     company_name=lead_data['nazwa_firmy'],
            #     industry_code=lead_data['pkd'],
            #     owner_name=f"{lead_data['imie']} {lead_data['nazwisko']}",
            #     location=lead_data['lokalizacja'],
            #     company_age=lead_data['wiek_firmy'],
            #     wealth_tier=lead_data['wealth_tier']
            # )
            # return result

            # Placeholder response
            logger.warning("[BIGDECODER] Full BigDecoder not connected - using fallback")
            return self._analyze_lite(lead_data)

        except Exception as e:
            logger.error(f"[BIGDECODER] Error in full analysis: {e}")
            return self._analyze_lite(lead_data)

    def _analyze_lite(self, lead_data: Dict) -> Dict:
        """
        Fallback to simple analysis based on PKD code.

        Args:
            lead_data: Lead information

        Returns:
            Basic analysis result
        """
        from ..config import PKD_PROFILES

        pkd = lead_data.get('pkd', '')
        profile = PKD_PROFILES.get(pkd, PKD_PROFILES['DEFAULT'])

        # Basic profiling
        result = {
            'cognitive_profile': profile['name'],
            'pain_points': profile['pain_points'],
            'motivators': profile['motivators'],
            'communication_style': 'professional',
            'recommended_approach': profile['hook_angle'],
            'personalized_hook': self._generate_basic_hook(lead_data, profile),
            'confidence_score': 0.6  # Low confidence for Lite mode
        }

        logger.info(f"[BIGDECODER] Lite analysis: {result['cognitive_profile']}")
        return result

    def _generate_basic_hook(self, lead_data: Dict, profile: Dict) -> str:
        """
        Generate basic personalized hook.

        Args:
            lead_data: Lead information
            profile: PKD profile

        Returns:
            Basic hook string
        """
        imie = lead_data.get('imie', '')
        angle = profile.get('hook_angle', 'korzyści finansowe')

        greeting = f"Dzień dobry {'Panie/Pani ' + imie if imie else ''}! "
        hook = greeting + f"Chciałbym porozmawiać o {angle} związanych z przesiadką na Teslę."

        return hook


# === CLI TEST ===

if __name__ == "__main__":
    print("=== BigDecoder Integration Test ===\n")

    # Test data
    test_lead = {
        'nazwa_firmy': 'Kancelaria Prawna Kowalski',
        'pkd': '6910Z',
        'imie': 'Jan',
        'nazwisko': 'Kowalski',
        'lokalizacja': 'Katowice',
        'wiek_firmy': 5,
        'wealth_tier': 'PREMIUM'
    }

    # Test Lite mode
    integration = BigDecoderIntegration()
    result = integration.analyze_lead(test_lead)

    print("Analysis Result (Lite Mode):")
    print(f"  Profile: {result['cognitive_profile']}")
    print(f"  Communication: {result['communication_style']}")
    print(f"  Hook: {result['personalized_hook']}")
    print(f"  Confidence: {result['confidence_score']}")
    print()

    print("Pain Points:")
    for point in result['pain_points']:
        print(f"  - {point}")
    print()

    print("Motivators:")
    for mot in result['motivators']:
        print(f"  - {mot}")
    print()

    print("✅ BigDecoder Integration Test Complete!")
