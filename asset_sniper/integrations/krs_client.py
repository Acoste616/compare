"""
KRS API Client (api-krs.ms.gov.pl)

Endpoint:
- GET /api/krs/OdpisAktualny/{krs}?rejestr=P&format=json

Purpose: Get company data (capital, registration date, legal form) for Sp. z o.o.

NOTE: Works only for companies with KRS number (Sp. z o.o., S.A., etc.)
      Does NOT work for JDG (Jednoosobowa Działalność Gospodarcza)

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class KrsClient:
    """
    Client for KRS (Krajowy Rejestr Sądowy) API.

    Use case: Enrich data for companies (not JDG):
    - Capital (kapitał zakładowy) -> proxy for company size
    - Registration date
    - Legal form verification
    """

    BASE_URL = "https://api-krs.ms.gov.pl"
    TIMEOUT = 30  # seconds

    def __init__(self):
        """Initialize KRS client."""
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AssetSniper/1.0'})

    def get_company_info(self, krs_number: str) -> Optional[Dict]:
        """
        Fetch company information from KRS.

        Args:
            krs_number: 10-digit KRS number (e.g., "0000123456")

        Returns:
            Dictionary with company data:
            {
                "krs": str,
                "name": str,
                "legal_form": str,
                "capital": float,  # in PLN
                "registration_date": str,  # YYYY-MM-DD
                "nip": str
            }

        Returns None if company not found or API error.
        """
        # Normalize KRS number (10 digits with leading zeros)
        krs_clean = str(krs_number).zfill(10)

        # Build URL
        endpoint = f"/api/krs/OdpisAktualny/{krs_clean}"
        params = {"rejestr": "P", "format": "json"}
        url = f"{self.BASE_URL}{endpoint}"

        logger.info(f"[KRS] Fetching data for KRS {krs_clean}...")

        try:
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()

            # Extract relevant fields (API structure may vary)
            # This is a simplified example - adapt to actual API response
            result = {
                "krs": krs_clean,
                "name": data.get("nazwa", ""),
                "legal_form": data.get("forma_prawna", ""),
                "capital": self.extract_capital(data),
                "registration_date": data.get("data_rejestracji", ""),
                "nip": data.get("nip", ""),
            }

            logger.info(f"[KRS] ✓ {result['name']} | Capital: {result['capital']:,.0f} PLN")
            return result

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"[KRS] Company not found: KRS {krs_clean}")
            else:
                logger.error(f"[KRS] HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"[KRS] Error: {e}")
            return None

    @staticmethod
    def extract_capital(krs_data: Dict) -> float:
        """
        Extract company capital from KRS data.

        Args:
            krs_data: Raw KRS API response

        Returns:
            Capital in PLN (0.0 if not found)
        """
        try:
            # API may return capital in various formats
            # Example: "100000,00 PLN" or {"amount": 100000, "currency": "PLN"}

            capital_field = krs_data.get("kapital_zakladowy", "")

            if isinstance(capital_field, str):
                # Parse string: "100000,00 PLN"
                capital_str = capital_field.replace(" PLN", "").replace(",", ".").strip()
                return float(capital_str)
            elif isinstance(capital_field, dict):
                # Parse dict: {"amount": 100000, "currency": "PLN"}
                return float(capital_field.get("amount", 0))
            else:
                return 0.0

        except Exception as e:
            logger.debug(f"[KRS] Could not parse capital: {e}")
            return 0.0


# === CLI TEST ===

if __name__ == "__main__":
    print("=== KRS Client Test ===\n")

    client = KrsClient()

    # Test with example KRS number (replace with real one for actual test)
    test_krs = "0000123456"

    company_info = client.get_company_info(test_krs)

    if company_info:
        print(f"Company Info:")
        print(f"  Name: {company_info['name']}")
        print(f"  Legal Form: {company_info['legal_form']}")
        print(f"  Capital: {company_info['capital']:,.0f} PLN")
        print(f"  Registration: {company_info['registration_date']}")
        print(f"  NIP: {company_info['nip']}")
    else:
        print(f"Company not found or API error")

    print()
    print("✅ KRS Client Test Complete!")
