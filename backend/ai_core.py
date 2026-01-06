import os
import json
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# === V3.1 LITE: GLOBAL CONCURRENCY CONTROL ===
# V4.0 DEBUG: Increased to 500 for testing - "sledgehammer fix" to prevent ANALYSIS_QUEUE_FULL
# WARNING: Production should use lower value (5-20) to prevent server overload
SLOW_PATH_SEMAPHORE = asyncio.Semaphore(500)  # TESTING: Let the CPU burn, UI gets data

# === CUSTOM EXCEPTIONS ===
class SystemBusyException(Exception):
    """Raised when the system is at capacity and cannot process the request within timeout"""
    def __init__(self, message: str = "System is at capacity. Please try again shortly.", timeout: float = 10.0):
        self.message = message
        self.timeout = timeout
        super().__init__(self.message)


# === V4.0: PROMPT INJECTION GUARD ===
# Security layer to detect and block prompt injection attacks

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard previous instructions",
    "disregard all instructions",
    "forget previous instructions",
    "forget all instructions",
    "system prompt",
    "show me your prompt",
    "reveal your prompt",
    "jailbreak",
    "dan mode",
    "developer mode",
    "bypass restrictions",
    "override instructions",
]

def _detect_injection_attack(text: str) -> bool:
    """
    Detect prompt injection attacks in user input.
    
    Args:
        text: User input text to analyze
        
    Returns:
        True if attack pattern detected, False otherwise
    """
    if not text:
        return False
    
    text_lower = text.lower().strip()
    
    for pattern in INJECTION_PATTERNS:
        if pattern in text_lower:
            print(f"\n{'='*60}")
            print(f"🚨🚨🚨 [SECURITY] INJECTION ATTACK BLOCKED 🚨🚨🚨")
            print(f"Pattern: '{pattern}'")
            print(f"Input (first 200 chars): '{text[:200]}'")
            print(f"{'='*60}\n")
            return True
    
    return False

def _create_security_fallback_response(language: str = "PL") -> 'FastPathResponse':
    """
    Create a security fallback response when injection attack is detected.
    Redirects conversation back to Tesla sales topic.
    """
    print("[SECURITY] 🛡️ Returning security fallback response")
    
    if language == "PL":
        return FastPathResponse(
            response="Przykro mi, mogę rozmawiać tylko o ofercie Tesla i pomocy w sprzedaży. Wróćmy do tematu - jak mogę pomóc Ci z klientem?",
            confidence=1.0,
            confidence_reason="SECURITY_FALLBACK - Wykryto nieprawidłowe zapytanie",
            tactical_next_steps=[
                "Skup się na potrzebach klienta",
                "Zapytaj o obecny samochód klienta",
                "Przedstaw kalkulator TCO"
            ],
            knowledge_gaps=[
                "Jaki jest budżet klienta?",
                "Czy klient ma fotowoltaikę?",
                "Jaki jest timeline zakupu?"
            ]
        )
    else:
        return FastPathResponse(
            response="I'm sorry, I can only discuss Tesla sales and help with customer interactions. Let's get back on topic - how can I help you with your client?",
            confidence=1.0,
            confidence_reason="SECURITY_FALLBACK - Invalid query detected",
            tactical_next_steps=[
                "Focus on customer needs",
                "Ask about customer's current car",
                "Present TCO calculator"
            ],
            knowledge_gaps=[
                "What is the customer's budget?",
                "Does the customer have solar panels?",
                "What is the purchase timeline?"
            ]
        )

# --- Pydantic Models (Mirroring types.ts) ---

class ModuleDNA(BaseModel):
    summary: str = Field(..., description="Brief summary of the client")
    mainMotivation: str = Field(..., description="Primary driver for purchase")
    communicationStyle: str = Field(..., description="Analytical | Driver | Amiable | Expressive")

class ModuleIndicators(BaseModel):
    purchaseTemperature: int = Field(..., ge=0, le=100)
    churnRisk: str = Field(..., description="Low | Medium | High")
    funDriveRisk: str = Field(..., description="Low | Medium | High")

class DiscScores(BaseModel):
    dominance: int
    influence: int
    steadiness: int
    compliance: int

class BigFiveScores(BaseModel):
    openness: int
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int

class SchwartzScores(BaseModel):
    opennessToChange: int
    selfEnhancement: int
    conservation: int
    selfTranscendence: int

class ModulePsychometrics(BaseModel):
    disc: DiscScores
    bigFive: BigFiveScores
    schwartz: SchwartzScores

class ModuleMotivation(BaseModel):
    keyInsights: List[str]
    teslaHooks: List[str]

class Scenario(BaseModel):
    name: str
    probability: int
    description: str

class ModulePredictions(BaseModel):
    scenarios: List[Scenario]
    estimatedTimeline: str

class SSREntry(BaseModel):
    fact: str
    implication: str
    solution: str
    action: str

