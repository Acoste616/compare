import React from 'react';
import { Flame, TrendingDown, Zap, DollarSign, AlertTriangle } from 'lucide-react';
import { GothamData } from '../types';

interface BurningHouseScoreProps {
  data: GothamData | null;
}

// DEMO DATA: Used when real data is unavailable
const DEMO_DATA: GothamData = {
  burning_house_score: {
    total_annual_loss: 24000,
    ev_annual_cost: 1800,
    annual_savings: 22200,
    dotacja_naszeauto: 27000,
    net_benefit_3_years: 93600,
    urgency_score: 78,
    urgency_message: "⚠️ TRYB DEMO - Dane testowe. Wprowadź dane klienta aby zobaczyć rzeczywiste obliczenia.",
    depreciation_loss_ice: 12000,
    depreciation_loss_ev: 19000,
    depreciation_advantage: -7000
  },
  urgency_level: 'HIGH',
  sales_hooks: [
    "💡 DEMO: Klient traci ~24,000 PLN rocznie na paliwie",
    "💡 DEMO: Dotacja NaszEauto: 27,000 PLN",
    "💡 DEMO: Wprowadź rzeczywiste dane klienta powyżej"
  ],
  cepik_market: null,
  market_context_text: "TRYB DEMONSTRACYJNY",
  opportunity_score: null
};

