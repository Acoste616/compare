# ASSET SNIPER v1.0

**Rafineria leadów B2B** inspirowana architekturą Palantir Foundry.

Przekształca surowe dane z CEIDG w precyzyjne cele sprzedażowe dla branży Tesla EV.

---

## 🎯 North Star Metric

**Maksymalizacja "Propensity to Close" przy minimalnym nakładzie czasu handlowca.**

---

## ⚡ Quick Start

### Instalacja

```bash
pip install pandas
```

### Podstawowe użycie (CLI)

```bash
python -m asset_sniper.main --input leads.csv --output enriched.csv
```

### Programmatic API

```python
from asset_sniper import AssetSniper

sniper = AssetSniper()
df_enriched = sniper.process('input.csv', 'output.csv')

# Pobierz tylko Tier S (VIP leads)
tier_s = df_enriched[df_enriched['TargetTier'] == 'S']
print(f"Tier S: {len(tier_s)} leadów")
```

---

## 📊 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ASSET SNIPER                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐             │
│  │  INPUT   │   │ REFINERY │   │  GOTHAM  │             │
│  │  (CSV)   │──▶│   CORE   │──▶│  ENGINE  │             │
│  └──────────┘   └──────────┘   └──────────┘             │
│                                      │                   │
│                                      ▼                   │
│                              ┌──────────┐                │
│                              │ SCORING  │                │
│                              │  MATRIX  │                │
│                              └──────────┘                │
│                                      │                   │
│                                      ▼                   │
│                              ┌──────────┐                │
│                              │BIGDECODER│                │
│                              │   LITE   │                │
│                              └──────────┘                │
│                                      │                   │
│                                      ▼                   │
│                              ┌──────────┐                │
│                              │  OUTPUT  │                │
│                              │   CSV    │                │
│                              └──────────┘                │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Modules

### 1. **Lead Refinery** (`lead_refinery.py`)
Czyszczenie i walidacja danych wejściowych.

- ✅ Walidacja NIP (checksum)
- ✅ Normalizacja telefonów (48XXXXXXXXX)
- ✅ Walidacja email
- ✅ Czyszczenie kodów pocztowych (XX-XXX)
- ✅ Parsowanie dat

### 2. **Gotham Engine** (`gotham_engine.py`)
Warstwy inteligencji rynkowej.

**Layer 1: Wealth Proxy**
- Kod pocztowy → zamożność regionu (1-10)
- Premium/High/Medium/Standard/Low tiers

**Layer 2: Charger Infrastructure**
- Dystans do najbliższej ładowarki EV
- Statyczna baza (Tesla Supercharger, IONITY, Orlen, Greenway)
- TODO: Integracja OpenChargeMap API

**Layer 3: Tax Engine**
- Korzyści podatkowe EV vs ICE
- EV: 225k PLN limit amortyzacji
- ICE: 150k PLN limit
- Oszczędność: 14 250 - 24 000 PLN/rok

**Layer 4: Leasing Cycle**
- Wiek firmy → cykl odnowienia leasingu
- 3-6 lat = prime window (95% propensity)

### 3. **Scoring Matrix** (`scoring_matrix.py`)
Klasyfikacja Tier S-E (0-100 punktów).

**Scoring Weights:**
- PKD Tier: 30 pts (S-tier industries)
- Wealth Proxy: 25 pts (region wealth)
- Company Age: 20 pts (leasing cycle)
- Charger Proximity: 15 pts (distance)
- Contact Quality: 10 pts (phone/email/www)

**Tier Thresholds:**
- **S (85-100):** NATYCHMIAST - Telefon w 24h
- **AAA (75-84):** DZIŚ - Kontakt tego dnia
- **AA (65-74):** TEN TYDZIEŃ
- **A (50-64):** AUTOMAT - Sekwencja automatyczna
- **B (35-49):** NISKI - Raz w miesiącu
- **C-E (0-34):** ARCHIWUM - Ignoruj

### 4. **BigDecoder Lite** (`bigdecoder_lite.py`)
Generator spersonalizowanych komunikatów.

**Generuje:**
- **SniperHook:** Personalized cold call opening
- **TaxWeapon:** Konkretny argument podatkowy z liczbami
- **LeadDescription:** Krótki opis dla handlowca

**Przykład:**
```
Hook: "Dzień dobry Panie Janie! Tesla to nie tylko prestiż -
       to konkretne oszczędności podatkowe. W przypadku Pana
       firmy to 24 000 PLN rocznie. A ładowarka 2.5km od Katowic."

Tax Weapon: "OSZCZĘDNOŚĆ PODATKOWA: do 24 000 PLN/rok (32% stawka) |
             EV: pełna amortyzacja do 225 000 PLN |
             Spalinowe: tylko do 150 000 PLN |
             Dotacja NaszEauto: 27 000 PLN"

Description: "Prawnik z Katowice, ładowarka 2.5km, firma 5 lat (cykl wymiany),
              lokalizacja premium"
```

---

## 🔌 API Integrations (Opcjonalne)

### CEPiK Client (`integrations/cepik_client.py`)
```python
from asset_sniper.integrations import CepikClient

client = CepikClient()
stats = client.get_ev_stats_by_region("ŚLĄSKIE")
awareness_score = client.get_ev_awareness_score("40-001")
```

### KRS Client (`integrations/krs_client.py`)
```python
from asset_sniper.integrations import KrsClient

client = KrsClient()
company_info = client.get_company_info("0000123456")
# Returns: capital, registration_date, legal_form
```

