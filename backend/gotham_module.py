"""
TESLA-GOTHAM Module (ULTRA v4.0)
Real Market Intelligence for Polish EV Market

FEATURES:
- Burning House Calculator: Fuel + Taxes vs. EV TCO
- CEPiK Integration: Regional vehicle registration data (Mock for now)
- Market Urgency Scoring

Author: Lead Architect
Version: 1.0.0
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


# === PYDANTIC MODELS ===

class BurningHouseInput(BaseModel):
    """Input data for Burning House calculation"""
    monthly_fuel_cost: float = Field(..., description="Monthly fuel cost in PLN", ge=0)
    current_car_value: float = Field(..., description="Current car market value in PLN", ge=0)
    annual_tax: float = Field(225_000, description="Annual vehicle tax in PLN (default: 225k for high-emission)")
    has_family_card: bool = Field(False, description="Karta Dużej Rodziny eligibility")
    region: str = Field("ŚLĄSKIE", description="Voivodeship for CEPiK data")


class BurningHouseScore(BaseModel):
    """Burning House Score output"""
    total_annual_loss: float = Field(..., description="Total annual cost of keeping current car (fuel + tax)")
    ev_annual_cost: float = Field(..., description="Estimated annual cost with Tesla (electricity + tax)")
    annual_savings: float = Field(..., description="Annual savings by switching to EV")
    dotacja_naszeauto: float = Field(..., description="NaszEauto subsidy (27k or 40k PLN)")
    net_benefit_3_years: float = Field(..., description="Net financial benefit over 3 years")
    urgency_score: int = Field(..., description="Urgency score 0-100", ge=0, le=100)
    urgency_message: str = Field(..., description="Human-readable urgency message")


class CEPiKData(BaseModel):
    """CEPiK regional vehicle data"""
    region: str
    total_ev_registrations_2024: int
    growth_rate_yoy: float  # Year-over-year growth percentage
    top_brand: str
    trend: str  # "ROSNĄCY" | "STABILNY" | "SPADAJĄCY"


# === BURNING HOUSE CALCULATOR ===

class BurningHouseCalculator:
    """
    Calculates the financial "burning" cost of keeping a combustion car
    vs. switching to Tesla in the Polish market.

    KEY INSIGHT: Fuel + Taxes are "money on fire" every month.
    """

    # Constants (Polish market 2025)
    EV_ELECTRICITY_COST_PER_100KM = 8.0  # PLN (avg. home charging rate)
    EV_ANNUAL_TAX_MODEL_3 = 0  # PLN (EVs exempt from excise tax)
    DOTACJA_NASZEAUTO_STANDARD = 27_000  # PLN (standard subsidy)
    DOTACJA_NASZEAUTO_FAMILY = 40_000  # PLN (with Karta Dużej Rodziny)
    AVERAGE_ANNUAL_KM = 15_000  # Average Polish driver

    @classmethod
    def calculate(cls, input_data: BurningHouseInput) -> BurningHouseScore:
        """
        Calculate Burning House Score

        Formula:
        - Annual Loss = (Monthly Fuel * 12) + Annual Tax
        - EV Cost = (15,000 km / 100) * 8 PLN + 0 PLN tax = 1,200 PLN/year
        - Savings = Annual Loss - EV Cost
        - Net Benefit (3 years) = (Savings * 3) + Dotacja - (0 initial cost delta)
        """

        # 1. Calculate current car annual costs
        annual_fuel_cost = input_data.monthly_fuel_cost * 12
        annual_tax = input_data.annual_tax
        total_annual_loss = annual_fuel_cost + annual_tax

        # 2. Calculate Tesla annual costs
        ev_electricity_cost = (cls.AVERAGE_ANNUAL_KM / 100) * cls.EV_ELECTRICITY_COST_PER_100KM
        ev_annual_cost = ev_electricity_cost + cls.EV_ANNUAL_TAX_MODEL_3

        # 3. Calculate savings
        annual_savings = total_annual_loss - ev_annual_cost

        # 4. Determine subsidy
        dotacja = cls.DOTACJA_NASZEAUTO_FAMILY if input_data.has_family_card else cls.DOTACJA_NASZEAUTO_STANDARD

        # 5. Calculate 3-year net benefit
        savings_3_years = annual_savings * 3
        net_benefit_3_years = savings_3_years + dotacja

        # 6. Calculate urgency score (0-100)
        urgency_score = cls._calculate_urgency(
            annual_loss=total_annual_loss,
            car_value=input_data.current_car_value,
            annual_savings=annual_savings
        )

        # 7. Generate urgency message
        urgency_message = cls._generate_urgency_message(urgency_score, annual_savings)

        return BurningHouseScore(
            total_annual_loss=round(total_annual_loss, 2),
            ev_annual_cost=round(ev_annual_cost, 2),
            annual_savings=round(annual_savings, 2),
            dotacja_naszeauto=dotacja,
            net_benefit_3_years=round(net_benefit_3_years, 2),
            urgency_score=urgency_score,
            urgency_message=urgency_message
        )

    @staticmethod
    def _calculate_urgency(annual_loss: float, car_value: float, annual_savings: float) -> int:
        """
        Calculate urgency score based on financial loss velocity

        Scoring logic:
        - High annual loss (>30k PLN/year) = High urgency
        - Low car value (<50k PLN) = Lower opportunity cost to switch
        - High savings (>25k PLN/year) = High urgency
        """
        score = 0

        # Factor 1: Annual loss (0-40 points)
        if annual_loss > 30_000:
            score += 40
        elif annual_loss > 20_000:
            score += 30
        elif annual_loss > 10_000:
            score += 20
        else:
            score += 10

        # Factor 2: Car value (0-30 points) - inverse scoring (lower value = higher urgency)
        if car_value < 50_000:
            score += 30
        elif car_value < 100_000:
            score += 20
        elif car_value < 150_000:
            score += 10
        else:
            score += 5

        # Factor 3: Annual savings (0-30 points)
        if annual_savings > 25_000:
            score += 30
        elif annual_savings > 15_000:
            score += 20
        elif annual_savings > 10_000:
            score += 10
        else:
            score += 5

        return min(score, 100)

    @staticmethod
    def _generate_urgency_message(score: int, annual_savings: float) -> str:
        """Generate human-readable urgency message in Polish"""
        if score >= 80:
            return f"🔥 KRYTYCZNE: Tracisz {annual_savings:,.0f} PLN rocznie! Każdy miesiąc zwłoki kosztuje {annual_savings/12:,.0f} PLN."
        elif score >= 60:
            return f"⚠️ WYSOKIE: Potencjalne oszczędności {annual_savings:,.0f} PLN/rok. Warto działać teraz."
        elif score >= 40:
            return f"📊 UMIARKOWANE: Oszczędności {annual_savings:,.0f} PLN/rok. Rozważ switch w perspektywie 6-12 miesięcy."
        else:
            return f"✅ NISKIE: Oszczędności {annual_savings:,.0f} PLN/rok. Obecny pojazd jeszcze opłacalny."


# === CEPiK CONNECTOR (MOCK) ===

class CEPiKConnector:
    """
    Mock connector for CEPiK (Centralna Ewidencja Pojazdów i Kierowców)

    In production, this would connect to official government API.
    For now, returns realistic mock data for Polish regions.
    """

    # Mock data (2024 estimates based on real trends)
    MOCK_DATA = {
        "ŚLĄSKIE": CEPiKData(
            region="ŚLĄSKIE",
            total_ev_registrations_2024=3_245,
            growth_rate_yoy=124.5,
            top_brand="Tesla Model 3",
            trend="ROSNĄCY"
        ),
        "MAZOWIECKIE": CEPiKData(
            region="MAZOWIECKIE",
            total_ev_registrations_2024=8_127,
            growth_rate_yoy=156.3,
            top_brand="Tesla Model Y",
            trend="ROSNĄCY"
        ),
        "MAŁOPOLSKIE": CEPiKData(
            region="MAŁOPOLSKIE",
            total_ev_registrations_2024=2_891,
            growth_rate_yoy=98.7,
            top_brand="Tesla Model 3",
            trend="ROSNĄCY"
        ),
        "POMORSKIE": CEPiKData(
            region="POMORSKIE",
            total_ev_registrations_2024=2_134,
            growth_rate_yoy=87.2,
            top_brand="Volvo EX30",
            trend="STABILNY"
        ),
        "WIELKOPOLSKIE": CEPiKData(
            region="WIELKOPOLSKIE",
            total_ev_registrations_2024=2_567,
            growth_rate_yoy=102.4,
            top_brand="Tesla Model 3",
            trend="ROSNĄCY"
        ),
        "DOLNOŚLĄSKIE": CEPiKData(
            region="DOLNOŚLĄSKIE",
            total_ev_registrations_2024=2_456,
            growth_rate_yoy=91.8,
            top_brand="Tesla Model Y",
            trend="ROSNĄCY"
        )
    }

    @classmethod
    def get_regional_data(cls, region: str) -> Optional[CEPiKData]:
        """
        Get vehicle registration data for a specific region

        Args:
            region: Voivodeship name (e.g., "ŚLĄSKIE", "MAZOWIECKIE")

        Returns:
            CEPiKData or None if region not found
        """
        region_upper = region.upper()

        # Return mock data
        data = cls.MOCK_DATA.get(region_upper)

        if data:
            print(f"[CEPiK] Mock data for {region_upper}: {data.total_ev_registrations_2024} EVs (+{data.growth_rate_yoy}% YoY)")
        else:
            print(f"[CEPiK] WARN - No data for region: {region_upper}. Using ŚLĄSKIE as fallback.")
            data = cls.MOCK_DATA["ŚLĄSKIE"]

        return data

    @classmethod
    def get_market_context(cls, region: str) -> str:
        """
        Generate human-readable market context for sales pitch

        Returns:
            Formatted string with regional market insights
        """
        data = cls.get_regional_data(region)

        if not data:
            return "Brak danych rynkowych dla regionu."

        # Format growth rate
        growth_emoji = "📈" if data.growth_rate_yoy > 50 else "📊"
        trend_emoji = "🔥" if data.trend == "ROSNĄCY" else "✅"

        context = f"""
{trend_emoji} RYNEK {data.region}:
- {data.total_ev_registrations_2024:,} nowych rejestracji EV w 2024
- Wzrost {data.growth_rate_yoy}% r/r {growth_emoji}
- Najpopularniejszy: {data.top_brand}
- Trend: {data.trend}
        """.strip()

        return context


# === GOTHAM INTELLIGENCE API ===

class GothamIntelligence:
    """
    Main API for GOTHAM module
    Combines Burning House + CEPiK data into actionable sales intelligence
    """

    @staticmethod
    def get_full_context(
        monthly_fuel_cost: float,
        current_car_value: float,
        annual_tax: float = 225_000,
        has_family_card: bool = False,
        region: str = "ŚLĄSKIE"
    ) -> Dict[str, Any]:
        """
        Get complete GOTHAM context for AI injection

        Returns:
            Dictionary with:
            - burning_house_score: Financial urgency data
            - cepik_market: Regional market context
            - sales_hooks: Pre-formatted arguments for salesperson
        """

        # 1. Calculate Burning House Score
        bh_input = BurningHouseInput(
            monthly_fuel_cost=monthly_fuel_cost,
            current_car_value=current_car_value,
            annual_tax=annual_tax,
            has_family_card=has_family_card,
            region=region
        )

        burning_house = BurningHouseCalculator.calculate(bh_input)

        # 2. Get CEPiK market data
        cepik_data = CEPiKConnector.get_regional_data(region)
        market_context = CEPiKConnector.get_market_context(region)

        # 3. Generate sales hooks (ready-to-use arguments)
        sales_hooks = [
            f"Klient traci {burning_house.annual_savings:,.0f} PLN rocznie na paliwie i podatkach",
            f"Dotacja NaszEauto: {burning_house.dotacja_naszeauto:,.0f} PLN ({'Karta Dużej Rodziny' if has_family_card else 'Standard'})",
            f"Zwrot inwestycji w 3 lata: {burning_house.net_benefit_3_years:,.0f} PLN",
            f"Rynek {region}: +{cepik_data.growth_rate_yoy}% rejestracji EV r/r" if cepik_data else ""
        ]

        # Filter out empty hooks
        sales_hooks = [h for h in sales_hooks if h]

        return {
            "burning_house_score": burning_house.dict(),
            "cepik_market": cepik_data.dict() if cepik_data else None,
            "market_context_text": market_context,
            "sales_hooks": sales_hooks,
            "urgency_level": "CRITICAL" if burning_house.urgency_score >= 80 else "HIGH" if burning_house.urgency_score >= 60 else "MEDIUM"
        }


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    print("=== TESLA-GOTHAM Module Test ===\n")

    # Example: Client with high fuel costs and Karta Dużej Rodziny
    test_input = BurningHouseInput(
        monthly_fuel_cost=1_500,  # 1,500 PLN/month on fuel
        current_car_value=80_000,  # Car worth 80k PLN
        annual_tax=225_000,  # High emission tax
        has_family_card=True,
        region="ŚLĄSKIE"
    )

    print("INPUT:")
    print(f"- Monthly fuel: {test_input.monthly_fuel_cost} PLN")
    print(f"- Car value: {test_input.current_car_value:,} PLN")
    print(f"- Annual tax: {test_input.annual_tax:,} PLN")
    print(f"- Family card: {test_input.has_family_card}")
    print(f"- Region: {test_input.region}\n")

    # Calculate
    result = BurningHouseCalculator.calculate(test_input)

    print("BURNING HOUSE SCORE:")
    print(f"- Total annual loss: {result.total_annual_loss:,.2f} PLN")
    print(f"- EV annual cost: {result.ev_annual_cost:,.2f} PLN")
    print(f"- Annual savings: {result.annual_savings:,.2f} PLN")
    print(f"- NaszEauto subsidy: {result.dotacja_naszeauto:,.0f} PLN")
    print(f"- 3-year net benefit: {result.net_benefit_3_years:,.2f} PLN")
    print(f"- Urgency score: {result.urgency_score}/100")
    print(f"- Message: {result.urgency_message}\n")

    # Get full context
    full_context = GothamIntelligence.get_full_context(
        monthly_fuel_cost=1_500,
        current_car_value=80_000,
        annual_tax=225_000,
        has_family_card=True,
        region="ŚLĄSKIE"
    )

    print("GOTHAM INTELLIGENCE:")
    print(f"- Urgency level: {full_context['urgency_level']}")
    print(f"- Sales hooks:")
    for hook in full_context['sales_hooks']:
        print(f"  • {hook}")
    print(f"\n{full_context['market_context_text']}")