const BurningHouseScore: React.FC<BurningHouseScoreProps> = ({ data }) => {
  // V4.0 FIX: If no data or zeroed data, show DEMO MODE
  const isDemo = !data || !data.burning_house_score || data.burning_house_score.urgency_score === 0;
  const displayData = isDemo ? DEMO_DATA : data;

  const { burning_house_score, urgency_level, sales_hooks } = displayData;

  // Determine urgency styling
  const getUrgencyStyles = () => {
    // If DEMO mode, use special styling
    if (isDemo) {
      return {
        bg: 'bg-purple-950/50',
        border: 'border-purple-900',
        text: 'text-purple-400',
        glow: 'shadow-[0_0_20px_rgba(168,85,247,0.2)]',
        pulse: 'animate-pulse'
      };
    }

    switch (urgency_level) {
      case 'CRITICAL':
        return {
          bg: 'bg-red-950/50',
          border: 'border-red-900',
          text: 'text-red-400',
          glow: 'shadow-[0_0_30px_rgba(239,68,68,0.3)]',
          pulse: 'animate-pulse'
        };
      case 'HIGH':
        return {
          bg: 'bg-orange-950/50',
          border: 'border-orange-900',
          text: 'text-orange-400',
          glow: 'shadow-[0_0_20px_rgba(251,146,60,0.2)]',
          pulse: ''
        };
      case 'MEDIUM':
        return {
          bg: 'bg-yellow-950/50',
          border: 'border-yellow-900',
          text: 'text-yellow-400',
          glow: 'shadow-[0_0_15px_rgba(250,204,21,0.15)]',
          pulse: ''
        };
      default:
        return {
          bg: 'bg-zinc-900/50',
          border: 'border-zinc-800',
          text: 'text-zinc-400',
          glow: '',
          pulse: ''
        };
    }
  };

  const styles = getUrgencyStyles();

  return (
    <div
      className={`${styles.bg} border ${styles.border} rounded-xl p-6 ${styles.glow} ${styles.pulse} transition-all duration-500 animate-[fadeIn_0.5s_ease-in]`}
      style={{
        animation: 'fadeIn 0.5s ease-in'
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Flame size={20} className={`${styles.text} ${urgency_level === 'CRITICAL' ? 'animate-pulse' : ''}`} />
          <h3 className={`font-bold ${styles.text} tracking-tight`}>
            🔥 GOTHAM INTELLIGENCE
          </h3>
        </div>
        <div className={`text-xs font-mono px-2 py-1 rounded ${styles.bg} ${styles.text} border ${styles.border}`}>
          {urgency_level}
        </div>
      </div>

      {/* Urgency Message */}
      <div className={`mb-4 p-3 rounded-lg bg-black/30 border ${styles.border}`}>
        <p className={`text-sm font-medium ${styles.text}`}>
          {burning_house_score.urgency_message}
        </p>
      </div>

      {/* Financial Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Annual Loss */}
        <div className="bg-black/30 rounded-lg p-3 border border-zinc-800">
          <div className="flex items-center gap-1 mb-1">
            <TrendingDown size={12} className="text-red-400" />
            <span className="text-[10px] text-zinc-500 uppercase tracking-wide">Roczna Strata</span>
          </div>
          <div className="text-lg font-bold font-mono text-red-400">
            {burning_house_score.total_annual_loss.toLocaleString('pl-PL')} PLN
          </div>
        </div>

        {/* Annual Savings */}
        <div className="bg-black/30 rounded-lg p-3 border border-zinc-800">
          <div className="flex items-center gap-1 mb-1">
            <Zap size={12} className="text-green-400" />
            <span className="text-[10px] text-zinc-500 uppercase tracking-wide">Oszczędności</span>
          </div>
          <div className="text-lg font-bold font-mono text-green-400">
            {burning_house_score.annual_savings.toLocaleString('pl-PL')} PLN
          </div>
        </div>

        {/* Dotacja */}
        <div className="bg-black/30 rounded-lg p-3 border border-zinc-800">
          <div className="flex items-center gap-1 mb-1">
            <DollarSign size={12} className="text-blue-400" />
            <span className="text-[10px] text-zinc-500 uppercase tracking-wide">Dotacja NaszEauto</span>
          </div>
          <div className="text-lg font-bold font-mono text-blue-400">
            {burning_house_score.dotacja_naszeauto.toLocaleString('pl-PL')} PLN
          </div>
        </div>

        {/* 3-Year Benefit */}
        <div className="bg-black/30 rounded-lg p-3 border border-zinc-800">
          <div className="flex items-center gap-1 mb-1">
            <TrendingDown size={12} className="text-purple-400" />
            <span className="text-[10px] text-zinc-500 uppercase tracking-wide">Zysk 3 lata</span>
          </div>
          <div className="text-lg font-bold font-mono text-purple-400">
            {burning_house_score.net_benefit_3_years.toLocaleString('pl-PL')} PLN
          </div>
        </div>
      </div>

      {/* Urgency Score Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-zinc-500 uppercase tracking-wide">Urgency Score</span>
          <span className={`text-sm font-mono font-bold ${styles.text}`}>
            {burning_house_score.urgency_score}/100
          </span>
        </div>
        <div className="h-2 bg-zinc-900 rounded-full overflow-hidden border border-zinc-800">
          <div
            className={`h-full transition-all duration-1000 ${urgency_level === 'CRITICAL' ? 'bg-gradient-to-r from-red-600 to-red-500' :
                urgency_level === 'HIGH' ? 'bg-gradient-to-r from-orange-600 to-orange-500' :
                  urgency_level === 'MEDIUM' ? 'bg-gradient-to-r from-yellow-600 to-yellow-500' :
                    'bg-gradient-to-r from-zinc-600 to-zinc-500'
              }`}
            style={{ width: `${burning_house_score.urgency_score}%` }}
          />
        </div>
      </div>

      {/* Sales Hooks */}
      {sales_hooks && sales_hooks.length > 0 && (
        <div className="bg-black/30 rounded-lg p-3 border border-zinc-800">
          <div className="flex items-center gap-1 mb-2">
            <AlertTriangle size={12} className="text-amber-400" />
            <span className="text-[10px] text-zinc-500 uppercase tracking-wide font-bold">Sales Hooks</span>
          </div>
          <ul className="space-y-1">
            {sales_hooks.map((hook, idx) => (
              <li key={idx} className="text-xs text-zinc-300 flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">•</span>
                <span>{hook}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-zinc-800">
        <div className="flex items-center justify-between">
          <span className="text-[9px] text-zinc-600 uppercase tracking-wider">
            Powered by GOTHAM v4.0
          </span>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
            <span className="text-[9px] text-green-500">Live</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BurningHouseScore;
