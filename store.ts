
import { create } from 'zustand';
import { Session, AnalysisState, INITIAL_ANALYSIS, JourneyStage, Message, ViewState, RagNugget, GoldenStandard, Theme, Language, LogEntry } from './types';

// --- TRANSLATIONS ---
const TRANSLATIONS = {
  PL: {
    dashboard: "Pulpit",
    admin: "Panel Admin",
    dojo: "AI Dojo",
    newSession: "Nowa Sesja",
    recentSessions: "Ostatnie Sesje",
    sold: "SPRZEDANE",
    lost: "UTRACONE",
    secured: "System Bezpieczny",
    analysisStream: "Strumień Analizy",
    processing: "PRZETWARZANIE...",
    activeSessions: "Aktywne Sesje",
    attentionNeeded: "Wymaga Uwagi",
    avgTemp: "Śr. Temp. Zakupu",
    startNewSession: "START NOWEJ SESJI",
    searchPlaceholder: "Wyszukaj ID Sesji...",
    retrieve: "Pobierz",
    activeOperations: "Aktywne Operacje",
    archivedHistory: "Archiwum Historii",
    systemModules: "Moduły Systemu",
    endSession: "Zakończ Sesję",
    typeMessage: "Wpisz odpowiedź klienta...",
    sessionClosed: "Sesja Zamknięta - Tylko Odczyt",
    missionDebrief: "Raport Misji",
    confirmOutcome: "Potwierdź wynik sesji",
    saleClosed: "SPRZEDAŻ",
    noSale: "BRAK SPRZEDAŻY",
    updatingModels: "Aktualizacja Modeli...",
    churnHigh: "Wysokie Ryzyko Rezygnacji",
    churnLow: "Niskie Ryzyko",
    funDriveHigh: "Wysoka",
    funDriveLow: "Niska",
    dnaSummary: "Synteza Profilu AI",
    coreDrivers: "Kluczowe Motywatory",
    teslaAnchors: "Haki Sprzedażowe Tesla",
    nextBestAction: "Rekomendowana Akcja",
    decisionMaker: "Decydent",
    criticalPath: "Ścieżka Krytyczna",
    estTimeline: "Szac. Czas",
    // Dashboard additional
    cognitiveEngineActive: "Kognitywny Silnik Sprzedaży AKTYWNY",
    systemMonitoring: "System ULTRA v3.0 monitoruje interakcje w czasie rzeczywistym. Protokół prywatności: wszystkie dane osobowe usunięte.",
    anonymizedTracking: "Anonimowe śledzenie",
    allSystemsNominal: "Wszystkie systemy sprawne",
    noActiveSessions: "Brak aktywnych sesji.",
    noArchivedSessions: "Brak zarchiwizowanych sesji.",
    sale: "SPRZEDAŻ",
    loss: "UTRACONA",
    strategy: "Strategia",
    toClient: "Do Klienta",
    // Chat additional
    connectionFailure: "Błąd połączenia. Upewnij się, że Backend działa."
  },
  EN: {
    dashboard: "Dashboard",
    admin: "Admin Panel",
    dojo: "AI Dojo",
    newSession: "New Session",
    recentSessions: "Recent Sessions",
    sold: "SOLD",
    lost: "LOST",
    secured: "System Secured",
    analysisStream: "Analysis Stream",
    processing: "PROCESSING...",
    activeSessions: "Active Sessions",
    attentionNeeded: "Attention Needed",
    avgTemp: "Avg. Purchase Temp",
    startNewSession: "START NEW SESSION",
    searchPlaceholder: "Retrieve Session ID...",
    retrieve: "Retrieve",
    activeOperations: "Active Operations",
    archivedHistory: "Archived History",
    systemModules: "System Modules",
    endSession: "End Session",
    typeMessage: "Type customer response...",
    sessionClosed: "Session Closed - Read Only",
    missionDebrief: "Mission Debrief",
    confirmOutcome: "Confirm session outcome",
    saleClosed: "SALE CLOSED",
    noSale: "NO SALE",
    updatingModels: "Updating Models...",
    churnHigh: "High Churn Risk",
    churnLow: "Low Risk",
    funDriveHigh: "High",
    funDriveLow: "Low",
    dnaSummary: "AI Profile Synthesis",
    coreDrivers: "Core Drivers",
    teslaAnchors: "Tesla Anchors",
    nextBestAction: "Next Best Action",
    decisionMaker: "Decision Maker",
    criticalPath: "Critical Path",
    estTimeline: "Est. Timeline",
    // Dashboard additional
    cognitiveEngineActive: "Cognitive Sales Engine ACTIVE",
    systemMonitoring: "System ULTRA v3.0 is monitoring real-time interactions. Privacy Protocol Enforced: All personal identifiers stripped.",
    anonymizedTracking: "Anonymized tracking",
    allSystemsNominal: "All systems nominal",
    noActiveSessions: "No active sessions.",
    noArchivedSessions: "No archived sessions found.",
    sale: "SALE",
    loss: "LOSS",
    strategy: "Strategy",
    toClient: "To Client",
    // Chat additional
    connectionFailure: "Connection failure. Please ensure Backend is running."
  }
};

