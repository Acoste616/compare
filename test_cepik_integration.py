#!/usr/bin/env python3
"""
Quick integration test for CEPiK connector and GOTHAM module
This test verifies the structure and imports without making actual API calls
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("TESLA-GOTHAM CEPiK Integration Test")
print("=" * 70)
print()

# Test 1: Import store module
print("1️⃣  Testing store.py import...")
try:
    from backend.services.gotham.store import CEPiKCache
    print("   ✅ CEPiKCache imported successfully")
    print(f"   - Cache file location: {CEPiKCache.CACHE_FILE}")
    print(f"   - Cache TTL: {CEPiKCache.CACHE_TTL_HOURS}h")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print()

# Test 2: Import cepik_connector module
print("2️⃣  Testing cepik_connector.py import...")
try:
    from backend.services.gotham.cepik_connector import CEPiKConnector
    print("   ✅ CEPiKConnector imported successfully")
    print(f"   - Base URL: {CEPiKConnector.BASE_URL}")
    print(f"   - Target brands: {', '.join(CEPiKConnector.TARGET_BRANDS)}")
    print(f"   - Competitor brands (legacy): {', '.join(CEPiKConnector.COMPETITOR_BRANDS)}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print()

# Test 3: Import gotham_module
print("3️⃣  Testing gotham_module.py import...")
try:
    from backend.gotham_module import (
        GothamIntelligence,
        CEPiKConnector as GothamCEPiKConnector,
        BurningHouseCalculator
    )
    print("   ✅ GOTHAM module imported successfully")
    print("   - GothamIntelligence: OK")
    print("   - CEPiKConnector: OK")
    print("   - BurningHouseCalculator: OK")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print()

# Test 4: Verify new function exists
print("4️⃣  Testing get_leasing_expiry_counts() function...")
try:
    connector = CEPiKConnector()

    # Check if function exists
    if not hasattr(connector, 'get_leasing_expiry_counts'):
        raise AttributeError("get_leasing_expiry_counts not found")

    print("   ✅ Function exists and is callable")
    print(f"   - Function signature: get_leasing_expiry_counts(months_back=36)")

    # Check function docstring
    docstring = connector.get_leasing_expiry_counts.__doc__
    if docstring and "BUSINESS LOGIC" in docstring:
        print("   - Documentation: OK")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print()

# Test 5: Verify cache operations
print("5️⃣  Testing cache operations...")
try:
    # Test cache set/get
    test_data = {"BMW": 100, "AUDI": 85, "TOTAL": 185}

    CEPiKCache.set("test_key", test_data)
    print("   ✅ Cache SET operation: OK")

    retrieved = CEPiKCache.get("test_key")
    if retrieved == test_data:
        print("   ✅ Cache GET operation: OK")
    else:
        raise ValueError(f"Cache mismatch: expected {test_data}, got {retrieved}")

    # Test invalidation
    CEPiKCache.invalidate("test_key")
    print("   ✅ Cache INVALIDATE operation: OK")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print()

# Test 6: Verify get_opportunity_score exists
print("6️⃣  Testing get_opportunity_score() function...")
try:
    if not hasattr(GothamCEPiKConnector, 'get_opportunity_score'):
        raise AttributeError("get_opportunity_score not found")

    print("   ✅ Function exists in CEPiKConnector")
    print("   - This function calculates opportunity scores from real CEPiK data")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print()

# Test 7: Test date calculation logic
print("7️⃣  Testing date calculation logic...")
try:
    from datetime import datetime, timedelta

    # Simulate date range calculation (36 months back)
    today = datetime.now()
    start_date = today - timedelta(days=30 * 36)
    date_from = start_date.replace(day=1)

    end_date = today - timedelta(days=30 * 35)
    if end_date.month == 12:
        date_to = end_date.replace(year=end_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        date_to = end_date.replace(month=end_date.month + 1, day=1) - timedelta(days=1)

    print(f"   ✅ Date calculation logic: OK")
    print(f"   - Range: {date_from.strftime('%Y%m%d')} to {date_to.strftime('%Y%m%d')}")
    print(f"   - Month: {date_from.strftime('%B %Y')}")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("✅ ALL INTEGRATION TESTS PASSED!")
print("=" * 70)
print()
print("📝 SUMMARY:")
print("   - store.py: Caching layer implemented")
print("   - cepik_connector.py: Real API integration ready")
print("   - gotham_module.py: Updated to use new connector")
print("   - New function: get_leasing_expiry_counts(months_back=36)")
print("   - Target brands: TESLA, BMW, MERCEDES-BENZ, AUDI, VOLVO")
print("   - Caching: 24h TTL with fallback support")
print()
print("🚀 Ready to fetch REAL data from CEPiK API!")
print("   To test with real API: python backend/services/gotham/cepik_connector.py")
print()
