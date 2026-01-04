

export enum JourneyStage {
  DISCOVERY = "DISCOVERY",
  DEMO = "DEMO",
  OBJECTION_HANDLING = "OBJECTION_HANDLING",
  FINANCING = "FINANCING",
  CLOSING = "CLOSING",
  DELIVERY = "DELIVERY"
}

export type ViewState = 'dashboard' | 'chat' | 'admin' | 'dojo';
export type Language = 'PL' | 'EN';
export type Theme = 'dark' | 'light';

export interface Message {
  id: string;
  role: 'user' | 'ai' | 'system';
  content: string;
  timestamp: number;
  
  // AI Metadata
  confidence?: number; 
  confidenceReason?: string; // Text explanation for confidence
  clientStyle?: string; // e.g., "Techniczny", "Relacyjny"
  
  // UI Sections
  feedback?: 'positive' | 'negative' | null;
  feedbackDetails?: string;
  
  // Yellow Box: Questions for the salesperson to consider/observe
  contextNeeds?: string[]; 
  
  // Purple Box: Suggested clickable questions/actions
  suggestedActions?: string[]; 
}

// --- M1: DNA Client ---
export interface ModuleDNA {
  summary: string;
  mainMotivation: string;
  communicationStyle: 'Analytical' | 'Driver' | 'Amiable' | 'Expressive';
}

// --- M2: Tactical Indicators ---
export interface ModuleIndicators {
  purchaseTemperature: number; // 0-100
  churnRisk: 'Low' | 'Medium' | 'High';
  funDriveRisk: 'Low' | 'Medium' | 'High';
}

// --- M3: Psychometric Profile ---
export interface ModulePsychometrics {
  disc: {
    dominance: number;
    influence: number;
    steadiness: number;
    compliance: number;
  };
  bigFive: {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    neuroticism: number;
  };
  // ADDED: Schwartz Values for deeper motivation analysis
  schwartz: {
    opennessToChange: number; // Hedonism, Stimulation, Self-direction
    selfEnhancement: number; // Achievement, Power
    conservation: number; // Security, Conformity, Tradition
    selfTranscendence: number; // Benevolence, Universalism
  };
}

// --- M4: Deep Motivation ---
export interface ModuleMotivation {
  keyInsights: string[];
  teslaHooks: string[];
}

// --- M5: Predictive Paths ---
export interface Scenario {
  name: string;
  probability: number;
  description: string;
}
export interface ModulePredictions {
  scenarios: Scenario[];
  estimatedTimeline: string;
}

// --- M6: Strategic Playbook (SSR 2.0) ---
export interface SSREntry {
  fact: string;         // e.g., "Has 2 kids and wife"
  implication: string;  // e.g., "Safety is #1 priority, Wife is the decision maker (CFO)"
  solution: string;     // e.g., "Focus on 5-star safety, Isofix, Entertainment for kids"
  action: string;       // e.g., "Invite wife to test drive, show crash test videos"
}

export interface ModulePlaybook {
  suggestedTactics: string[];
  ssr: SSREntry[]; // The Google-like Analysis Table
}

// --- M7: Decision Vectors ---
export interface ModuleDecision {
  decisionMaker: string;
  influencers: string[];
  criticalPath: string;
}

// --- AUTO-STAGE DETECTION ---
export interface JourneyStageAnalysis {
  currentStage: JourneyStage;
  confidence: number;
  reasoning: string;
}

// The Complete Analysis Object
export interface AnalysisState {
  m1_dna: ModuleDNA;
  m2_indicators: ModuleIndicators;
  m3_psychometrics: ModulePsychometrics;
  m4_motivation: ModuleMotivation;
  m5_predictions: ModulePredictions;
  m6_playbook: ModulePlaybook;
  m7_decision: ModuleDecision;
  journeyStageAnalysis: JourneyStageAnalysis;
  isAnalyzing: boolean;
  lastUpdated: number;
}

export const INITIAL_ANALYSIS: AnalysisState = {
  m1_dna: { summary: "Awaiting data...", mainMotivation: "Unknown", communicationStyle: "Analytical" },
  m2_indicators: { purchaseTemperature: 0, churnRisk: "Low", funDriveRisk: "Low" },
  m3_psychometrics: {
    disc: { dominance: 50, influence: 50, steadiness: 50, compliance: 50 },
    bigFive: { openness: 50, conscientiousness: 50, extraversion: 50, agreeableness: 50, neuroticism: 50 },
    schwartz: { opennessToChange: 50, selfEnhancement: 50, conservation: 50, selfTranscendence: 50 }
  },
  m4_motivation: { keyInsights: [], teslaHooks: [] },
  m5_predictions: { scenarios: [], estimatedTimeline: "Unknown" },
  m6_playbook: { suggestedTactics: [], ssr: [] },
  m7_decision: { decisionMaker: "Unknown", influencers: [], criticalPath: "Unknown" },
  journeyStageAnalysis: { currentStage: JourneyStage.DISCOVERY, confidence: 0, reasoning: "Initializing..." },
  isAnalyzing: false,
  lastUpdated: Date.now()
};

export interface Session {
  id: string;
  createdAt: number;
  status: 'active' | 'closed'; // New field
  outcome: 'sale' | 'no_sale' | null; // New field
  journeyStage: JourneyStage;
  messages: Message[];
  lastUpdated: number;
  analysisState: AnalysisState; // Persistent analysis state per session
}

// --- ADMIN / DOJO TYPES ---
export interface RagNugget {
  id: string;
  title: string;
  content: string;
  keywords: string[];
  language: string;
}

export interface GoldenStandard {
  id: string;
  category: 'financial' | 'competitive' | 'technical' | 'objection';
  context: string;
  response: string;
  tags: string[];
  language: string;
  date: string;
}

export interface LogEntry {
  id: string;
  timestamp: number;
  type: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS';
  message: string;
  source: 'SYSTEM' | 'USER' | 'AI';
}

// --- GOTHAM MODULE (v4.0) ---

export interface BurningHouseScore {
  total_annual_loss: number;
  ev_annual_cost: number;
  annual_savings: number;
  dotacja_naszeauto: number;
  net_benefit_3_years: number;
  urgency_score: number; // 0-100
  urgency_message: string;
}

export interface CEPiKMarket {
  region: string;
  total_ev_registrations_2024: number;
  growth_rate_yoy: number;
  top_brand: string;
  trend: string;
}

export interface GothamData {
  burning_house_score: BurningHouseScore;
  cepik_market: CEPiKMarket | null;
  market_context_text: string;
  sales_hooks: string[];
  urgency_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface MarketOverview {
  total_expiring_leases: number;
  competitor_breakdown: {
    [key: string]: number;
  };
  opportunity_score: number;
  urgency_level: string;
  insight: string;
  region: string;
  last_updated: string;
  error?: string;
}