// --- MOCK DATA FOR KNOWLEDGE BASE ---

const INITIAL_RAG_NUGGETS: RagNugget[] = [
  {
    id: 'f4895319-9a1b-4b03-ba8e-68ad1751c491',
    title: 'Cena Model 3 Long Range 2025 (Polska)',
    content: 'Tesla Model 3 Long Range (2025) w Polsce kosztuje 229,990 PLN (cena katalogowa). Po odliczeniu dotacji "Mój Elektryk" (18,750 PLN netto) efektywna cena wynosi ~211,240 PLN. Zasięg WLTP: 629 km. Przyspieszenie 0-100 km/h: 4.4 sekundy. W standardzie pompa ciepła i podwójne szyby.',
    keywords: ['Model 3', 'cena', '2025', 'dotacja', 'mój elektryk', 'zasięg'],
    language: 'PL'
  },
  {
    id: 'a1235319-9a1b-4b03-ba8e-123123123',
    title: 'Tesla Vision vs USS (Czujniki Parkowania)',
    content: 'Wszystkie nowe modele (3/Y) od 2023 nie posiadają czujników ultradźwiękowych (USS). System opiera się w 100% na kamerach (Tesla Vision). High Fidelity Park Assist rysuje otoczenie w 3D. Ważne: Brak sygnału dźwiękowego poniżej 30cm w starszych wersjach softu, aktualizacje poprawiły precyzję.',
    keywords: ['Tesla Vision', 'Park Assist', 'USS', 'czujniki', 'kamery', 'parkowanie'],
    language: 'PL'
  },
  {
    id: 'bat-001',
    title: 'Degradacja Baterii i Zasięg Zimą',
    content: 'Baterie Tesla tracą średnio tylko 12% pojemności po 300,000 km. Zimą zasięg może spaść o 10-20% w zależności od temperatury, ale system pompy ciepła (Heat Pump) drastycznie redukuje te straty w porównaniu do konkurencji. Zalecane przygotowanie auta (Preconditioning) w aplikacji przed jazdą.',
    keywords: ['bateria', 'zima', 'zasięg', 'degradacja', 'pompa ciepła', 'mróz'],
    language: 'PL'
  },
  // ADDED: Naszeauto Nuggets
  {
    id: 'na-001',
    title: 'Program "Naszeauto" - Kryteria Kwalifikacji (Model 3/Y)',
    content: 'Program "Naszeauto" obejmuje Teslę Model 3 i Model Y pod warunkiem nieprzekroczenia limitu ceny 225 000 PLN brutto (dla osób fizycznych) lub 201 792 PLN netto (dla firm). Model 3 RWD mieści się w limicie. Model Y RWD jest na granicy - wymaga weryfikacji aktualnego cennika. Wersje Long Range i Performance zazwyczaj przekraczają limit, chyba że klient posiada Kartę Dużej Rodziny (brak limitu ceny).',
    keywords: ['Naszeauto', 'dotacja', 'limit ceny', 'Model 3', 'Model Y', 'kwalifikacja'],
    language: 'PL'
  },
  {
    id: 'na-002',
    title: 'Wysokość Dopłat "Naszeauto"',
    content: 'Maksymalna kwota dotacji w programie "Naszeauto" wynosi 18 750 PLN dla nabywców indywidualnych i firm. Posiadacze Karty Dużej Rodziny mogą ubiegać się o 27 000 PLN. Dotacja jest wypłacana jako refundacja po zakupie (ok. 3-6 miesięcy oczekiwania).',
    keywords: ['Naszeauto', 'kwota', '18750', '27000', 'refundacja', 'KDR'],
    language: 'PL'
  },
  {
    id: 'na-003',
    title: 'Analiza TCO vs Brak Dotacji (Naszeauto)',
    content: 'Jeśli klient nie kwalifikuje się do "Naszeauto" (np. wybiera wersję Long Range), kluczowym argumentem jest TCO (Całkowity Koszt Posiadania). Oszczędność na paliwie (ok. 15 000 PLN rocznie przy przebiegu 25k km) oraz serwisie przewyższa wartość dotacji w ciągu pierwszych 18-24 miesięcy eksploatacji. Wartość rezydualna Tesli (jedna z najwyższych na rynku) dodatkowo rekompensuje brak wstępnej dotacji.',
    keywords: ['TCO', 'koszty', 'oszczędność', 'paliwo', 'serwis', 'wartość rezydualna', 'Naszeauto'],
    language: 'PL'
  }
];

