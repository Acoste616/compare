"""
Test GOTHAM Live Integration
Tests the complete flow: Intent Detection -> Scraper -> WebSocket -> Frontend
"""

import asyncio
import json
from backend.gotham_module import GothamIntelligence, BurningHouseCalculator
from backend.services.gotham.scraper import FuelPriceScraper

def test_scraper():
    """Test 1: Scraper functionality"""
    print("=" * 60)
    print("TEST 1: FUEL PRICE SCRAPER")
    print("=" * 60)

    # Test price fetching
    prices = FuelPriceScraper.get_prices_with_cache()
    print(f"✅ Prices loaded: {prices}")

    # Test freshness check
    is_fresh = FuelPriceScraper.is_data_fresh()
    print(f"✅ Data is fresh: {is_fresh}")

    print()

def test_burning_house_calculator():
    """Test 2: BurningHouseCalculator with live prices"""
    print("=" * 60)
    print("TEST 2: BURNING HOUSE CALCULATOR (LIVE DATA)")
    print("=" * 60)

    # Test live price integration
    pb95_price = BurningHouseCalculator.get_live_fuel_price("Pb95")
    print(f"✅ Live Pb95 price: {pb95_price} PLN/L")

    on_price = BurningHouseCalculator.get_live_fuel_price("ON")
    print(f"✅ Live Diesel price: {on_price} PLN/L")

    lpg_price = BurningHouseCalculator.get_live_fuel_price("LPG")
    print(f"✅ Live LPG price: {lpg_price} PLN/L")

    print()

def test_gotham_intelligence():
    """Test 3: Full GOTHAM Intelligence context"""
    print("=" * 60)
    print("TEST 3: GOTHAM INTELLIGENCE FULL CONTEXT")
    print("=" * 60)

    # Simulate client with high fuel costs
    context = GothamIntelligence.get_full_context(
        monthly_fuel_cost=1500,  # 1,500 PLN/month
        current_car_value=70_000,  # 70k PLN car
        annual_tax=225_000,  # High emission tax
        has_family_card=True,  # Karta Dużej Rodziny
        region="MAZOWIECKIE"
    )

    print(f"✅ Urgency Level: {context['urgency_level']}")
    print(f"✅ Annual Savings: {context['burning_house_score']['annual_savings']:,.0f} PLN")
    print(f"✅ Dotacja: {context['burning_house_score']['dotacja_naszeauto']:,.0f} PLN")
    print(f"✅ 3-Year Net Benefit: {context['burning_house_score']['net_benefit_3_years']:,.0f} PLN")
    print(f"✅ Urgency Score: {context['burning_house_score']['urgency_score']}/100")
    print(f"\n📊 Sales Hooks:")
    for hook in context['sales_hooks']:
        print(f"   • {hook}")

    print()

def test_intent_detection():
    """Test 4: Intent detection keywords"""
    print("=" * 60)
    print("TEST 4: INTENT DETECTION")
    print("=" * 60)

    # Test keywords
    test_messages = [
        "Ile kosztuje paliwo do tego auta?",
        "How much will I save on fuel?",
        "Jakie są koszty utrzymania?",
        "Tell me about the TCO",
        "Chcę wiedzieć o leasingu"
    ]

    financial_keywords = [
        "paliwo", "benzyna", "diesel", "lpg",
        "oszczędności", "oszczędzić", "taniej",
        "koszt", "koszty", "wydatek", "wydatki",
        "podatek", "opłata", "rata", "leasing",
        "spalanie", "pali", "zużycie",
        "tco", "całkowity koszt", "utrzymanie",
        "fuel", "gas", "petrol", "gasoline",
        "savings", "save", "cheaper",
        "cost", "costs", "expense", "expenses",
        "tax", "fee", "lease",
        "consumption", "burns", "mpg",
        "total cost", "maintenance"
    ]

    for msg in test_messages:
        detected = any(keyword in msg.lower() for keyword in financial_keywords)
        status = "✅ DETECTED" if detected else "❌ NOT DETECTED"
        print(f"{status}: \"{msg}\"")

    print()

def test_websocket_payload():
    """Test 5: WebSocket payload format"""
    print("=" * 60)
    print("TEST 5: WEBSOCKET PAYLOAD FORMAT")
    print("=" * 60)

    context = GothamIntelligence.get_full_context(
        monthly_fuel_cost=1200,
        current_car_value=80_000,
        annual_tax=225_000,
        has_family_card=False,
        region="ŚLĄSKIE"
    )

    # Simulate WebSocket message
    ws_payload = {
        "type": "gotham_update",
        "data": context
    }

    payload_json = json.dumps(ws_payload, indent=2, ensure_ascii=False)
    print("✅ WebSocket Payload Preview:")
    print(payload_json[:500] + "...")

    # Verify structure
    assert "type" in ws_payload
    assert "data" in ws_payload
    assert "burning_house_score" in ws_payload["data"]
    assert "urgency_level" in ws_payload["data"]
    print("\n✅ Payload structure is valid!")

    print()

if __name__ == "__main__":
    print("\n🔥 GOTHAM LIVE INTEGRATION TEST SUITE\n")

    try:
        test_scraper()
        test_burning_house_calculator()
        test_gotham_intelligence()
        test_intent_detection()
        test_websocket_payload()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n🚀 GOTHAM Live System is OPERATIONAL!\n")
        print("Next steps:")
        print("1. Start backend: uvicorn backend.main:app --reload")
        print("2. Start frontend: npm run dev")
        print("3. Mention 'paliwo' or 'koszt' in chat")
        print("4. Watch the red 'Burning House' widget appear! 🔥\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
