


import React, { useState, useEffect } from 'react';
import { useStore } from '../store';
import PsychometricChart from './RadarChart';
import ModuleFeedback from './ModuleFeedback';
import {
  Dna,
  Activity,
  Brain,
  Zap,
  GitBranch,
  BookOpen,
  Users,
  ChevronDown,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  Lightbulb,
  Target,
  Rocket,
  ArrowDown,
  Compass,
  Map,
  Fingerprint
} from 'lucide-react';

interface AccordionCardProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  isUpdated?: boolean;
  delay?: number;
  moduleName?: string;
  sessionId?: string;
  userInput?: string;
  moduleOutput?: string;
}

const AccordionCard: React.FC<AccordionCardProps> = ({
  title,
  icon,
  children,
  defaultOpen = true,
  isUpdated,
  delay = 0,
  moduleName,
  sessionId,
  userInput,
  moduleOutput
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [highlight, setHighlight] = useState(false);

  useEffect(() => {
    if (isUpdated) {
      const timer1 = setTimeout(() => setHighlight(true), delay);
      const timer2 = setTimeout(() => setHighlight(false), delay + 2000);
      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
      };
    }
  }, [isUpdated, delay]);

  return (
    <div className={`mb-3 border rounded-lg transition-all duration-700 ${highlight
      ? 'border-tesla-red dark:bg-zinc-900 bg-zinc-50 shadow-[0_0_15px_rgba(227,25,55,0.2)]'
      : 'dark:border-zinc-800/60 border-zinc-300 dark:bg-zinc-900/40 bg-white'
      } backdrop-blur-sm overflow-hidden group`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 dark:hover:bg-zinc-800/50 hover:bg-zinc-100 transition-colors outline-none"
      >
        <div className={`flex items-center gap-2 font-medium uppercase text-xs tracking-wider transition-colors ${highlight ? 'dark:text-white text-black' : 'text-tesla-red'
          }`}>
          {icon}
          <span>{title}</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Module Feedback Buttons */}
          {moduleName && (
            <div onClick={(e) => e.stopPropagation()}>
              <ModuleFeedback
                sessionId={sessionId}
                moduleName={moduleName}
                userInput={userInput}
                moduleOutput={moduleOutput || ''}
              />
            </div>
          )}
          <div className={`text-zinc-500 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}>
            <ChevronDown size={14} />
          </div>
        </div>
      </button>

      <div
        className={`transition-all duration-500 ease-in-out overflow-hidden ${isOpen ? 'max-h-[1200px] opacity-100' : 'max-h-0 opacity-0'
          }`}
      >
        <div className="p-3 pt-0 dark:text-zinc-300 text-zinc-600 text-sm dark:border-zinc-800/30 border-zinc-200 mt-1">
          {children}
        </div>
      </div>
    </div>
  );
};

const AnalysisPanel: React.FC = () => {
  const { currentAnalysis, t, currentSessionId, sessions } = useStore();
  const [prevUpdated, setPrevUpdated] = useState(0);
  const [isNewData, setIsNewData] = useState(false);

  const {
    m1_dna,
    m2_indicators,
    m3_psychometrics,
    m4_motivation,
    m5_predictions,
    m6_playbook,
    m7_decision,
    isAnalyzing
  } = currentAnalysis;

  // Build conversation summary for Slow Path feedback context
  const currentSession = currentSessionId ? sessions[currentSessionId] : null;
  const conversationSummary = currentSession?.messages
    .slice(-6)  // Last 6 messages for context
    .map(m => `${m.role.toUpperCase()}: ${m.content}`)
    .join('\n') || '';

  useEffect(() => {
    if (currentAnalysis.lastUpdated > prevUpdated) {
      setIsNewData(true);
      setPrevUpdated(currentAnalysis.lastUpdated);
      const timer = setTimeout(() => setIsNewData(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [currentAnalysis.lastUpdated, prevUpdated]);

  return (
    <div className="h-full flex flex-col dark:bg-black bg-white dark:border-l dark:border-zinc-800 border-l border-zinc-200 w-full transition-colors duration-300">
      {/* Header */}
      <div className="p-4 border-b dark:border-zinc-800 border-zinc-200 flex justify-between items-center dark:bg-zinc-900/20 bg-zinc-50 backdrop-blur">
        <h2 className="dark:text-zinc-400 text-zinc-500 text-xs uppercase tracking-widest font-bold flex items-center gap-2">
          <Activity size={14} className={isAnalyzing ? "animate-pulse text-tesla-red" : ""} />
          {t('analysisStream')}
        </h2>
        {isAnalyzing && (
          <span className="text-[10px] font-mono text-tesla-red animate-pulse">{t('processing')}</span>
        )}
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">

        {/* M1: DNA */}
        <AccordionCard
          title="M1: DNA Client"
          icon={<Dna size={14} />}
          isUpdated={isNewData}
          delay={0}
          moduleName="slow_path_m1_dna"
          sessionId={currentSessionId || undefined}
          userInput={conversationSummary}
          moduleOutput={JSON.stringify(m1_dna)}
        >
          {/* Enhanced AI Summary */}
          <div className="bg-gradient-to-br dark:from-zinc-900 dark:to-zinc-900/50 from-zinc-100 to-white rounded-lg border dark:border-tesla-red/30 border-zinc-300 p-4 mb-3 relative overflow-hidden shadow-inner">
            <div className="absolute top-0 right-0 p-2 opacity-10">
              <Dna size={40} />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <Sparkles size={12} className="text-tesla-red animate-pulse" />
              <span className="text-[10px] font-bold dark:text-zinc-400 text-zinc-500 uppercase tracking-wider">{t('dnaSummary')}</span>
            </div>
            <p className="text-xs dark:text-zinc-100 text-zinc-800 leading-relaxed font-medium font-sans">
              {m1_dna.summary}
            </p>
          </div>

          {/* Attribute Grid */}
          <div className="grid grid-cols-2 gap-2 text-[10px] uppercase tracking-wide font-mono">
            <div className="dark:bg-zinc-950 bg-zinc-50 p-2 rounded border dark:border-zinc-800/50 border-zinc-200 flex flex-col justify-between group hover:border-zinc-400 dark:hover:border-zinc-700 transition-colors">
              <span className="block dark:text-zinc-500 text-zinc-400 mb-1 text-[9px]">Motivation</span>
              <span className="dark:text-zinc-300 text-zinc-800 font-bold truncate group-hover:text-black dark:group-hover:text-white transition-colors" title={m1_dna.mainMotivation}>
                {m1_dna.mainMotivation}
              </span>
            </div>
            <div className="dark:bg-zinc-950 bg-zinc-50 p-2 rounded border dark:border-zinc-800/50 border-zinc-200 flex flex-col justify-between group hover:border-zinc-400 dark:hover:border-zinc-700 transition-colors">
              <span className="block dark:text-zinc-500 text-zinc-400 mb-1 text-[9px]">Style</span>
              <span className="dark:text-zinc-300 text-zinc-800 font-bold truncate group-hover:text-black dark:group-hover:text-white transition-colors" title={m1_dna.communicationStyle}>
                {m1_dna.communicationStyle}
              </span>
            </div>
          </div>
        </AccordionCard>

        {/* M2: Indicators */}
        <AccordionCard
          title="M2: Tactical Indicators"
          icon={<Activity size={14} />}
          isUpdated={isNewData}
          delay={100}
          moduleName="slow_path_m2_indicators"
          sessionId={currentSessionId || undefined}
          userInput={conversationSummary}
          moduleOutput={JSON.stringify(m2_indicators)}
        >
          <div className="mb-4">
            <div className="flex justify-between text-xs mb-1.5">
              <span className="dark:text-zinc-400 text-zinc-500">Purchase Temperature</span>
              <span className={`font-mono font-bold ${m2_indicators.purchaseTemperature > 70 ? 'text-green-500 dark:text-green-400' : m2_indicators.purchaseTemperature > 40 ? 'text-yellow-500 dark:text-yellow-400' : 'text-red-500 dark:text-red-400'}`}>
                {m2_indicators.purchaseTemperature}%
              </span>
            </div>
            <div className="h-2 w-full dark:bg-zinc-950 bg-zinc-200 rounded-full overflow-hidden border dark:border-zinc-800 border-zinc-300">
              <div
                className={`h-full transition-all duration-1000 ease-out ${m2_indicators.purchaseTemperature > 70 ? 'bg-gradient-to-r from-green-600 to-green-400' :
                  m2_indicators.purchaseTemperature > 40 ? 'bg-gradient-to-r from-yellow-600 to-yellow-400' :
                    'bg-gradient-to-r from-red-600 to-red-400'
                  }`}
                style={{ width: `${m2_indicators.purchaseTemperature}%` }}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className={`flex items-center justify-between px-2 py-1.5 rounded border ${m2_indicators.churnRisk === 'High'
              ? 'dark:bg-red-900/10 bg-red-50 dark:border-red-900/30 border-red-200 text-red-500 dark:text-red-400'
              : 'dark:bg-zinc-900 bg-zinc-50 dark:border-zinc-800 border-zinc-200 dark:text-zinc-400 text-zinc-600'
              }`}>
              <span>Churn Risk</span>
              {m2_indicators.churnRisk === 'High' && <AlertTriangle size={12} />}
              <span className="font-bold">{m2_indicators.churnRisk}</span>
            </div>
            <div className="flex items-center justify-between px-2 py-1.5 rounded border dark:bg-zinc-900 bg-zinc-50 dark:border-zinc-800 border-zinc-200 dark:text-zinc-400 text-zinc-600">
              <span>Fun Drive</span>
              <span className="font-bold">{m2_indicators.funDriveRisk}</span>
            </div>
          </div>
        </AccordionCard>

        {/* M3: Psychometrics */}
        <AccordionCard
          title="M3: Psychometrics"
          icon={<Brain size={14} />}
          isUpdated={isNewData}
          delay={200}
          moduleName="slow_path_m3_psychometrics"
          sessionId={currentSessionId || undefined}
          userInput={conversationSummary}
          moduleOutput={JSON.stringify(m3_psychometrics)}
        >
          <div className="flex items-center justify-between mb-2 text-xs px-1">
            <span className="text-zinc-500">Dominant Trait</span>
            <span className="font-bold text-tesla-red bg-tesla-red/10 px-2 py-0.5 rounded-full border border-tesla-red/20">
              {Object.entries(m3_psychometrics.disc).reduce((a, b) => a[1] > b[1] ? a : b)[0].toUpperCase()}
            </span>
          </div>
          <div className="-ml-4 h-48 min-h-[200px]">
            <PsychometricChart data={m3_psychometrics} />
          </div>

          {/* Schwartz Values Mini-Bar */}
          <div className="mt-4 space-y-2 pt-4 border-t dark:border-zinc-800 border-zinc-200">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2 mb-2">
              <Compass size={10} /> Schwartz Values
            </div>
            {Object.entries(m3_psychometrics.schwartz || {}).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between text-[10px]">
                <span className="text-zinc-500 capitalize truncate w-24">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                <div className="flex-1 mx-2 h-1.5 bg-zinc-900 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-600 rounded-full" style={{ width: `${value}%` }}></div>
                </div>
                <span className="font-mono text-zinc-300 w-6 text-right">{value}</span>
              </div>
            ))}
          </div>
        </AccordionCard>

        {/* M4: Motivation */}
        <AccordionCard
          title="M4: Deep Motivation"
          icon={<Zap size={14} />}
          isUpdated={isNewData}
          delay={300}
          moduleName="slow_path_m4_motivation"
          sessionId={currentSessionId || undefined}
          userInput={conversationSummary}
          moduleOutput={JSON.stringify(m4_motivation)}
        >
          <div className="flex flex-col gap-3">
            {/* Insights (Problem) */}
            {m4_motivation.keyInsights.length > 0 && (
              <div className="dark:bg-yellow-950/10 bg-yellow-50 rounded-lg p-2 border dark:border-yellow-900/30 border-yellow-200">
                <div className="text-[10px] font-bold dark:text-yellow-600 text-yellow-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Lightbulb size={10} className="text-yellow-500" />
                  <span>{t('coreDrivers')}</span>
                </div>
                <div className="space-y-1.5">
                  {m4_motivation.keyInsights.slice(0, 2).map((insight, i) => (
                    <div key={i} className="flex gap-2 items-start">
                      <div className="w-1 h-1 rounded-full bg-yellow-600 mt-1.5 shrink-0"></div>
                      <span className="text-xs dark:text-zinc-300 text-zinc-800 leading-snug">{insight}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Hooks (Solution) */}
            {m4_motivation.teslaHooks.length > 0 && (
              <div className="dark:bg-red-950/10 bg-red-50 rounded-lg p-2 border dark:border-red-900/30 border-red-200">
                <div className="text-[10px] font-bold text-tesla-red uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Rocket size={10} />
                  <span>{t('teslaAnchors')}</span>
                </div>
                <div className="space-y-1.5">
                  {m4_motivation.teslaHooks.slice(0, 3).map((hook, i) => (
                    <div key={i} className="flex gap-2 text-xs items-start group cursor-default">
                      <CheckCircle2 size={12} className="dark:text-zinc-600 text-zinc-400 group-hover:text-tesla-red transition-colors shrink-0 mt-0.5" />
                      <span className="dark:text-zinc-300 text-zinc-800 group-hover:text-black dark:group-hover:text-white transition-colors">{hook}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </AccordionCard>

        {/* M5: Predictions */}
        <AccordionCard
          title="M5: Predictive Paths"
          icon={<GitBranch size={14} />}
          isUpdated={isNewData}
          delay={400}
          moduleName="slow_path_m5_predictions"
          sessionId={currentSessionId || undefined}
          userInput={conversationSummary}
          moduleOutput={JSON.stringify(m5_predictions)}
        >
          <div className="mb-3 text-[10px] uppercase tracking-wider text-zinc-500 flex justify-between border-b dark:border-zinc-800 border-zinc-200 pb-1">
            <span>{t('estTimeline')}</span>
            <span className="dark:text-white text-zinc-900 font-mono">{m5_predictions.estimatedTimeline}</span>
          </div>
          <div className="space-y-3">
            {m5_predictions.scenarios.slice(0, 2).map((s, i) => (
              <div key={i} className="relative">
                <div className="flex justify-between text-xs mb-1 z-10 relative">
                  <span className="dark:text-zinc-200 text-zinc-800 font-medium">{s.name}</span>
                  <span className="font-mono text-tesla-red">{(s.probability * 100).toFixed(0)}%</span>
                </div>
                <div className="h-1 w-full dark:bg-zinc-900 bg-zinc-200 rounded-full overflow-hidden mb-1">
                  <div
                    className="h-full bg-zinc-500 dark:bg-zinc-700"
                    style={{ width: `${s.probability * 100}%` }}
                  />
                </div>
                <p className="text-[10px] text-zinc-500 leading-tight">{s.description}</p>
              </div>
            ))}
          </div>
        </AccordionCard>

        {/* M6: Playbook */}
        <AccordionCard
          title="M6: Playbook & SSR 2.0"
          icon={<BookOpen size={14} />}
          isUpdated={isNewData}
          delay={500}
          moduleName="slow_path_m6_playbook"
          sessionId={currentSessionId || undefined}
          userInput={conversationSummary}
          moduleOutput={JSON.stringify(m6_playbook)}
        >
          {/* SSR 2.0 SECTION */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-zinc-800">
              <Map size={12} className="text-blue-400" />
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">SSR 2.0: Strategic Synthesis</span>
            </div>
            {m6_playbook.ssr && m6_playbook.ssr.length > 0 ? (
              <div className="space-y-3">
                {m6_playbook.ssr.map((entry, i) => (
                  <div key={i} className="bg-zinc-900/50 border border-zinc-800 p-3 rounded-lg relative group hover:border-zinc-600 transition-colors">
                    {/* Fact Chip */}
                    <div className="absolute -top-2 -right-2 bg-zinc-800 text-zinc-400 text-[9px] px-2 py-0.5 rounded-full border border-zinc-700 shadow-sm flex items-center gap-1">
                      <Fingerprint size={8} />
                      {entry.fact}
                    </div>

                    <div className="mt-1 space-y-2">
                      <div className="text-xs font-medium text-white">{entry.solution}</div>
                      <div className="flex gap-2 text-[10px] items-start">
                        <span className="text-zinc-500 shrink-0">IMP:</span>
                        <span className="text-zinc-400 leading-tight">{entry.implication}</span>
                      </div>
                      <div className="flex gap-2 text-[10px] items-start">
                        <span className="text-blue-500 shrink-0 font-bold">ACT:</span>
                        <span className="text-blue-200 leading-tight">{entry.action}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-zinc-600 text-[10px] italic">
                Gathering data for synthesis...
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-zinc-800">
            <Target size={12} className="text-tesla-red" />
            <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Tactical Sequence</span>
          </div>

          {m6_playbook.suggestedTactics.length > 0 ? (
            <div className="relative space-y-4 pl-2 py-1">
              {/* Vertical Tactical Line */}
              <div className="absolute left-[11px] top-2 bottom-2 w-px border-l border-dashed dark:border-zinc-700 border-zinc-300"></div>

              {m6_playbook.suggestedTactics.slice(0, 4).map((tactic, i) => (
                <div key={i} className="relative flex gap-3 items-start group">
                  {/* Number Node */}
                  <div className={`relative z-10 shrink-0 w-5 h-5 rounded-full border transition-all flex items-center justify-center text-[9px] font-mono ${i === 0
                    ? 'bg-tesla-red text-white border-tesla-red shadow-[0_0_10px_rgba(227,25,55,0.4)]'
                    : 'dark:bg-zinc-950 bg-white text-zinc-500 dark:border-zinc-700 border-zinc-300 group-hover:border-zinc-500'
                    }`}>
                    {i === 0 ? <Target size={10} /> : i + 1}
                  </div>
                  {/* Content */}
                  <div className={`p-2.5 rounded border transition-all w-full ${i === 0
                    ? 'dark:bg-zinc-800/80 bg-zinc-100 dark:border-zinc-600 border-zinc-300 shadow-sm'
                    : 'dark:bg-zinc-900/30 bg-zinc-50 dark:border-zinc-800/50 border-zinc-200 hover:bg-white dark:hover:bg-zinc-900 hover:border-zinc-400 dark:hover:border-zinc-700'
                    }`}>
                    <p className={`text-xs leading-snug ${i === 0 ? 'dark:text-white text-zinc-900 font-medium' : 'dark:text-zinc-300 text-zinc-700'}`}>
                      {tactic}
                    </p>
                  </div>
                </div>
              ))}

              {/* End Node */}
              <div className="relative flex gap-3 items-center opacity-50">
                <div className="relative z-10 shrink-0 w-5 h-5 rounded-full dark:bg-zinc-900 bg-zinc-100 border dark:border-zinc-800 border-zinc-300 flex items-center justify-center">
                  <div className="w-1.5 h-1.5 rounded-full bg-zinc-500 dark:bg-zinc-700"></div>
                </div>
                <span className="text-[9px] text-zinc-600 uppercase tracking-widest">Close</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-4 text-zinc-600 gap-2">
              <Target size={24} className="opacity-20" />
              <span className="text-[10px] italic">Generating strategic sequence...</span>
            </div>
          )}
        </AccordionCard>

        {/* M7: Decision */}
        <AccordionCard
          title="M7: Decision Vectors"
          icon={<Users size={14} />}
          isUpdated={isNewData}
          delay={600}
          moduleName="slow_path_m7_decision"
          sessionId={currentSessionId || undefined}
          userInput={conversationSummary}
          moduleOutput={JSON.stringify(m7_decision)}
        >
          <div className="space-y-2 text-xs">
            <div className="flex flex-col gap-1">
              <span className="text-zinc-500 uppercase text-[10px] tracking-wider">{t('decisionMaker')}</span>
              <span className="dark:text-white text-zinc-900 dark:bg-zinc-800 bg-zinc-200 px-2 py-1 rounded border dark:border-zinc-700 border-zinc-300 inline-block self-start">
                {m7_decision.decisionMaker}
              </span>
            </div>
            <div className="flex flex-col gap-1 pt-2 border-t dark:border-zinc-800 border-zinc-200">
              <span className="text-zinc-500 uppercase text-[10px] tracking-wider">{t('criticalPath')}</span>
              <span className="dark:text-zinc-300 text-zinc-800">{m7_decision.criticalPath}</span>
            </div>
          </div>
        </AccordionCard>

        <div className="text-[10px] text-zinc-700 dark:text-zinc-700 text-center mt-6 pb-4 font-mono">
          ULTRA v3.0 • CONFIDENTIAL
        </div>
      </div>
    </div>
  );
};

export default AnalysisPanel;