const INITIAL_GOLDEN_STANDARDS: GoldenStandard[] = [
  {
    id: '1081',
    category: 'financial',
    context: 'Klient pyta o leasing dla firmy',
    response: 'Leasing operacyjny Tesla dla firmy to świetna decyzja finansowa. Korzyści: 1) 100% raty leasingowej = koszt uzyskania przychodu (KUP). 2) VAT marża 23% - pełne odliczenie. 3) 0% emisji = brak podatku od środków transportu (~2000 zł/rok oszczędności). Przykład Model 3 LR (250k): wpłata 20% (50k), 48 m-cy, rata ~2800 zł netto. ROI: Tesla zwraca się w 3-4 lata dzięki oszczędnościom na paliwie i serwisie.',
    tags: ['leasing', 'firma', 'b2b', 'vat', 'finansowanie'],
    language: 'PL',
    date: '11.11.2025'
  },
  {
    id: '1080',
    category: 'competitive',
    context: 'Klient porównuje Teslę z BMW i4',
    response: 'BMW i4 to solidne auto, ale Tesla Model 3 wygrywa w kluczowych kategoriach EV: 1) Zasięg realny i sieć Superchargerów (niezawodność podróży). 2) Technologia Software (aktualizacje OTA vs wizyty w serwisie). 3) Cena/Jakość - Model 3 jest tańszy o ok. 50 tys. PLN przy lepszym wyposażeniu standardowym. Jeśli zależy Panu na technologii i spokoju w trasie, Tesla jest bezkonkurencyjna.',
    tags: ['porównanie', 'bmw', 'i4', 'konkurencja'],
    language: 'PL',
    date: '11.11.2025'
  }
];

// --- DEMO DATA ---
const DEMO_SESSION_ID = 'S-XLC-589';

const DEMO_MESSAGES: Message[] = [
  {
    id: 'msg-1',
    role: 'user',
    content: "Klient jest zaniepokojony. Mówi, że 'słyszał, że Tesla zimą traci 40% zasięgu' i boi się, że nie dojedzie z Warszawy do Krakowa.",
    timestamp: Date.now() - 10000
  },
  {
    id: 'msg-2',
    role: 'ai',
    content: "Rozumiem obawy dotyczące zasięgu zimą. Rzeczywisty spadek zasięgu zależy od wielu czynników, takich jak temperatura, styl jazdy i używanie ogrzewania. Proszę pamiętać, że Tesla ma system wstępnego ogrzewania baterii, co minimalizuje utratę zasięgu w chłodne dni. Dodatkowo, może Pan skorzystać z planera podróży w Tesli, który uwzględnia warunki pogodowe i zaplanuje ładowanie po drodze, aby zapewnić dotarcie do celu.",
    timestamp: Date.now(),
    confidence: 0.60,
    confidenceReason: "(Brak konkretnych danych w bazie wiedzy dotyczących utraty zasięgu zimą. Odpowiedź opiera się na ogólnej wiedzy o Tesli i systemach ogrzewania baterii.)",
    clientStyle: "Techniczny",
    contextNeeds: [
      "Jak klient zareagował na informację o systemie wstępnego ogrzewania baterii?",
      "Czy klient wydaje się bardziej zaniepokojony zasięgiem, czy wygodą podróży?"
    ],
    suggestedActions: [
      "Czy ma Pan możliwość ładowania w domu lub w pracy?",
      "Czy chciałby Pan zobaczyć symulację trasy do Krakowa w nawigacji?"
    ]
  }
];