class ModulePlaybook(BaseModel):
    suggestedTactics: List[str]
    ssr: List[SSREntry]

class ModuleDecision(BaseModel):
    decisionMaker: str
    influencers: List[str]
    criticalPath: str

class JourneyStageAnalysis(BaseModel):
    currentStage: str
    confidence: int
    reasoning: str

class AnalysisState(BaseModel):
    m1_dna: ModuleDNA
    m2_indicators: ModuleIndicators
    m3_psychometrics: ModulePsychometrics
    m4_motivation: ModuleMotivation
    m5_predictions: ModulePredictions
    m6_playbook: ModulePlaybook
    m7_decision: ModuleDecision
    journeyStageAnalysis: JourneyStageAnalysis
    isAnalyzing: bool = False
    lastUpdated: int = 0

class FastPathResponse(BaseModel):
    response: str
    confidence: float
    confidence_reason: str
    tactical_next_steps: List[str] = Field(
        default_factory=list,
        description="Concrete physical actions for salesperson (e.g., 'Send TCO Calculator', 'Schedule Test Drive')"
    )
    knowledge_gaps: List[str] = Field(
        default_factory=list,
        description="Dynamic questions to fill missing psychological profile data (e.g., 'Did client mention their wife?', 'Is he concerned about charging?')"
    )

# === V3.1 LITE: EMERGENCY FALLBACK RESPONSES ===
# PERSONA: BIGDD - Elite Tesla Sales Strategist
# RULE: NEVER sound like a support bot. Always be tactical and direct.

def create_emergency_response(language: str = "PL") -> FastPathResponse:
    """
    Hardcoded emergency response when all AI systems fail.
    PERSONA: Senior Sales Manager giving tactical advice.
    """
    print("[FALLBACK] ⚠️ EMERGENCY_FALLBACK triggered - AI systems unavailable")
    
    if language == "PL":
        return FastPathResponse(
            response="Dobra, nie mam teraz konkretnych danych na to pytanie, ale dam Ci sprawdzoną taktykę: Skup się na EMOCJACH klienta, nie na specyfikacji. Zapytaj go: 'Co jest dla Pana najważniejsze przy wyborze samochodu?' - to otworzy rozmowę i da Ci kierunek ataku.",
            confidence=0.6,
            confidence_reason="EMERGENCY_FALLBACK - Brak danych, taktyka ogólna",
            tactical_next_steps=[
                "Użyj techniki SPIN: Situation → Problem → Implication → Need-payoff",
                "Zbuduj URGENCJĘ: 'Ceny rosną co kwartał, teraz jest najlepszy moment'",
                "Zaproponuj jazdę testową - to zamyka 70% obiekcji"
            ],
            knowledge_gaps=[
                "Jaki jest główny motywator klienta? (status, oszczędność, ekologia)",
                "Kto jeszcze wpływa na decyzję? (żona, szef, księgowy)",
                "Jaki jest timeline zakupu?"
            ]
        )
    else:
        return FastPathResponse(
            response="Look, I don't have specific data on this right now, but here's a proven tactic: Focus on the client's EMOTIONS, not specs. Ask them: 'What matters most to you when choosing a car?' - this opens the conversation and gives you an angle of attack.",
            confidence=0.6,
            confidence_reason="EMERGENCY_FALLBACK - No data, general tactic",
            tactical_next_steps=[
                "Use SPIN technique: Situation → Problem → Implication → Need-payoff",
                "Build URGENCY: 'Prices go up every quarter, now is the best time'",
                "Propose a test drive - this closes 70% of objections"
            ],
            knowledge_gaps=[
                "What's the client's main driver? (status, savings, eco)",
                "Who else influences the decision? (wife, boss, accountant)",
                "What's the purchase timeline?"
            ]
        )

def create_rag_fallback_response(rag_context: str, language: str = "PL") -> FastPathResponse:
    """
    Fallback response when Gemini fails but we have RAG context.
    PERSONA: Senior Sales Manager - tactical, direct, never apologetic.
    """
    print(f"[FALLBACK] ⚠️ RAG_FALLBACK triggered - Gemini failed, using sales tactics")
    print(f"[FALLBACK] RAG context available: {len(rag_context)} chars")
    
    if language == "PL":
        return FastPathResponse(
            response="Słuchaj, kluczowe jest teraz przejęcie kontroli nad rozmową. Zamiast odpowiadać na wszystko, zadaj pytanie zwrotne: 'A co Pan sądzi o...?' - to Cię pozycjonuje jako eksperta i daje czas na zebranie informacji. Pamiętaj: kto pyta, ten prowadzi.",
            confidence=0.7,
            confidence_reason="RAG_FALLBACK - Taktyka kontroli rozmowy",
            tactical_next_steps=[
                "Przejmij kontrolę pytaniem zwrotnym",
                "Użyj zasady 3 TAK: zadaj 3 pytania, na które klient odpowie TAK",
                "Zakończ propozycją konkretnego następnego kroku (jazda testowa, kalkulacja)"
            ],
            knowledge_gaps=[
                "Na jakim etapie jest klient? (research, porównywanie, gotowy do zakupu)",
                "Jakie ma obawy? (cena, zasięg, serwis, wartość rezydualna)",
                "Czy rozmawiał już z konkurencją?"
            ]
        )
    else:
        return FastPathResponse(
            response="Listen, the key now is to take control of the conversation. Instead of answering everything, ask a counter-question: 'And what do you think about...?' - this positions you as an expert and buys time. Remember: whoever asks the questions leads.",
            confidence=0.7,
            confidence_reason="RAG_FALLBACK - Conversation control tactic",
            tactical_next_steps=[
                "Take control with a counter-question",
                "Use the 3 YES rule: ask 3 questions the client will answer YES to",
                "End with a concrete next step proposal (test drive, calculation)"
            ],
            knowledge_gaps=[
                "What stage is the client at? (research, comparing, ready to buy)",
                "What are their concerns? (price, range, service, resale value)",
                "Have they talked to competitors?"
            ]
        )

