"""
CEPiK API Client (api.cepik.gov.pl)

Endpoints:
- GET /statystyki/pojazdy/{data-statystyki}/{wojewodztwo}
- GET /slowniki

Purpose: Regional EV awareness scoring based on registration statistics

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import requests
from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CepikClient:
    """
    Client for CEPiK (Centralna Ewidencja Pojazdów i Kierowców) API.

    Use case: Get EV registration statistics for regional awareness scoring.
    Higher EV adoption in region = higher market awareness = better lead quality.
    """

    BASE_URL = "https://api.cepik.gov.pl"
    TIMEOUT = 30  # seconds

    # Województwa codes (TERYT)
    WOJEWODZTWA = {
        "ŚLĄSKIE": "24",
        "MAZOWIECKIE": "14",
        "MAŁOPOLSKIE": "12",
        "POMORSKIE": "22",
        "WIELKOPOLSKIE": "30",
        "DOLNOŚLĄSKIE": "02",
        "ŁÓDZKIE": "10",
        "LUBELSKIE": "06",
        "KUJAWSKO-POMORSKIE": "04",
        "ZACHODNIOPOMORSKIE": "32",
        "PODKARPACKIE": "18",
        "WARMIŃSKO-MAZURSKIE": "28",
        "LUBUSKIE": "08",
        "ŚWIĘTOKRZYSKIE": "26",
        "PODLASKIE": "20",
        "OPOLSKIE": "16",
    }

    def __init__(self):
        """Initialize CEPiK client."""
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AssetSniper/1.0'})

    def get_ev_stats_by_region(self, wojewodztwo: str, date: Optional[str] = None) -> Dict:
        """
        Fetch EV registration statistics for województwo.

        Args:
            wojewodztwo: Voivodeship name (e.g., "ŚLĄSKIE")
            date: Statistics date in YYYY-MM-DD format (default: last month)

        Returns:
            Dictionary with statistics:
            {
                "total_evs": int,
                "total_vehicles": int,
                "ev_percentage": float,
                "date": str,
                "region": str
            }

        Raises:
            requests.HTTPError: If API request fails
        """
        # Get województwo code
        woj_code = self.WOJEWODZTWA.get(wojewodztwo.upper())
        if not woj_code:
            logger.warning(f"Unknown województwo: {wojewodztwo}, using ŚLĄSKIE")
            woj_code = "24"

        # Default date: last month
        if not date:
            last_month = datetime.now() - timedelta(days=30)
            date = last_month.strftime("%Y-%m-%d")

        # Build URL
        endpoint = f"/statystyki/pojazdy/{date}/{woj_code}"
        url = f"{self.BASE_URL}{endpoint}"

        logger.info(f"[CEPiK] Fetching stats for {wojewodztwo} on {date}...")

        try:
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()

            # Parse response (structure may vary - adapt as needed)
            # This is a simplified example
            total_evs = data.get('total_electric_vehicles', 0)
            total_vehicles = data.get('total_vehicles', 0)
            ev_percentage = (total_evs / total_vehicles * 100) if total_vehicles > 0 else 0

            result = {
                "total_evs": total_evs,
                "total_vehicles": total_vehicles,
                "ev_percentage": round(ev_percentage, 2),
                "date": date,
                "region": wojewodztwo,
            }

            logger.info(f"[CEPiK] ✓ {wojewodztwo}: {total_evs} EVs ({ev_percentage:.2f}%)")
            return result

        except requests.HTTPError as e:
            logger.error(f"[CEPiK] HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"[CEPiK] Error: {e}")
            raise

    def get_ev_awareness_score(self, kod_pocztowy: str) -> int:
        """
        Calculate EV awareness score for postal code (0-10).

        Logic:
        - Get region from postal code prefix
        - Fetch EV statistics
        - Score based on EV adoption rate

        Args:
            kod_pocztowy: Polish postal code (XX-XXX)

        Returns:
            Score 0-10 (10 = highest awareness)
        """
        # Extract województwo from postal code (simplified mapping)
        prefix = kod_pocztowy[:2] if kod_pocztowy else ""

        # Mapping: postal prefix -> województwo
        postal_to_woj = {
            "00": "MAZOWIECKIE",
            "01": "MAZOWIECKIE",
            "02": "MAZOWIECKIE",
            "03": "MAZOWIECKIE",
            "04": "MAZOWIECKIE",
            "30": "MAŁOPOLSKIE",
            "31": "MAŁOPOLSKIE",
            "32": "MAŁOPOLSKIE",
            "40": "ŚLĄSKIE",
            "41": "ŚLĄSKIE",
            "42": "ŚLĄSKIE",
            "43": "ŚLĄSKIE",
            "44": "ŚLĄSKIE",
            "50": "DOLNOŚLĄSKIE",
            "51": "DOLNOŚLĄSKIE",
            "60": "WIELKOPOLSKIE",
            "61": "WIELKOPOLSKIE",
            "80": "POMORSKIE",
            "81": "POMORSKIE",
            "82": "POMORSKIE",
            "90": "ŁÓDZKIE",
            "91": "ŁÓDZKIE",
        }

        wojewodztwo = postal_to_woj.get(prefix, "ŚLĄSKIE")

        try:
            stats = self.get_ev_stats_by_region(wojewodztwo)
            ev_pct = stats["ev_percentage"]

            # Score mapping
            if ev_pct > 5.0:
                return 10
            elif ev_pct > 3.0:
                return 8
            elif ev_pct > 2.0:
                return 6
            elif ev_pct > 1.0:
                return 4
            else:
                return 2

        except Exception as e:
            logger.warning(f"[CEPiK] Could not get awareness score: {e}")
            return 5  # Default neutral score


# === CLI TEST ===

if __name__ == "__main__":
    print("=== CEPiK Client Test ===\n")

    client = CepikClient()

    # Test 1: Get regional stats
    try:
        stats = client.get_ev_stats_by_region("ŚLĄSKIE")
        print(f"Regional stats: {stats}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()

    # Test 2: Get awareness score
    score = client.get_ev_awareness_score("40-001")
    print(f"EV Awareness Score for 40-001: {score}/10")
    print()

    print("✅ CEPiK Client Test Complete!")