### OpenChargeMap Client (`integrations/opencharge_client.py`)
```python
from asset_sniper.integrations import OpenChargeClient

client = OpenChargeClient(api_key="YOUR_API_KEY")
chargers = client.get_chargers_near(lat=50.2649, lon=19.0238, radius_km=20)
nearest = client.get_nearest_fast_charger(lat=50.2649, lon=19.0238)
```

---

## 📤 Output Format (CRM-Compatible)

Kolumny **WYMAGANE** dla bota CRM:

| Kolumna | Typ | Opis |
|---------|-----|------|
| Imie | string | Imię (oczyszczone) |
| Nazwisko | string | Nazwisko |
| Email | string | Email (zwalidowany, lowercase) |
| Telefon | string | Telefon (48XXXXXXXXX) |
| TargetTier | string | Tier (S/AAA/AA/A/B/C/D/E) |
| TotalScore | int | Score 0-100 |

Kolumny **DODATKOWE** (dla Tier S-A):

| Kolumna | Typ | Opis |
|---------|-----|------|
| LeadDescription | string | Krótki opis leada |
| SniperHook | string | Spersonalizowany hook |
| TaxWeapon | string | Argument podatkowy |
| GothamInsight | string | Podsumowanie Gotham layers |

---

## 🚀 Advanced Usage

### Batch Processing (100k+ records)

```python
from asset_sniper.utils import BatchProcessor

processor = BatchProcessor(chunk_size=10000)

def process_chunk(df):
    sniper = AssetSniper()
    return sniper.process_dataframe(df)  # Custom method

stats = processor.process_large_csv(
    'huge_file.csv',
    'output.csv',
    processor_func=process_chunk
)

print(f"Processed {stats['processed_rows']} rows in {stats['chunks_processed']} chunks")
```

### BigDecoder Full Integration

```python
from asset_sniper.bigdecoder_full import BigDecoderIntegration
# Assuming you have UltraBigDecoder instance
from my_ai_system import UltraBigDecoder

bigdecoder = UltraBigDecoder()
integration = BigDecoderIntegration(bigdecoder_instance=bigdecoder)

result = integration.analyze_lead({
    'nazwa_firmy': 'Kancelaria Kowalski',
    'pkd': '6910Z',
    'imie': 'Jan',
    'lokalizacja': 'Katowice',
    'wiek_firmy': 5,
    'wealth_tier': 'PREMIUM'
})

print(result['personalized_hook'])
print(result['cognitive_profile'])
```

---

## 🧪 Testing

```bash
# Run all tests
python -m asset_sniper.tests.test_pipeline

# Run with pytest (if installed)
pytest asset_sniper/tests/
```

---

## 📋 CLI Options

```bash
python -m asset_sniper.main \
  --input leads.csv \
  --output enriched.csv \
  [OPTIONS]

Options:
  --all-tiers              Export all tiers (default: only S-A)
  --no-phone-required      Do not filter out leads without phone
  --require-email          Require email address
  -h, --help              Show help message
```

---

## 📊 Example Results

```
=== ASSET SNIPER v1.0 ===
Data Refinery for B2B Tesla Leads

📂 Input file: leads.csv
📂 Output file: enriched.csv

=== STAGE 1: Loading CSV ===
✅ Loaded 10000 rows

=== STAGE 2: Lead Refinery (Data Cleaning) ===
[REFINERY] Refining 10000 rows...
[REFINERY] Filtered 234 rows without valid phone
✅ Refined: 9766 rows

=== STAGE 3: Gotham Engine (Market Intelligence) ===
[GOTHAM] Processing 9766 rows...
✅ Enriched with Gotham layers

=== STAGE 4: Scoring Matrix (Tier Classification) ===
[SCORING] Scoring 9766 leads...
[SCORING] Tier distribution:
  S: 124 (1.3%)
  AAA: 287 (2.9%)
  AA: 512 (5.2%)
  A: 1234 (12.6%)
  B: 2456 (25.1%)
  C-E: 5153 (52.8%)
✅ Scored and tiered

=== STAGE 5: BigDecoder Lite (Message Generation) ===
[BIGDECODER] Generating messages for 2157 Tier S-A leads
✅ Messages generated

=== STAGE 6: Export to CSV ===
📊 Filtered to Tier S-A: 2157 leads
✅ Saved to: enriched.csv

=== PIPELINE COMPLETE ===
⏱️  Processing time: 12.34s
📊 Output rows: 2157
🎯 Ready for CRM import!
```

---

## 🔐 Security & GDPR

1. **GDPR Compliance:** Nie przechowuj danych dłużej niż potrzeba
2. **API Keys:** Przechowuj w zmiennych środowiskowych (`.env`)
3. **Rate Limiting:** Respektuj limity API (CEPiK, KRS, OpenChargeMap)
4. **No Logging of PII:** System nie loguje NIP, telefonów, emaili

---

## 📚 Documentation

Pełna specyfikacja: Zobacz `BIBLE.md` w głównym katalogu projektu.

---

## 🤝 Contributing

1. Fork repo
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

Copyright © 2026 BigDInc Team. All rights reserved.

---

## 🎉 Success Metrics

System działa poprawnie gdy:

1. ✅ Przetwarza 100k+ rekordów w <10 minut
2. ✅ Generuje Tier S-A dla ~10-15% leadów
3. ✅ Każdy Tier S ma kompletny SniperHook i TaxWeapon
4. ✅ Format wyjściowy jest kompatybilny z botem CRM
5. ✅ Zero błędów przy różnych formatach CSV wejściowego

---

**Wersja:** 1.0.0
**Data:** 2026-01-07
**Autor:** BigDInc Team

---

*"Rafineria leadów, która zamienia surowy węgiel w diamenty."*
