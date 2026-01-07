"""
MOCK CEPiK DATA FOR TESTING
This file contains mock data that was previously in backend/gotham_module.py

Use this for testing purposes ONLY. Production code should use real API data.

Author: Data Integration Specialist
Version: 1.0.0
"""

from backend.gotham_module import CEPiKData

# Mock data (2024 estimates based on real trends)
# USE FOR TESTING ONLY - Production uses real CEPiK API
# Confidence Score: 50 (estimated/mock data)
MOCK_CEPIK_DATA = {
    "ŚLĄSKIE": CEPiKData(
        region="ŚLĄSKIE",
        total_ev_registrations_2024=3_245,
        growth_rate_yoy=124.5,
        top_brand="Tesla Model 3",
        trend="ROSNĄCY",
        confidence_score=50
    ),
    "MAZOWIECKIE": CEPiKData(
        region="MAZOWIECKIE",
        total_ev_registrations_2024=8_127,
        growth_rate_yoy=156.3,
        top_brand="Tesla Model Y",
        trend="ROSNĄCY",
        confidence_score=50
    ),
    "MAŁOPOLSKIE": CEPiKData(
        region="MAŁOPOLSKIE",
        total_ev_registrations_2024=2_891,
        growth_rate_yoy=98.7,
        top_brand="Tesla Model 3",
        trend="ROSNĄCY",
        confidence_score=50
    ),
    "POMORSKIE": CEPiKData(
        region="POMORSKIE",
        total_ev_registrations_2024=2_134,
        growth_rate_yoy=87.2,
        top_brand="Volvo EX30",
        trend="STABILNY",
        confidence_score=50
    ),
    "WIELKOPOLSKIE": CEPiKData(
        region="WIELKOPOLSKIE",
        total_ev_registrations_2024=2_567,
        growth_rate_yoy=102.4,
        top_brand="Tesla Model 3",
        trend="ROSNĄCY",
        confidence_score=50
    ),
    "DOLNOŚLĄSKIE": CEPiKData(
        region="DOLNOŚLĄSKIE",
        total_ev_registrations_2024=2_456,
        growth_rate_yoy=91.8,
        top_brand="Tesla Model Y",
        trend="ROSNĄCY",
        confidence_score=50
    )
}