const DEMO_ANALYSIS: AnalysisState = {
  ...INITIAL_ANALYSIS,
  m1_dna: {
    summary: "Klient wykazuje wysoki poziom technicznej świadomości, ale posiada silne obawy (lęk przed zasięgiem). Wymaga argumentacji opartej na danych.",
    mainMotivation: "Bezpieczeństwo / Niezawodność",
    communicationStyle: "Analytical"
  },
  m2_indicators: {
    purchaseTemperature: 35,
    churnRisk: "Medium",
    funDriveRisk: "Low"
  },
  m3_psychometrics: {
    disc: { dominance: 20, influence: 30, steadiness: 80, compliance: 70 },
    bigFive: { openness: 40, conscientiousness: 80, extraversion: 30, agreeableness: 60, neuroticism: 70 },
    schwartz: { opennessToChange: 20, selfEnhancement: 30, conservation: 80, selfTranscendence: 60 }
  },
  m4_motivation: {
    keyInsights: [
      "Klient unika ryzyka technologicznego (Early Adopter Anxiety).",
      "Lęk przed utratą kontroli nad podróżą (Range Anxiety).",
      "Potrzeba dowodu społecznego lub technicznego."
    ],
    teslaHooks: [
      "Pokaż Trip Planner (predykcja zużycia z dokładnością do 1%).",
      "Wyjaśnij technologię Heat Pump (niezawodność w -20°C).",
      "Pokaż mapę Superchargerów (niezawodność 99.9%)."
    ]
  },
  m6_playbook: {
    suggestedTactics: [
      "Zastosuj technikę 'Feel-Felt-Found' ('Rozumiem Pana obawy, inni też tak myśleli, ale odkryli...').",
      "Zaproponuj symulację trasy Warszawa-Kraków w aucie demo.",
      "Przedstaw dane o degradacji baterii (tylko 12% po 300k km).",
      "Umów jazdę próbną w chłodny dzień (jeśli możliwe)."
    ],
    ssr: [
      {
        fact: "Obawa o zasięg zimą (Warszawa-Kraków)",
        implication: "Klient boi się utknąć w trasie z rodziną (Lęk przed utratą kontroli).",
        solution: "Heat Pump + Trip Planner (Precyzja 99%).",
        action: "Pokaż ekran Trip Plannera z estymacją % baterii u celu."
      },
      {
        fact: "Słyszał, że traci 40% zasięgu",
        implication: "Opiera się na mitach lub starych danych (Brak zaufania do technologii).",
        solution: "Dane o degradacji (12% przy 300k km) i testy norweskie.",
        action: "Użyj argumentu: 'W Norwegii 80% aut to elektryki'."
      }
    ]
  },
  journeyStageAnalysis: {
    currentStage: JourneyStage.OBJECTION_HANDLING,
    confidence: 0.9,
    reasoning: "Klient wyraża obawy (objections) dotyczące zasięgu i niezawodności, co jest typowe dla etapu obsługi obiekcji."
  },
  lastUpdated: Date.now()
};

interface KnowledgeBase {
  nuggets: RagNugget[];
  standards: GoldenStandard[];
}

interface AppState {
  currentView: ViewState;
  currentSessionId: string | null;
  sessions: Record<string, Session>;
  currentAnalysis: AnalysisState;
  knowledgeBase: KnowledgeBase;
  systemLogs: LogEntry[];

  // Settings
  theme: Theme;
  language: Language;
  toggleTheme: () => void;
  toggleLanguage: () => void;
  t: (key: keyof typeof TRANSLATIONS.EN) => string;

