"""
OpenChargeMap API Client (api.openchargemap.io)

Endpoint:
- GET /v3/poi/?output=json&countrycode=PL&latitude=X&longitude=Y&distance=50

Purpose: Dynamic EV charger infrastructure data (replaces static CHARGER_LOCATIONS)

API Key: Optional (higher rate limits with key, store in OPENCHARGE_API_KEY env var)

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import requests
import os
from typing import Dict, List, Optional, Tuple
import logging
import math

logger = logging.getLogger(__name__)


class OpenChargeClient:
    """
    Client for OpenChargeMap API.

    Use case: Get real-time EV charger locations for proximity scoring.
    Replaces static CHARGER_LOCATIONS with dynamic data.
    """

    BASE_URL = "https://api.openchargemap.io/v3"
    TIMEOUT = 30  # seconds
    DEFAULT_RADIUS_KM = 50  # Search radius in km

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenChargeMap client.

        Args:
            api_key: Optional API key (get from https://openchargemap.org)
                    If not provided, checks OPENCHARGE_API_KEY env var
        """
        self.api_key = api_key or os.getenv("OPENCHARGE_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AssetSniper/1.0'})

    def get_chargers_near(
        self,
        lat: float,
        lon: float,
        radius_km: int = 50,
        min_power_kw: int = 50
    ) -> List[Dict]:
        """
        Get EV chargers near coordinates.

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in km (max 500)
            min_power_kw: Minimum charger power in kW (50+ for fast charging)

        Returns:
            List of chargers:
            [
                {
                    "id": int,
                    "name": str,
                    "lat": float,
                    "lon": float,
                    "distance_km": float,
                    "power_kw": int,
                    "operator": str,
                    "address": str
                },
                ...
            ]
        """
        endpoint = "/poi/"
        url = f"{self.BASE_URL}{endpoint}"

        params = {
            "output": "json",
            "countrycode": "PL",
            "latitude": lat,
            "longitude": lon,
            "distance": min(radius_km, 500),  # API max: 500km
            "maxresults": 100,
            "compact": "true",
            "verbose": "false",
        }

        # Add API key if available
        if self.api_key:
            params["key"] = self.api_key

        logger.info(f"[OpenCharge] Searching chargers near ({lat}, {lon}) radius={radius_km}km...")

        try:
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()

            # Parse chargers
            chargers = []
            for poi in data:
                # Extract data (structure may vary)
                charger_lat = poi.get("AddressInfo", {}).get("Latitude")
                charger_lon = poi.get("AddressInfo", {}).get("Longitude")

                if not charger_lat or not charger_lon:
                    continue

                # Calculate distance
                distance = self._haversine_distance(lat, lon, charger_lat, charger_lon)

                # Get power (from first connection if available)
                connections = poi.get("Connections", [])
                power_kw = 0
                if connections:
                    power_kw = connections[0].get("PowerKW", 0) or 0

                # Filter by minimum power
                if power_kw < min_power_kw:
                    continue

                charger = {
                    "id": poi.get("ID"),
                    "name": poi.get("AddressInfo", {}).get("Title", "Unknown"),
                    "lat": charger_lat,
                    "lon": charger_lon,
                    "distance_km": round(distance, 1),
                    "power_kw": int(power_kw),
                    "operator": poi.get("OperatorInfo", {}).get("Title", "Unknown"),
                    "address": poi.get("AddressInfo", {}).get("AddressLine1", ""),
                }

                chargers.append(charger)

            # Sort by distance
            chargers.sort(key=lambda x: x["distance_km"])

            logger.info(f"[OpenCharge] ✓ Found {len(chargers)} chargers (>{min_power_kw}kW)")
            return chargers

        except requests.HTTPError as e:
            logger.error(f"[OpenCharge] HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"[OpenCharge] Error: {e}")
            return []

    def get_nearest_fast_charger(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get nearest fast charger (>50kW).

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Nearest charger dict or None if not found
        """
        chargers = self.get_chargers_near(lat, lon, radius_km=50, min_power_kw=50)

        if chargers:
            return chargers[0]  # Already sorted by distance
        else:
            return None

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c


# === CLI TEST ===

if __name__ == "__main__":
    print("=== OpenChargeMap Client Test ===\n")

    client = OpenChargeClient()

    # Test coordinates: Katowice centrum
    test_lat = 50.2649
    test_lon = 19.0238

    print(f"Searching for fast chargers near Katowice ({test_lat}, {test_lon})...\n")

    # Get chargers
    chargers = client.get_chargers_near(test_lat, test_lon, radius_km=20, min_power_kw=50)

    if chargers:
        print(f"Found {len(chargers)} fast chargers:\n")
        for i, charger in enumerate(chargers[:5], 1):
            print(f"{i}. {charger['name']}")
            print(f"   Operator: {charger['operator']}")
            print(f"   Power: {charger['power_kw']} kW")
            print(f"   Distance: {charger['distance_km']} km")
            print()
    else:
        print("No chargers found (or API error)")

    print("✅ OpenChargeMap Client Test Complete!")