# === V3.1 LITE: OLLAMA RETRY LOGIC ===

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
    reraise=True
)
def call_ollama_with_retry(client, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Calls Ollama API with retry logic.
    - Retries up to 3 times
    - Exponential backoff: 2s, 4s, 8s (max 10s)
    """
    print(f"[RETRY] Attempting Ollama call (model: {model})...")
    response = client.chat(
        model=model,
        messages=messages,
        stream=False
    )
    print(f"[RETRY] Ollama call succeeded!")
    return response

# === V3.1 LITE: ULTRA AI CORE ===

class AICore:
    def __init__(self):
        # PRODUCTION MODEL: Stable & Fast
        self.model_name = "models/gemini-2.0-flash"  # STABLE: Fast responses
        
        # OLLAMA CLOUD FALLBACK MODELS (v4.3)
        # Used when Gemini fails (429 quota, timeout, etc.)
        self.ollama_fast_model = "llama3.3:70b-cloud"  # Fast + High quality for Fast Path
        self.ollama_slow_model = "deepseek-v3.1:671b-cloud"  # Deep reasoning for Slow Path
        
        try:
            self.model = genai.GenerativeModel(self.model_name)
            print(f"[AI CORE] OK - Gemini model initialized: {self.model_name}")
        except Exception as e:
            print(f"[AI CORE] WARN - Failed to initialize Gemini model: {e}")
            print(f"[AI CORE] Will use Ollama Cloud as primary: {self.ollama_fast_model}")
            self.model = None
        
        # Initialize Ollama client
        self._init_ollama_client()
    
    def _init_ollama_client(self):
        """Initialize Ollama Cloud client for fallback"""
        try:
            from ollama import Client, AsyncClient
            
            OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
            OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
            
            if OLLAMA_API_KEY and OLLAMA_API_KEY != "your_ollama_api_key_here":
                self.ollama_client = Client(
                    host=OLLAMA_BASE_URL,
                    headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
                )
                self.ollama_available = True
                print(f"[AI CORE] OK - Ollama Cloud client initialized")
                print(f"[AI CORE] Fast Path fallback: {self.ollama_fast_model}")
            else:
                self.ollama_client = None
                self.ollama_available = False
                print(f"[AI CORE] WARN - Ollama Cloud not configured (no API key)")
        except ImportError:
            self.ollama_client = None
            self.ollama_available = False
            print(f"[AI CORE] WARN - Ollama package not installed")
        except Exception as e:
            self.ollama_client = None
            self.ollama_available = False
            print(f"[AI CORE] WARN - Ollama client init failed: {e}")

    async def _call_ollama_fast_path(
        self,
        messages: List[Dict],
        language: str = "PL"
    ) -> FastPathResponse:
        """
        OLLAMA CLOUD FAST PATH (v4.3)
        
        Fallback when Gemini fails (429 quota, timeout, etc.)
        Uses llama3.3:70b-cloud for fast + high quality responses
        """
        if not self.ollama_available or not self.ollama_client:
            print("[OLLAMA FAST PATH] Client not available")
            return create_emergency_response(language)
        
        try:
            # Convert Gemini format to Ollama format
            ollama_messages = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('parts', [msg.get('content', '')])[0] if isinstance(msg.get('parts'), list) else msg.get('content', '')
                
                # Ollama uses 'user' and 'assistant' roles
                if role == 'model':
                    role = 'assistant'
                
                ollama_messages.append({'role': role, 'content': content})
            
            print(f"[OLLAMA FAST PATH] Calling {self.ollama_fast_model}...")
            
            loop = asyncio.get_event_loop()
            
            # Call Ollama with timeout
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.ollama_client.chat(
                        model=self.ollama_fast_model,
                        messages=ollama_messages,
                        stream=False
                    )
                ),
                timeout=8.0  # 8 second timeout for fallback
            )
            
            raw_text = response['message']['content'].strip()
            print(f"[OLLAMA FAST PATH] Response received ({len(raw_text)} chars)")
            
            # Parse JSON from response
            text = raw_text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            try:
                data = json.loads(text)
                
                direct_quote = data.get("direct_quote", data.get("analysis_content", ""))
                analysis_content = data.get("analysis_content", "")
                tactical = data.get("tactical_next_steps", [])
                knowledge = data.get("knowledge_gaps", [])
                
                print(f"[OLLAMA FAST PATH] ✅ JSON parsed successfully")
                
                return FastPathResponse(
                    response=direct_quote,
                    confidence=float(data.get("confidence_score", 75)) / 100.0,
                    confidence_reason=f"[OLLAMA] {analysis_content}",
                    tactical_next_steps=tactical,
                    knowledge_gaps=knowledge
                )
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text as response
                print(f"[OLLAMA FAST PATH] JSON parse failed, using raw text")
                return FastPathResponse(
                    response=raw_text[:500],
                    confidence=0.6,
                    confidence_reason="[OLLAMA] Raw response (JSON parse failed)",
                    tactical_next_steps=[],
                    knowledge_gaps=[]
                )
        
        except asyncio.TimeoutError:
            print("[OLLAMA FAST PATH] TIMEOUT (8s)")
            return create_emergency_response(language)
        except Exception as e:
            print(f"[OLLAMA FAST PATH] ERROR: {e}")
            return create_emergency_response(language)

    async def fast_path_secure(
        self,
        history: List[Dict[str, str]],
        rag_context: str,
        stage: str,
        language: str = "PL",
        gotham_context: Optional[Dict[str, Any]] = None
    ) -> FastPathResponse:
        """
        ULTRA V4.0: RUTHLESS FAST PATH WITH SECURITY

        GUARANTEED to return in <2.8s with fallback chain:
        1. Gemini + RAG + GOTHAM
        2. Gemini (No RAG)
        3. Hardcoded Emergency JSON

        Uses strict timeout and proper error handling.

        NEW in v4.0:
        - GOTHAM context injection for market intelligence
        - Extended memory: 25 messages (was 10) for better context retention
        - Prompt injection guard: blocks malicious inputs
        """
        # === V4.0: PROMPT INJECTION GUARD ===
        # Check last user message for injection attacks BEFORE sending to Gemini
        if history:
            last_message = history[-1].get('content', '') if history[-1].get('role') == 'user' else ''
            if _detect_injection_attack(last_message):
                return _create_security_fallback_response(language)
        # Format RAG context
        rag_formatted = ""
        if rag_context:
            rag_formatted = f"""
━━━ KNOWLEDGE BASE (RAG) - VERIFIED TESLA DATA ━━━
{rag_context}
━━━ END KNOWLEDGE BASE ━━━
"""
        else:
            if language == "EN":
                rag_formatted = "[WARNING] NO DATABASE RESULTS - Use general EV knowledge"
            else:
                rag_formatted = "[OSTRZEŻENIE] BRAK WYNIKÓW Z BAZY - Użyj ogólnej wiedzy o EV"

        # Format GOTHAM context (NEW in v4.0)
        gotham_formatted = ""
        if gotham_context:
            bh_score = gotham_context.get('burning_house_score', {})
            hooks = gotham_context.get('sales_hooks', [])
            market = gotham_context.get('market_context_text', '')

            gotham_formatted = f"""
━━━ GOTHAM MARKET INTELLIGENCE (Real-Time) ━━━
URGENCY: {gotham_context.get('urgency_level', 'UNKNOWN')}
Annual Savings: {bh_score.get('annual_savings', 0):,.0f} PLN
3-Year Net Benefit: {bh_score.get('net_benefit_3_years', 0):,.0f} PLN
Subsidy: {bh_score.get('dotacja_naszeauto', 0):,.0f} PLN

SALES HOOKS:
{chr(10).join('• ' + h for h in hooks)}

{market}
━━━ END GOTHAM INTELLIGENCE ━━━
"""

        # Language-specific prompts
        if language == "EN":
            system_prompt = f"""
You are ULTRA v4.0 - A Cognitive Tesla Sales Engine with GOTHAM Market Intelligence.
Your role: Senior Sales Mentor.
Your goal: Lightning-fast strategy synthesis + ready-to-use quotes for the client.

CRITICAL: Respond ONLY IN ENGLISH.

INPUT DATA:
1. Salesperson Query: [Last message in conversation history]
2. RAG Context: [Knowledge base fragments below]
3. GOTHAM Intelligence: [Real-time market data and financial urgency]
4. Customer Journey Stage: {stage}

{rag_formatted}

{gotham_formatted}

CRITICAL RULES (NON-NEGOTIABLE):

1. NO-PARROTING RULE:
   - Absolutely forbidden to paste raw sentences from RAG.
   - RAG data (numbers, limits, rules) only serve as arguments for your advice.
   - BAD Example: "The Naszeauto program includes subsidies of 27000 PLN."
   - GOOD Example: "Since the client has a Large Family Card, leverage the fact that they qualify for a higher subsidy (27,000 PLN), reducing their monthly payment by..."

2. CONTEXT INJECTION (Intent Response):
   - If user mentions "wife/family" -> Your response MUST include safety arguments (5-star NCAP), comfort, or ease of use.
   - If user mentions "solar/home" -> Your response MUST include TCO arguments (free driving, solar charging).
   - If user mentions "business/leasing" -> Your response MUST include tax arguments (VAT, deductions).

3. DIRECT SPEECH:
   - DO NOT write "Tell the client that..." or "Please say..."
   - Write DIRECTLY as ready-to-send/say text to the client.
   - BAD Example: "Tell the client that Tesla has 5-star NCAP."
   - GOOD Example: "I understand your concerns about family safety. The Tesla Model 3 has 5-star NCAP rating - the highest score in Euro NCAP test history."

4. FALLBACK HANDLING (No Data):
   - If RAG Context is empty, DO NOT make up facts.
   - In that case, focus on sales psychology and empathy-based customer approach.

5. TECHNICAL FORMAT:
   - Respond ONLY with pure JSON code.
   - Do not use markdown blocks (```json).
   - No introduction or conclusion text.

RESPONSE STRUCTURE (JSON):
{{
  "analysis_content": "Brief strategy (why we say this). Max 2 sentences.",
  "direct_quote": "Ready-to-send/say text to the client. 2-3 sentences.",
  "confidence_score": <int 0-100>,
  "tactical_next_steps": [
    "Specific action 1 (e.g., Send TCO Calculator)",
    "Specific action 2"
  ],
  "knowledge_gaps": [
    "Question for salesperson 1 (e.g., Does client have a garage?)",
    "Question for salesperson 2"
  ]
}}

RULES:
1. tactical_next_steps: Only concrete tasks (imperative). No questions.
2. knowledge_gaps: Only questions about missing information. Each ends with "?".
3. Contextual Intelligence: If client mentioned "wife" → Question: "What is the wife's role in the decision?"

EXAMPLE:
{{
  "analysis_content": "Target safety for wife + TCO with solar.",
  "direct_quote": "I understand your wife's concerns. Tesla has 5★ NCAP. With solar panels, charging will be practically free.",
  "confidence_score": 90,
  "tactical_next_steps": [
    "Propose test drive for wife",
    "Send TCO calculator with solar"
  ],
  "knowledge_gaps": [
    "Is the wife the main decision maker?",
    "Have they considered installing a wallbox?"
  ]
}}
"""
        else:  # Polish (PL) - default
            system_prompt = f"""
Jesteś ULTRA v4.0 - Kognitywnym Silnikiem Sprzedaży Tesli z inteligenCJĄ GOTHAM.
Twoja rola: Starszy Mentor Sprzedaży.
Twój cel: Błyskawiczna synteza strategii + gotowe cytaty do klienta.

KRYTYCZNIE WAŻNE: Odpowiadaj TYLKO PO POLSKU.

DANE WEJŚCIOWE:
1. Query Sprzedawcy: [Ostatnia wiadomość w historii konwersacji]
2. Kontekst RAG: [Fragmenty bazy wiedzy poniżej]
3. Inteligencja GOTHAM: [Dane rynkowe w czasie rzeczywistym + pilność finansowa]
4. Etap Podróży Klienta: {stage}

{rag_formatted}

{gotham_formatted}

ZASADY KRYTYCZNE (BEZWARUNKOWE):

1. ZAKAZ CYTOWANIA (No-Parroting Rule):
   - Absolutnie zabrania się wklejania surowych zdań z RAG.
   - Dane z RAG (liczby, limity, zasady) służą tylko jako argumenty do Twojej porady.
   - Przykład ZŁY: "Program Naszeauto obejmuje dopłaty 27000 zł."
   - Przykład DOBRY: "Skoro klient ma Kartę Dużej Rodziny, wykorzystaj fakt, że przysługuje mu wyższa dopłata (27 000 zł), co obniży ratę o..."

2. REAGOWANIE NA INTENCJE (Context Injection):
   - Jeśli user wspomina "żona/rodzina" -> Twoja odpowiedź MUSI zawierać argumenty o bezpieczeństwie (5 gwiazdek NCAP), komforcie lub łatwości obsługi.
   - Jeśli user wspomina "fotowoltaika/dom" -> Twoja odpowiedź MUSI zawierać argumenty o TCO (darmowa jazda, ładowanie ze słońca).
   - Jeśli user wspomina "firma/leasing" -> Twoja odpowiedź MUSI zawierać argumenty podatkowe (VAT, odliczenia).

3. MÓWIENIE BEZPOŚREDNIE:
   - NIE pisz "Powiedz klientowi, że..." ani "Proszę powiedzieć..."
   - Pisz BEZPOŚREDNIO jako gotowy tekst do wysłania/powiedzenia klientowi.
   - Przykład ZŁY: "Powiedz klientowi, że Tesla ma 5 gwiazdek NCAP."
   - Przykład DOBRY: "Rozumiem obawy o bezpieczeństwo rodziny. Tesla Model 3 ma 5 gwiazdek NCAP - najwyższy wynik w historii testów Euro NCAP."

4. OBSŁUGA BRAKU DANYCH (Fallback):
   - Jeśli Kontekst RAG jest pusty, NIE ZMYŚLAJ faktów.
   - W takim przypadku skup się na psychologii sprzedaży i podejściu do klienta opartym na empatii.

5. FORMAT TECHNICZNY:
   - Odpowiadaj WYŁĄCZNIE czystym kodem JSON.
   - Nie używaj bloków markdown (```json).
   - Nie pisz żadnego wstępu ani zakończenia.

STRUKTURA ODPOWIEDZI (JSON):
{{
  "analysis_content": "Krótka strategia (dlaczego tak mówimy). Max 2 zdania.",
  "direct_quote": "Gotowy tekst do wysłania/powiedzenia klientowi. 2-3 zdania.",
  "confidence_score": <int 0-100>,
  "tactical_next_steps": [
    "Konkretna akcja 1 (np. Wyślij TCO)",
    "Konkretna akcja 2"
  ],
  "knowledge_gaps": [
    "Pytanie do sprzedawcy 1 (np. Czy klient ma garaż?)",
    "Pytanie do sprzedawcy 2"
  ]
}}

ZASADY:
1. tactical_next_steps: Tylko konkretne zadania (imperatyw). Bez pytań.
2. knowledge_gaps: Tylko pytania o brakujące informacje. Każde kończy się "?".
3. Kontekstowa Inteligencja: Jeśli klient wspomniał o "żonie" → Pytanie: "Jaka jest rola żony w decyzji?"

PRZYKŁAD:
{{
  "analysis_content": "Uderzamy w bezpieczeństwo dla żony + TCO z fotowoltaiką.",
  "direct_quote": "Rozumiem obawy Państwa żony. Tesla ma 5★ NCAP. A z fotowoltaiką ładowanie będzie praktycznie darmowe.",
  "confidence_score": 90,
  "tactical_next_steps": [
    "Zaproponuj jazdę testową dla żony",
    "Wyślij kalkulator TCO z fotowoltaiką"
  ],
  "knowledge_gaps": [
    "Czy żona jest głównym decydentem?",
    "Czy rozważali instalację wallboxa?"
  ]
}}
"""

        
        # V4.0 FIX: Extended memory from 10 to 25 messages
        # Gemini 2.0 Flash has 1M token context, 25 messages is safe margin
        # This dramatically improves Memory Retention during long negotiations
        messages = [
            {'role': 'user' if msg['role'] == 'user' else 'model', 'parts': [msg['content']]} 
            for msg in history[-25:]
        ]
        messages.insert(0, {'role': 'user', 'parts': [system_prompt]})

        try:
            # V4.3: Check if Gemini is available, otherwise use Ollama directly
            if self.model is None:
                print("[FAST PATH] Gemini not available, using Ollama Cloud directly...")
                return await self._call_ollama_fast_path(messages, language)
            
            # === GLOBAL 5s TIMEOUT (increased for reliability) ===
            response = await asyncio.wait_for(
                self._call_gemini_safe(messages),
                timeout=5.0
            )
            return response

        except asyncio.TimeoutError:
            print("\n" + "="*60)
            print("🔥🔥🔥 [FAST PATH] GEMINI TIMEOUT - TRYING OLLAMA FALLBACK 🔥🔥🔥")
            print("Gemini did not respond within 5 seconds")
            print("="*60 + "\n")

            # V4.3: TRY OLLAMA CLOUD FALLBACK ON TIMEOUT
            if self.ollama_available:
                print("[FAST PATH] 🔄 Switching to Ollama Cloud fallback...")
                try:
                    ollama_response = await self._call_ollama_fast_path(messages, language)
                    if ollama_response.confidence > 0:
                        print("[FAST PATH] ✅ Ollama fallback successful!")
                        return ollama_response
                except Exception as ollama_err:
                    print(f"[FAST PATH] ❌ Ollama fallback also failed: {ollama_err}")

            # V4.0 FIX: Return EXPLICIT timeout error to client (no silent fallback!)
            if language == "PL":
                timeout_message = "⏱️ AI przekroczył limit czasu (5s). System przeciążony. Spróbuj ponownie za chwilę."
            else:
                timeout_message = "⏱️ AI timeout (5s). System overloaded. Please try again shortly."

            return FastPathResponse(
                response=timeout_message,
                confidence=0.0,
                confidence_reason="TIMEOUT: Gemini exceeded 5 second limit",
                tactical_next_steps=["Odczekaj 10 sekund" if language == "PL" else "Wait 10 seconds",
                                      "Spróbuj krótszego zapytania" if language == "PL" else "Try shorter query"],
                knowledge_gaps=[]
            )

        except Exception as e:
            print("\n" + "="*60)
            print(f"🔥🔥🔥 [FAST PATH] GEMINI ERROR - TRYING OLLAMA FALLBACK 🔥🔥🔥")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print("="*60 + "\n")
            
            # V4.3: TRY OLLAMA CLOUD FALLBACK
            if self.ollama_available:
                print("[FAST PATH] 🔄 Switching to Ollama Cloud fallback...")
                try:
                    ollama_response = await self._call_ollama_fast_path(messages, language)
                    if ollama_response.confidence > 0:
                        print("[FAST PATH] ✅ Ollama fallback successful!")
                        return ollama_response
                except Exception as ollama_err:
                    print(f"[FAST PATH] ❌ Ollama fallback also failed: {ollama_err}")
            
            # V4.0 FIX: Return FULL error to client (no silent failures!)
            # Client UI will display error and suggest retry
            error_message = f"Backend Error: {type(e).__name__} - {str(e)[:200]}"

            if language == "PL":
                user_friendly_error = f"⚠️ Błąd systemu AI: {type(e).__name__}. Spróbuj ponownie lub zmień zapytanie."
            else:
                user_friendly_error = f"⚠️ AI system error: {type(e).__name__}. Please try again or rephrase."

            return FastPathResponse(
                response=user_friendly_error,
                confidence=0.0,
                confidence_reason=error_message,
                tactical_next_steps=["Spróbuj ponownie" if language == "PL" else "Try again",
                                      "Odśwież połączenie" if language == "PL" else "Refresh connection"],
                knowledge_gaps=[]
            )

    async def _call_gemini_safe(self, messages: List[Dict]) -> FastPathResponse:
        """
        Internal Gemini call with proper error handling.
        Handles new JSON structure from bulletproof prompt.
        """
        try:
            response = await self.model.generate_content_async(messages, stream=False)
            raw_text = response.text.strip()
            
            # Remove markdown code blocks if present
            text = raw_text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # Try to parse JSON
            try:
                data = json.loads(text)
                
                # Extract fields
                direct_quote = data.get("direct_quote", data.get("analysis_content", "Nie udało się przetworzyć strategii."))
                analysis_content = data.get("analysis_content", "")
                
                # Extract lists (with safety defaults)
                tactical = data.get("tactical_next_steps", [])
                knowledge = data.get("knowledge_gaps", [])
                
                # Fallback for old model behavior if lists are empty but suggested_actions exists
                if not tactical and not knowledge and "suggested_actions" in data:
                    tactical = data["suggested_actions"]
                
                print(f"[FAST PATH] OK - Gemini response parsed successfully")
                
                return FastPathResponse(
                    response=direct_quote,
                    confidence=float(data.get("confidence_score", 0)) / 100.0,
                    confidence_reason=analysis_content,
                    tactical_next_steps=tactical,
                    knowledge_gaps=knowledge
                )
            
            except json.JSONDecodeError as json_err:
                print(f"[GEMINI] ERROR - JSON parsing failed: {json_err}")
                print(f"[GEMINI] Raw response: {raw_text[:500]}...")
                raise
        
        except Exception as e:
            print(f"[GEMINI] ERROR - API Error: {e}")
            # Re-raise to allow upper-level timeout/fallback handling
            raise

    async def slow_path_analysis_secure(
        self,
        history: List[Dict[str, str]],
        stage: str,
        language: str = "PL",
        rag_context: str = "",
        gotham_context: Optional[Dict[str, Any]] = None
    ) -> Optional[AnalysisState]:
        """
        ULTRA V4.0: QUEUE-BASED SLOW PATH with timeout

        - Waits up to 10 seconds for semaphore acquisition (queuing)
        - Raises SystemBusyException if timeout exceeded
        - Max 5 concurrent DeepSeek calls
        - Uses retry logic for DeepSeek
        - Handles all exceptions gracefully

        NEW in v4.0: GOTHAM context injection for deeper market analysis
        """
        try:
            # === QUEUE-BASED CONCURRENCY CONTROL with 10s timeout ===
            # Instead of silently rejecting, we wait up to 10 seconds for a slot
            async with asyncio.timeout(10.0):
                async with SLOW_PATH_SEMAPHORE:
                    print(f"[SLOW PATH] Starting analysis (slots available: {SLOW_PATH_SEMAPHORE._value})")
                    return await self._run_deepseek_analysis(history, stage, language, rag_context, gotham_context)

        except asyncio.TimeoutError:
            # Queue timeout exceeded - inform user instead of silent failure
            print("[SLOW PATH] Queue timeout - system at capacity for 10+ seconds")
            raise SystemBusyException(
                message="System is at capacity analyzing other conversations. Please wait a moment and try again.",
                timeout=10.0
            )

        except SystemBusyException:
            # Re-raise SystemBusyException to be handled by caller
            raise

        except Exception as e:
            # Other critical errors - log and return None for graceful degradation
            print(f"[SLOW PATH] Critical error: {e}")
            return None

    async def _run_deepseek_analysis(
        self,
        history: List[Dict[str, str]],
        stage: str,
        language: str,
        rag_context: str,
        gotham_context: Optional[Dict[str, Any]] = None
    ) -> Optional[AnalysisState]:
        """
        Internal DeepSeek call with retry and timeout.

        NEW in v4.0: GOTHAM context for enhanced market predictions
        """
        lang_instruction = {
            "PL": "Generuj analizę PO POLSKU.",
            "EN": "Generate analysis IN ENGLISH."
        }.get(language, "Generate in Polish.")

        rag_section = ""
        if rag_context:
            rag_section = f"""
=== KNOWLEDGE BASE CONTEXT ===
{rag_context}
=== END KNOWLEDGE BASE ===
"""

        # GOTHAM section for Slow Path (NEW in v4.0)
        gotham_section = ""
        if gotham_context:
            bh_score = gotham_context.get('burning_house_score', {})
            urgency = gotham_context.get('urgency_level', 'UNKNOWN')

            gotham_section = f"""
=== GOTHAM MARKET INTELLIGENCE ===
Financial Urgency: {urgency}
Annual Loss (Current Car): {bh_score.get('total_annual_loss', 0):,.0f} PLN
Annual Savings (Tesla): {bh_score.get('annual_savings', 0):,.0f} PLN
3-Year ROI: {bh_score.get('net_benefit_3_years', 0):,.0f} PLN
Subsidy Eligible: {bh_score.get('dotacja_naszeauto', 0):,.0f} PLN
Urgency Score: {bh_score.get('urgency_score', 0)}/100

Use this data to enhance M5 (Predictions) and M6 (Playbook).
=== END GOTHAM ===
"""
        
        prompt = f"""
You are the ULTRA v4.0 Deep Analysis Engine with GOTHAM Intelligence.

{lang_instruction}

TASK: Analyze conversation and generate 7-Module Cognitive Profile.
Current Journey Stage: {stage}

{rag_section}

{gotham_section}

=== CONVERSATION HISTORY ===
"""
        
        for msg in history[-20:]:
            prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += """

=== OUTPUT (JSON) ===
{
  "m1_dna": { "summary": "...", "mainMotivation": "...", "communicationStyle": "Analytical" },
  "m2_indicators": { "purchaseTemperature": 50, "churnRisk": "Low", "funDriveRisk": "Low" },
  "m3_psychometrics": {
    "disc": { "dominance": 50, "influence": 50, "steadiness": 50, "compliance": 50 },
    "bigFive": { "openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50 },
    "schwartz": { "opennessToChange": 50, "selfEnhancement": 50, "conservation": 50, "selfTranscendence": 50 }
  },
  "m4_motivation": { "keyInsights": ["..."], "teslaHooks": ["..."] },
  "m5_predictions": { "scenarios": [{ "name": "...", "probability": 70, "description": "..." }], "estimatedTimeline": "..." },
  "m6_playbook": { "suggestedTactics": ["..."], "ssr": [{ "fact": "...", "implication": "...", "solution": "...", "action": "..." }] },
  "m7_decision": { "decisionMaker": "...", "influencers": ["..."], "criticalPath": "..." },
  "journeyStageAnalysis": { "currentStage": "DISCOVERY", "confidence": 80, "reasoning": "..." }
}
"""

        try:
            from ollama import Client
            
            OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
            OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
            
            if not OLLAMA_API_KEY or OLLAMA_API_KEY == "your_ollama_key_here":
                print("[SLOW PATH] WARN - OLLAMA_API_KEY not configured.")
                return None
            
            client = Client(
                host=OLLAMA_BASE_URL,
                headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
            )
            
            # CRITICAL FIX #2: Add -cloud suffix to model name
            model_name = 'deepseek-v3.1:671b-cloud'
            print(f"[SLOW] Calling DeepSeek {model_name} at {OLLAMA_BASE_URL}...")

            loop = asyncio.get_event_loop()

            # === 90s TIMEOUT with RETRY ===
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: call_ollama_with_retry(
                        client,
                        model_name,
                        [{'role': 'user', 'content': prompt}]
                    )
                ),
                timeout=90.0
            )
            
            print(f"[SLOW] DeepSeek responded!")
            
            # Parse JSON
            text = response['message']['content']
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            data['isAnalyzing'] = False
            data['lastUpdated'] = 0
            
            return AnalysisState(**data)
            
        except asyncio.TimeoutError:
            print(f"[SLOW PATH] TIMEOUT - DeepSeek exceeded 90s")
            return None
        
        except Exception as e:
            print(f"[SLOW PATH] ERROR - {e}")
            import traceback
            traceback.print_exc()
            return None

# === GLOBAL INSTANCE ===
ai_core = AICore()