  // Actions
  setView: (view: ViewState) => void;
  createSession: () => Promise<string>;
  selectSession: (id: string) => void;
  closeSession: (id: string, outcome: 'sale' | 'no_sale') => void;
  addMessage: (sessionId: string, message: Message) => void;
  setFeedback: (sessionId: string, messageId: string, feedback: 'positive' | 'negative', details?: string) => void;
  updateJourneyStage: (sessionId: string, stage: JourneyStage) => void;
  updateAnalysis: (partial: Partial<AnalysisState>) => void;
  setAnalyzing: (isAnalyzing: boolean) => void;

  // Knowledge Base Actions
  addNugget: (nugget: RagNugget) => void;
  removeNugget: (id: string) => void;
  addStandard: (standard: GoldenStandard) => void;
  removeStandard: (id: string) => void;
}

export const useStore = create<AppState>((set, get) => ({
  currentView: 'dashboard',
  currentSessionId: null,

  theme: 'dark',
  language: 'PL',

  toggleTheme: () => set(state => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
  toggleLanguage: () => set(state => ({ language: state.language === 'PL' ? 'EN' : 'PL' })),
  t: (key) => {
    const lang = get().language;
    return TRANSLATIONS[lang][key] || key;
  },

  sessions: {
    [DEMO_SESSION_ID]: {
      id: DEMO_SESSION_ID,
      createdAt: Date.now(),
      status: 'active',
      outcome: null,
      journeyStage: JourneyStage.OBJECTION_HANDLING,
      messages: DEMO_MESSAGES,
      lastUpdated: Date.now(),
      analysisState: DEMO_ANALYSIS
    }
  },

  currentAnalysis: INITIAL_ANALYSIS,

  knowledgeBase: {
    nuggets: INITIAL_RAG_NUGGETS,
    standards: INITIAL_GOLDEN_STANDARDS
  },

  systemLogs: [
    { id: 'log-init', timestamp: Date.now(), type: 'INFO', message: 'ULTRA v3.0 System Initialized', source: 'SYSTEM' }
  ],

  setView: (view) => set({ currentView: view }),

  createSession: async () => {
    try {
      const response = await fetch('http://localhost:8000/api/sessions', { method: 'POST' });
      const data = await response.json();
      const id = data.id;

      set((state) => ({
        sessions: {
          ...state.sessions, [id]: {
            id,
            createdAt: Date.now(),
            status: 'active',
            outcome: null,
            journeyStage: JourneyStage.DISCOVERY,
            messages: [],
            lastUpdated: Date.now(),
            analysisState: INITIAL_ANALYSIS
          }
        },
        currentSessionId: id,
        currentView: 'chat',
        currentAnalysis: INITIAL_ANALYSIS,
        systemLogs: [{
          id: `log-${Date.now()}`,
          timestamp: Date.now(),
          type: 'INFO',
          message: `Session ${id} started`,
          source: 'USER'
        }, ...state.systemLogs]
      }));
      return id;
    } catch (e) {
      console.error("Failed to create session", e);
      // Fallback for demo if backend is down? Or just fail.
      // For now, let's return empty string or handle error.
      return "";
    }
  },

  selectSession: (id) => set((state) => {
    const session = state.sessions[id];
    if (!session) return {};
    return {
      currentSessionId: id,
      currentView: 'chat',
      currentAnalysis: session.analysisState
    };
  }),

  closeSession: (id, outcome) => set((state) => {
    const session = state.sessions[id];
    if (!session) return state;

    const updatedSession: Session = {
      ...session,
      status: 'closed',
      outcome: outcome,
      lastUpdated: Date.now()
    };

    return {
      sessions: {
        ...state.sessions,
        [id]: updatedSession
      },
      currentSessionId: null, // Deselect
      currentView: 'dashboard', // Go to dashboard
      systemLogs: [{
        id: `log-${Date.now()}`,
        timestamp: Date.now(),
        type: outcome === 'sale' ? 'SUCCESS' : 'WARN',
        message: `Session ${id} closed with outcome: ${outcome.toUpperCase()}`,
        source: 'USER'
      }, ...state.systemLogs]
    };
  }),

  addMessage: (sessionId, message) => set((state) => {
    const session = state.sessions[sessionId];
    if (!session) return state;

    return {
      sessions: {
        ...state.sessions,
        [sessionId]: {
          ...session,
          messages: [...session.messages, message],
          lastUpdated: Date.now()
        }
      }
    };
  }),

  setFeedback: (sessionId, messageId, feedback, details) => set((state) => {
    const session = state.sessions[sessionId];
    if (!session) return state;

    const updatedMessages = session.messages.map(msg =>
      msg.id === messageId ? { ...msg, feedback, feedbackDetails: details } : msg
    );

    // Add log only for negative feedback to reduce noise
    let newLogs = state.systemLogs;
    if (feedback === 'negative') {
      newLogs = [{
        id: `log-fb-${Date.now()}`,
        timestamp: Date.now(),
        type: 'WARN',
        message: `Negative feedback in session ${sessionId}: ${details || 'No details'}`,
        source: 'USER'
      }, ...state.systemLogs];
    }

    return {
      sessions: {
        ...state.sessions,
        [sessionId]: {
          ...session,
          messages: updatedMessages
        }
      },
      systemLogs: newLogs
    };
  }),

  updateJourneyStage: (sessionId, stage) => set((state) => ({
    sessions: {
      ...state.sessions,
      [sessionId]: { ...state.sessions[sessionId], journeyStage: stage }
    }
  })),

  updateAnalysis: (partial) => set((state) => {
    const currentSessionId = state.currentSessionId;
    if (!currentSessionId) return state;

    const currentSession = state.sessions[currentSessionId];
    if (!currentSession) return state;

    // Merge analysis
    const updatedAnalysis = { ...state.currentAnalysis, ...partial, lastUpdated: Date.now() };

    // Logic for Auto-Stage Detection
    let updatedJourneyStage = currentSession.journeyStage;

    // If AI suggests a stage change with high confidence (> 70%), apply it
    if (partial.journeyStageAnalysis) {
      const { currentStage: aiStage, confidence } = partial.journeyStageAnalysis;
      if (aiStage && confidence > 0.7 && aiStage !== updatedJourneyStage) {
        console.log(`[Auto-Stage] Switching from ${updatedJourneyStage} to ${aiStage} (Confidence: ${confidence})`);
        updatedJourneyStage = aiStage;
      }
    }

    const updatedSessions = { ...state.sessions };
    updatedSessions[currentSessionId] = {
      ...updatedSessions[currentSessionId],
      analysisState: updatedAnalysis,
      journeyStage: updatedJourneyStage // Commit the stage change
    };

    return {
      currentAnalysis: updatedAnalysis,
      sessions: updatedSessions
    };
  }),

  setAnalyzing: (isAnalyzing) => set((state) => ({
    currentAnalysis: { ...state.currentAnalysis, isAnalyzing }
  })),

  // --- Knowledge Base Actions ---

  addNugget: (nugget) => set((state) => ({
    knowledgeBase: {
      ...state.knowledgeBase,
      nuggets: [nugget, ...state.knowledgeBase.nuggets]
    },
    systemLogs: [{
      id: `log-kb-${Date.now()}`,
      timestamp: Date.now(),
      type: 'INFO',
      message: `Knowledge Nugget added: ${nugget.title}`,
      source: 'USER'
    }, ...state.systemLogs]
  })),

  removeNugget: (id) => set((state) => ({
    knowledgeBase: {
      ...state.knowledgeBase,
      nuggets: state.knowledgeBase.nuggets.filter(n => n.id !== id)
    }
  })),

  addStandard: (standard) => set((state) => ({
    knowledgeBase: {
      ...state.knowledgeBase,
      standards: [standard, ...state.knowledgeBase.standards]
    },
    systemLogs: [{
      id: `log-std-${Date.now()}`,
      timestamp: Date.now(),
      type: 'INFO',
      message: `Golden Standard added to ${standard.category}`,
      source: 'USER'
    }, ...state.systemLogs]
  })),

  removeStandard: (id) => set((state) => ({
    knowledgeBase: {
      ...state.knowledgeBase,
      standards: state.knowledgeBase.standards.filter(s => s.id !== id)
    }
  }))

}));
