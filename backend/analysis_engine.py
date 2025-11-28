"""
ULTRA v3.1 - Deep Analysis Engine (Slow Path)
Analyzes conversation to build Client DNA: Psychometrics, Sales Temperature, Next Steps
Uses Ollama (DeepSeek/Llama3) for deep reasoning
"""
import os
import json
import asyncio
from typing import Dict, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")  # For Ollama Cloud
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")
ANALYSIS_TIMEOUT = 90  # seconds


class AnalysisEngine:
    """Deep analysis engine for psychological profiling and sales strategy"""
    
    def __init__(self):
        self.model = OLLAMA_MODEL.strip()
        self.base_url = OLLAMA_BASE_URL
        self.api_key = OLLAMA_API_KEY
        print(f"[ANALYSIS ENGINE] Initialized with model: {repr(self.model)}")
        print(f"[ANALYSIS ENGINE] Base URL: {self.base_url}")
        if self.api_key:
            print(f"[ANALYSIS ENGINE] API Key: {self.api_key[:5]}... (authenticated)")
    
    def _build_mega_prompt(self, chat_history: List[Dict], language: str = "PL") -> str:
        """Construct comprehensive Tesla-focused analysis prompt"""
        
        # Format conversation history based on language
        if language == "EN":
            conversation = "\n".join([
                f"{'CLIENT' if msg['role'] == 'user' else 'SALESPERSON'}: {msg['content']}"
                for msg in chat_history[-10:]  # Last 10 messages for context
            ])
        else:
            conversation = "\n".join([
                f"{'KLIENT' if msg['role'] == 'user' else 'SPRZEDAWCA'}: {msg['content']}"
                for msg in chat_history[-10:]  # Last 10 messages for context
            ])
        
        # English prompt
        if language == "EN":
            prompt = f"""CRITICAL: Respond ONLY IN ENGLISH. All analysis content, summaries, insights, and recommendations MUST be in English.

═══════════════════════════════════════════════════════════════
🎯 ULTRA V3.1 - DEEP PSYCHOMETRIC SALES ANALYSIS ENGINE
═══════════════════════════════════════════════════════════════

YOUR IDENTITY:
You are a RUTHLESS but EMPATHETIC Tesla Sales Strategist.
- You represent TESLA, not competitors
- Your goal is to maximize sale probability
- You MUST be OPINIONATED and ANALYTICAL, never neutral

CONVERSATION TO ANALYZE:
{conversation}

TASK: Generate a COMPLETE analysis in JSON format. ONLY JSON, no additional text.

CRITICAL ANALYSIS RULES (NON-NEGOTIABLE):

1. ⚡ NO NEUTRALITY - FORCE OPINIONS
   - NEVER return flat psychometric values (e.g., 50/50/50/50)
   - If client asks about money → Conservation: 75-85
   - If client asks about speed → Openness to Change: 75-85
   - Each psychometric dimension MUST have a distinct profile

2. 🔍 NO "UNKNOWN" - FORCE INFERENCE
   - "Unknown" = analytical failure
   - "for my wife" → Decision Maker: "Wife/Partner"
   - "asking about price" → Timeline: "1-2 months (Hot)"
   - "lease ending" → Timeline: "Immediate (2-4 weeks)"
   - INFER from subtle cues

3. 🏎️ TESLA IDENTITY (CRITICAL)
   - If client mentions competitor (e.g., "Mini"), DON'T say "Mini is great"
   - INSTEAD: "Mini is stylish, BUT Tesla Model Y has 3x better safety and lower TCO"
   - Tesla Hooks = ARGUMENTS AGAINST competition
   - Each hook must counter a specific competitor advantage

4. 🚫 ANTI-REPETITION
   - M6 SSR: Each entry MUST be unique
   - No copying text between entries
   - Each tactic must be concrete and DIFFERENT

REQUIRED JSON STRUCTURE (M1-M7):

{{
  "m1_dna": {{
    "summary": "2-3 sentences of psychological synthesis. MUST include main motivator and concern.",
    "mainMotivation": "Family Safety",
    "communicationStyle": "Analytical"
  }},
  "m2_indicators": {{
    "purchaseTemperature": 45,
    "churnRisk": "Medium",
    "funDriveRisk": "Low"
  }},
  "m3_psychometrics": {{
    "disc": {{
      "dominance": 30,
      "influence": 60,
      "steadiness": 75,
      "compliance": 55
    }},
    "bigFive": {{
      "openness": 65,
      "conscientiousness": 70,
      "extraversion": 45,
      "agreeableness": 80,
      "neuroticism": 40
    }},
    "schwartz": {{
      "opennessToChange": 55,
      "selfEnhancement": 35,
      "conservation": 75,
      "selfTranscendence": 70
    }}
  }},
  "m4_motivation": {{
    "keyInsights": [
      "Insight 1: Specific psychological observation",
      "Insight 2: Another observation",
      "Insight 3: Third observation"
    ],
    "teslaHooks": [
      "Hook 1: ARGUMENT AGAINST competitor with data",
      "Hook 2: Another hook - unique",
      "Hook 3: Third hook - concrete"
    ]
  }},
  "m5_predictions": {{
    "scenarios": [
      {{
        "outcome": "Positive",
        "description": "Most likely scenario",
        "probability": 60,
        "trigger": "What will cause this scenario"
      }},
      {{
        "outcome": "Negative",
        "description": "Failure scenario",
        "probability": 25,
        "trigger": "What will cause failure"
      }}
    ],
    "estimatedTimeline": "INFER from context! NOT 'Unknown'!"
  }},
  "m6_playbook": {{
    "suggestedTactics": [
      "Tactic 1: Concrete action",
      "Tactic 2: Another tactic",
      "Tactic 3: Third tactic"
    ],
    "ssr": [
      {{
        "fact": "Client trigger",
        "implication": "Psychological implication",
        "solution": "Tesla solution with data",
        "action": "Concrete action for salesperson"
      }},
      {{
        "fact": "Another trigger - UNIQUE",
        "implication": "Another implication",
        "solution": "Another solution",
        "action": "Another action - DIFFERENT!"
      }},
      {{
        "fact": "Third trigger",
        "implication": "Third implication",
        "solution": "Third solution",
        "action": "Third action - UNIQUE!"
      }}
    ]
  }},
  "m7_decision": {{
    "decisionMaker": "INFER! If 'for wife' → Wife",
    "influencers": ["Who else influences the decision?"],
    "criticalPath": "What will lead to the sale?"
  }},
  "journeyStageAnalysis": {{
    "currentStage": "QUALIFICATION",
    "confidence": 85,
    "reasoning": "Why this stage?"
  }}
}}

⚠️ FINAL REQUIREMENTS:
1. ONLY JSON - no text before/after
2. All fields REQUIRED
3. M3 differentiated (no 50/50/50/50)
4. M5 timeline and M7 decisionMaker CANNOT be "Unknown"
5. M6 SSR - each "action" unique
6. Tesla Hooks counter competition
7. Be OPINIONATED!
8. ALL TEXT VALUES MUST BE IN ENGLISH!

JSON:
"""
        else:  # Polish (PL) - default
            prompt = f"""KRYTYCZNIE WAŻNE: Odpowiadaj TYLKO PO POLSKU. Cała treść analizy, podsumowania, wnioski i rekomendacje MUSZĄ być po polsku.

═══════════════════════════════════════════════════════════════
🎯 ULTRA V3.1 - DEEP PSYCHOMETRIC SALES ANALYSIS ENGINE
═══════════════════════════════════════════════════════════════

TWOJA TOŻSAMOŚĆ:
Jesteś BEZWZGLĘDNYM, ale EMPATYCZNYM Strategiem Sprzedaży Tesla.
- Reprezentujesz TESLĘ, nie konkurencję
- Twoim celem jest zmaksymalizowanie prawdopodobieństwa sprzedaży
- Musisz być OPINIOTWÓRCZY i ANALITYCZNY, nigdy neutralny

ROZMOWA DO ANALIZY:
{conversation}

ZADANIE: Wygeneruj PEŁNĄ analizę w formacie JSON. TYLKO JSON, bez dodatkowego tekstu.

KRYTYCZNE ZASADY ANALIZY (NIEPRZEKRACZALNE):

1. ⚡ ZAKAZ NEUTRALNOŚCI - WYMUSZAJ OPINIE
   - NIGDY nie zwracaj płaskich wartości psychometrycznych (np. 50/50/50/50)
   - Jeśli klient pyta o pieniądze → Conservation: 75-85
   - Jeśli klient pyta o prędkość → Openness to Change: 75-85
   - Każdy wymiar psychometryczny MUSI mieć wyraźny profil

2. 🔍 ZAKAZ "UNKNOWN" - WYMUSZAJ WNIOSKOWANIE
   - "Unknown" = porażka analityczna
   - "dla żony" → Decision Maker: "Żona/Partnerka"
   - "pytanie o cenę" → Timeline: "1-2 miesiące (Gorący)"
   - "leasing się kończy" → Timeline: "Natychmiastowy (2-4 tygodnie)"
   - WNIOSKUJ z subtelnych wskazówek

3. 🏎️ TOŻSAMOŚĆ TESLA (KRYTYCZNE)
   - Jeśli klient wspomina konkurenta (np. "Mini"), NIE mów "Mini jest świetne"
   - ZAMIAST: "Mini jest stylowy, ALE Tesla Model Y ma 3x lepsze bezpieczeństwo i niższe TCO"
   - Tesla Hooks = ARGUMENTY PRZECIW konkurencji
   - Każdy hook musi kontratakować konkretną zaletę konkurenta

4. 🚫 ANTY-POWTÓRZENIA
   - M6 SSR: Każdy wpis MUSI być unikalny
   - Zakaz kopiowania tekstu w różnych wpisach
   - Każda taktyka musi być konkretna i RÓŻNA

WYMAGANA STRUKTURA JSON (M1-M7):

{{
  "m1_dna": {{
    "summary": "2-3 zdania syntezy psychologicznej. MUSI zawierać główny motywator i obawę.",
    "mainMotivation": "Bezpieczeństwo Rodziny",
    "communicationStyle": "Analytical"
  }},
  "m2_indicators": {{
    "purchaseTemperature": 45,
    "churnRisk": "Medium",
    "funDriveRisk": "Low"
  }},
  "m3_psychometrics": {{
    "disc": {{
      "dominance": 30,
      "influence": 60,
      "steadiness": 75,
      "compliance": 55
    }},
    "bigFive": {{
      "openness": 65,
      "conscientiousness": 70,
      "extraversion": 45,
      "agreeableness": 80,
      "neuroticism": 40
    }},
    "schwartz": {{
      "opennessToChange": 55,
      "selfEnhancement": 35,
      "conservation": 75,
      "selfTranscendence": 70
    }}
  }},
  "m4_motivation": {{
    "keyInsights": [
      "Wgląd 1: Konkretna obserwacja psychologiczna",
      "Wgląd 2: Inna obserwacja",
      "Wgląd 3: Trzecia obserwacja"
    ],
    "teslaHooks": [
      "Hook 1: ARGUMENT PRZECIW konkurentowi z danymi",
      "Hook 2: Inny hook - unikalny",
      "Hook 3: Trzeci hook - konkretny"
    ]
  }},
  "m5_predictions": {{
    "scenarios": [
      {{
        "outcome": "Positive",
        "description": "Najbardziej prawdopodobny scenariusz",
        "probability": 60,
        "trigger": "Co spowoduje ten scenariusz"
      }},
      {{
        "outcome": "Negative",
        "description": "Scenariusz porażki",
        "probability": 25,
        "trigger": "Co spowoduje porażkę"
      }}
    ],
    "estimatedTimeline": "WNIOSKUJ z kontekstu! NIE 'Unknown'!"
  }},
  "m6_playbook": {{
    "suggestedTactics": [
      "Taktyka 1: Konkretne działanie",
      "Taktyka 2: Inna taktyka",
      "Taktyka 3: Trzecia taktyka"
    ],
    "ssr": [
      {{
        "fact": "Trigger od klienta",
        "implication": "Psychologiczna implikacja",
        "solution": "Rozwiązanie Tesla z danymi",
        "action": "Konkretna akcja dla sprzedawcy"
      }},
      {{
        "fact": "Inny trigger - UNIKALNY",
        "implication": "Inna implikacja",
        "solution": "Inne rozwiązanie",
        "action": "Inna akcja - RÓŻNA!"
      }},
      {{
        "fact": "Trzeci trigger",
        "implication": "Trzecia implikacja",
        "solution": "Trzecie rozwiązanie",
        "action": "Trzecia akcja - UNIKALNA!"
      }}
    ]
  }},
  "m7_decision": {{
    "decisionMaker": "WNIOSKUJ! Jeśli 'dla żony' → Żona",
    "influencers": ["Kto jeszcze wpływa na decyzję?"],
    "criticalPath": "Co doprowadzi do sprzedaży?"
  }},
  "journeyStageAnalysis": {{
    "currentStage": "QUALIFICATION",
    "confidence": 85,
    "reasoning": "Dlaczego ten etap?"
  }}
}}

⚠️ FINALNE WYMAGANIA:
1. TYLKO JSON - bez tekstu przed/po
2. Wszystkie pola WYMAGANE
3. M3 zróżnicowane (zakaz 50/50/50/50)
4. M5 timeline i M7 decisionMaker NIE MOGĄ być "Unknown"
5. M6 SSR - każdy "action" unikalny
6. Tesla Hooks kontratakują konkurencję
7. Bądź OPINIOTWÓRCZY!
8. WSZYSTKIE WARTOŚCI TEKSTOWE MUSZĄ BYĆ PO POLSKU!

JSON:
"""
        return prompt

    async def _call_ollama(self, prompt: str) -> Optional[Dict]:
        """Call Ollama API with explicit cloud connection"""
        from ollama import AsyncClient
        
        # 1. Get Config (Explicitly bypass defaults)
        host = os.getenv("OLLAMA_BASE_URL") or "https://api.ollama.cloud"
        key = os.getenv("OLLAMA_API_KEY")
        model = self.model
        
        print(f"[ANALYSIS ENGINE] [DEBUG] Connecting to Ollama Host: {host}")
        print(f"[ANALYSIS ENGINE] [DEBUG] Model: {model}")
        print(f"[ANALYSIS ENGINE] [DEBUG] Key present: {bool(key)}")
        
        # 2. Init Client
        client_args = {"host": host}
        if key:
            client_args["headers"] = {"Authorization": f"Bearer {key}"}
            
        client = AsyncClient(**client_args)
        
        try:
            # 3. Call
            response = await client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            raw_response = response.get('message', {}).get('content', '')
            print(f"[ANALYSIS ENGINE] Raw response length: {len(raw_response)}")
            print(f"[ANALYSIS ENGINE] First 500 chars: {raw_response[:500]}")  # DEBUG
            
            # Try to extract JSON from response
            json_response = self._extract_json(raw_response)
            
            # DEBUG: Log parsing result
            if json_response:
                print(f"[ANALYSIS ENGINE] OK - JSON parsed successfully")
                print(f"[ANALYSIS ENGINE] Keys in response: {list(json_response.keys())}")
            else:
                print(f"[ANALYSIS ENGINE] ERROR - JSON parsing FAILED")
                print(f"[ANALYSIS ENGINE] Full response (first 1000 chars): {raw_response[:1000]}")
            
            return json_response
                
        except Exception as e:
            print(f"[ANALYSIS ENGINE] Error calling Ollama: {e}")
            return None
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response (handles markdown code blocks, etc)"""
        try:
            # Try direct parse first
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON in markdown code blocks
        import re
        # FIX: Corrected regex pattern (removed double escaping)
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except:
                pass
        
        # Try to find raw JSON object (greedy match for nested objects)
        # FIX: Corrected regex pattern
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
        
        # Last resort: find anything between first { and last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        
        print(f"[ANALYSIS ENGINE] Failed to extract JSON from response")
        return None
    
    def _create_fallback_analysis(self, language: str = "PL") -> Dict:
        """Create basic fallback analysis if LLM fails"""
        if language == "EN":
            return {
                "m1_dna": {
                    "summary": "Analysis unavailable - using basic profile.",
                    "mainMotivation": "Unknown",
                    "communicationStyle": "Analytical"
                },
                "m2_indicators": {
                    "purchaseTemperature": 50,
                    "churnRisk": "Medium",
                    "funDriveRisk": "Low"
                },
                "m3_psychometrics": {
                    "disc": {"dominance": 50, "influence": 50, "steadiness": 50, "compliance": 50},
                    "bigFive": {"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
                    "schwartz": {"opennessToChange": 50, "selfEnhancement": 50, "conservation": 50, "selfTranscendence": 50}
                },
                "m4_motivation": {
                    "keyInsights": ["Continue conversation to gather more data"],
                    "teslaHooks": ["Focus on building rapport first"]
                },
                "m5_predictions": {
                    "scenarios": [{"name": "Standard", "probability": 50, "description": "Awaiting more data"}],
                    "estimatedTimeline": "To be determined"
                },
                "m6_playbook": {
                    "suggestedTactics": ["Continue conversation, gather more information"],
                    "ssr": []
                },
                "m7_decision": {
                    "decisionMaker": "Unknown",
                    "influencers": [],
                    "criticalPath": "Gather more context"
                },
                "journeyStageAnalysis": {
                    "currentStage": "DISCOVERY",
                    "confidence": 50,
                    "reasoning": "Default stage - insufficient data"
                }
            }
        else:  # Polish (PL)
            return {
                "m1_dna": {
                    "summary": "Analiza niedostępna - używam podstawowego profilu.",
                    "mainMotivation": "Nieznany",
                    "communicationStyle": "Analytical"
                },
                "m2_indicators": {
                    "purchaseTemperature": 50,
                    "churnRisk": "Medium",
                    "funDriveRisk": "Low"
                },
                "m3_psychometrics": {
                    "disc": {"dominance": 50, "influence": 50, "steadiness": 50, "compliance": 50},
                    "bigFive": {"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
                    "schwartz": {"opennessToChange": 50, "selfEnhancement": 50, "conservation": 50, "selfTranscendence": 50}
                },
                "m4_motivation": {
                    "keyInsights": ["Kontynuuj rozmowę, zbieraj więcej danych"],
                    "teslaHooks": ["Skup się najpierw na budowaniu relacji"]
                },
                "m5_predictions": {
                    "scenarios": [{"name": "Standardowy", "probability": 50, "description": "Oczekiwanie na więcej danych"}],
                    "estimatedTimeline": "Do ustalenia"
                },
                "m6_playbook": {
                    "suggestedTactics": ["Kontynuuj rozmowę, zbieraj więcej informacji"],
                    "ssr": []
                },
                "m7_decision": {
                    "decisionMaker": "Nieznany",
                    "influencers": [],
                    "criticalPath": "Zbierz więcej kontekstu"
                },
                "journeyStageAnalysis": {
                    "currentStage": "DISCOVERY",
                    "confidence": 50,
                    "reasoning": "Domyślny etap - niewystarczające dane"
                }
            }
    
    async def run_deep_analysis(
        self, 
        session_id: str, 
        chat_history: List[Dict],
        language: str = "PL"
    ) -> Dict:
        """
        Main analysis function - runs deep psychometric and strategic analysis
        
        Args:
            session_id: Session ID for tracking
            chat_history: List of messages [{"role": "user/ai", "content": "..."}]
            language: Language code (PL/EN)
            
        Returns:
            Dict with complete analysis or fallback
        """
        print(f"[ANALYSIS ENGINE] Starting analysis for session: {session_id}")
        print(f"[ANALYSIS ENGINE] Message count: {len(chat_history)}")
        
        # Build prompt
        prompt = self._build_mega_prompt(chat_history, language)
        
        # Call LLM
        analysis = await self._call_ollama(prompt)
        
        if not analysis:
            print(f"[ANALYSIS ENGINE] Using fallback analysis")
            analysis = self._create_fallback_analysis(language)
        else:
            print(f"[ANALYSIS ENGINE] OK - Analysis complete")
            print(f"[ANALYSIS ENGINE] - M1 DNA: {analysis.get('m1_dna', {}).get('summary', '?')[:50]}...")
            print(f"[ANALYSIS ENGINE] - M2 Temperature: {analysis.get('m2_indicators', {}).get('purchaseTemperature', 0)}%")
            print(f"[ANALYSIS ENGINE] - Journey Stage: {analysis.get('journeyStageAnalysis', {}).get('currentStage', '?')}")
        
        return analysis


# Global instance
analysis_engine = AnalysisEngine()
