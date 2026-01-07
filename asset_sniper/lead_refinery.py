"""
ASSET SNIPER - Lead Refinery Module
Czyszczenie i normalizacja danych CSV z CEIDG

Functions:
- Walidacja i czyszczenie NIP
- Normalizacja telefonów (48XXXXXXXXX)
- Walidacja email
- Czyszczenie kodów pocztowych
- Parsowanie dat

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import re
import pandas as pd
from datetime import datetime, date
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LeadRefinery:
    """
    Data cleaning and normalization for CEIDG CSV files.

    Level 0: Clean dirty data
    - NIP validation (10 digits + checksum)
    - Phone normalization (48XXXXXXXXX format)
    - Email validation
    - Postal code cleaning (XX-XXX format)
    - Date parsing from multiple formats
    """

    # === NIP VALIDATION ===

    @staticmethod
    def clean_nip(nip: Any) -> str:
        """
        Clean and validate Polish NIP number.

        Validation:
        - Must be exactly 10 digits
        - Must pass checksum validation

        Args:
            nip: Raw NIP value from CSV

        Returns:
            Validated NIP string or empty string if invalid
        """
        if pd.isna(nip):
            return ""

        # Remove all non-digits
        nip_str = re.sub(r'\D', '', str(nip))

        # Must be exactly 10 digits
        if len(nip_str) != 10:
            return ""

        # Checksum validation
        weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(nip_str[i]) * weights[i] for i in range(9)) % 11

        if checksum != int(nip_str[9]):
            logger.debug(f"Invalid NIP checksum: {nip_str}")
            return ""

        return nip_str

    # === PHONE NORMALIZATION ===

    @staticmethod
    def clean_phone(phone: Any) -> str:
        """
        Clean and normalize Polish phone number.

        Output format: 48XXXXXXXXX (international format without +)

        Args:
            phone: Raw phone value from CSV

        Returns:
            Normalized phone string or empty string if invalid
        """
        if pd.isna(phone):
            return ""

        # Remove all non-digits
        phone_str = re.sub(r'\D', '', str(phone))

        # Handle different input formats
        if phone_str.startswith('48') and len(phone_str) == 11:
            # Already in 48XXXXXXXXX format
            return phone_str
        elif phone_str.startswith('048') and len(phone_str) == 12:
            # Remove leading 0
            return phone_str[1:]
        elif len(phone_str) == 9:
            # Add country code
            return f"48{phone_str}"
        else:
            logger.debug(f"Invalid phone format: {phone_str}")
            return ""

    # === EMAIL VALIDATION ===

    @staticmethod
    def clean_email(email: Any) -> str:
        """
        Clean and validate email address.

        Basic validation:
        - Contains @
        - Has domain with TLD
        - Lowercase normalization

        Args:
            email: Raw email value from CSV

        Returns:
            Validated email string (lowercase) or empty string if invalid
        """
        if pd.isna(email):
            return ""

        email_str = str(email).strip().lower()

        # Basic regex validation
        if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email_str):
            return email_str

        return ""

    # === POSTAL CODE CLEANING ===

    @staticmethod
    def clean_zip_code(zip_code: Any) -> str:
        """
        Clean Polish postal code.

        Output format: XX-XXX

        Args:
            zip_code: Raw postal code value from CSV

        Returns:
            Formatted postal code or empty string if invalid
        """
        if pd.isna(zip_code):
            return ""

        # Remove all non-digits
        zip_str = re.sub(r'\D', '', str(zip_code))

        # Must be exactly 5 digits
        if len(zip_str) != 5:
            return ""

        # Format as XX-XXX
        return f"{zip_str[:2]}-{zip_str[2:]}"

    # === DATE PARSING ===

    @staticmethod
    def parse_date(date_val: Any) -> Optional[date]:
        """
        Parse date from various formats.

        Supported formats:
        - YYYY-MM-DD
        - DD-MM-YYYY
        - DD.MM.YYYY
        - YYYY/MM/DD
        - DD/MM/YYYY

        Args:
            date_val: Raw date value from CSV

        Returns:
            Python date object or None if parsing fails
        """
        if pd.isna(date_val):
            return None

        date_str = str(date_val).strip()

        # Try different formats
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        logger.debug(f"Could not parse date: {date_str}")
        return None

    # === COMPATIBILITY ALIASES ===
    # These allow calling the methods with underscore prefix (backward compatibility)

    _clean_nip = clean_nip
    _clean_phone = clean_phone
    _clean_email = clean_email
    _clean_postal_code = clean_zip_code
    _parse_date = parse_date

    # === MAIN REFINE METHOD ===

    def refine(
        self,
        df: pd.DataFrame,
        require_phone: bool = True,
        require_email: bool = False
    ) -> pd.DataFrame:
        """
        Clean and normalize entire CSV DataFrame.

        Column mappings (flexible):
        - nip, NIP, Nip, numer_nip, tax_id -> nip_clean
        - phone, telefon, Telefon, tel -> telefon_clean
        - email, Email, e-mail -> email_clean
        - company_name, nazwa, Nazwa, NazwaSkrocona -> nazwa_clean
        - pkd, PKD, PkdGlowny -> pkd_clean
        - zip_code, KodPocztowy, postal_code -> kod_pocztowy_clean
        - city, miasto, Miejscowosc -> miasto_clean
        - start_date, DataRozpoczeciaDzialalnosci -> data_rozpoczecia

        Args:
            df: Input DataFrame from CSV
            require_phone: Drop rows without valid phone
            require_email: Drop rows without valid email

        Returns:
            Cleaned DataFrame with _clean columns
        """
        logger.info(f"[REFINERY] Refining {len(df)} rows...")

        df_clean = df.copy()

        # Column mapping definitions
        column_mappings = {
            'nip': ['nip', 'NIP', 'Nip', 'numer_nip', 'tax_id'],
            'phone': ['phone', 'telefon', 'Telefon', 'tel', 'phone_number'],
            'email': ['email', 'Email', 'e-mail', 'E-mail', 'mail'],
            'company_name': ['company_name', 'nazwa', 'Nazwa', 'firma', 'name', 'NazwaSkrocona', 'NazwaPodmiotu'],
            'legal_form': ['legal_form', 'forma_prawna', 'FormaPrawna', 'form'],
            'pkd': ['pkd', 'PKD', 'pkd_code', 'PkdGlowny', 'pkd_glowny', 'GlownyKodPkd'],
            'zip_code': ['zip_code', 'kod_pocztowy', 'KodPocztowy', 'postal_code', 'zip'],
            'city': ['city', 'miasto', 'Miasto', 'miejscowosc', 'Miejscowosc'],
            'voivodeship': ['voivodeship', 'wojewodztwo', 'Wojewodztwo', 'region'],
            'start_date': ['start_date', 'data_rozpoczecia', 'DataRozpoczeciaDzialalnosci', 'data_start'],
            'first_name': ['first_name', 'imie', 'Imie', 'imię'],
            'last_name': ['last_name', 'nazwisko', 'Nazwisko'],
            'status': ['status', 'StatusDzialalnoci', 'status_dzialalnosci'],
        }

        # Create case-insensitive column lookup
        df_columns_lower = {col.lower(): col for col in df_clean.columns}

        # Apply cleaning for each field type
        for target_col, possible_names in column_mappings.items():
            matched_col = None

            # Find matching column
            for name in possible_names:
                if name in df_clean.columns:
                    matched_col = name
                    break
                if name.lower() in df_columns_lower:
                    matched_col = df_columns_lower[name.lower()]
                    break

            if not matched_col:
                logger.warning(f"Column not found: {target_col}")
                continue

            # Apply appropriate cleaning function
            if target_col == 'nip':
                df_clean['nip_clean'] = df_clean[matched_col].apply(self.clean_nip)
            elif target_col == 'phone':
                df_clean['telefon_clean'] = df_clean[matched_col].apply(self.clean_phone)
            elif target_col == 'email':
                df_clean['email_clean'] = df_clean[matched_col].apply(self.clean_email)
            elif target_col == 'zip_code':
                df_clean['kod_pocztowy_clean'] = df_clean[matched_col].apply(self.clean_zip_code)
            elif target_col == 'start_date':
                df_clean['data_rozpoczecia'] = df_clean[matched_col].apply(self.parse_date)
            else:
                # Simple string cleaning (strip whitespace)
                df_clean[f'{target_col}_clean'] = df_clean[matched_col].astype(str).str.strip()

        # Filter out rows with missing required fields
        initial_count = len(df_clean)

        if require_phone and 'telefon_clean' in df_clean.columns:
            df_clean = df_clean[df_clean['telefon_clean'] != ""]
            logger.info(f"[REFINERY] Filtered {initial_count - len(df_clean)} rows without valid phone")

        if require_email and 'email_clean' in df_clean.columns:
            df_clean = df_clean[df_clean['email_clean'] != ""]
            logger.info(f"[REFINERY] Filtered {initial_count - len(df_clean)} rows without valid email")

        logger.info(f"[REFINERY] Refining complete. Output: {len(df_clean)} rows")

        return df_clean

    # Alias for compatibility with unified pipeline
    def process(
        self,
        df: pd.DataFrame,
        require_phone: bool = True,
        require_email: bool = False
    ) -> pd.DataFrame:
        """Alias for refine() method"""
        return self.refine(df, require_phone, require_email)


# === CLI TEST ===

if __name__ == "__main__":
    print("=== Lead Refinery Test ===\n")

    # Create test data
    test_data = {
        'NIP': ['5272829917', '123-456-78-90', 'invalid', '5261040828'],
        'Telefon': ['+48 500 100 200', '500100200', '48500100200', 'bad'],
        'Email': ['test@example.com', 'invalid', 'hello@firma.pl', ''],
        'Nazwa': ['Tech Solutions', 'Auto-Trans', 'StartupXYZ', 'Consulting'],
        'KodPocztowy': ['02677', '40-001', '90001', 'bad'],
        'DataRozpoczeciaDzialalnosci': ['2019-03-15', '15-08-2020', '01.01.2023', '2018/06/01']
    }

    df_test = pd.DataFrame(test_data)

    print("Input data:")
    print(df_test)
    print()

    # Test refinery
    refinery = LeadRefinery()
    df_result = refinery.refine(df_test, require_phone=False)

    print("Cleaned data:")
    clean_cols = [c for c in df_result.columns if 'clean' in c or 'data_' in c]
    print(df_result[clean_cols])
    print()

    print("✅ Lead Refinery Test Complete!")
