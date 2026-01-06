import React, { useEffect, useState } from 'react';
import { Target, TrendingUp, Users, AlertCircle, RefreshCw } from 'lucide-react';
import { MarketOverview } from '../types';

interface LeadSniperWidgetProps {
  region?: string;
}

const LeadSniperWidget: React.FC<LeadSniperWidgetProps> = ({ region = 'ŚLĄSKIE' }) => {
  const [data, setData] = useState<MarketOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMarketOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`http://localhost:8000/api/v1/gotham/market-overview?region=${region}`);
      const result = await response.json();

      if (result.error) {
        setError(result.error);
      }

      setData(result);
    } catch (err) {
      setError('Failed to fetch market data');
      console.error('[Lead Sniper] Error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketOverview();

    // Refresh every 5 minutes
    const interval = setInterval(fetchMarketOverview, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [region]);

  // Determine urgency styling
  const getUrgencyStyles = () => {
    if (!data) return { bg: 'bg-zinc-900/50', border: 'border-zinc-800', text: 'text-zinc-400', glow: '' };

    switch (data.urgency_level) {
      case 'CRITICAL':
        return {
          bg: 'bg-red-950/50',
          border: 'border-red-900',
          text: 'text-red-400',
          glow: 'shadow-[0_0_30px_rgba(239,68,68,0.3)]',
        };
      case 'HIGH':
        return {
          bg: 'bg-orange-950/50',
          border: 'border-orange-900',
          text: 'text-orange-400',
          glow: 'shadow-[0_0_20px_rgba(251,146,60,0.2)]',
        };
      case 'MEDIUM':
        return {
          bg: 'bg-yellow-950/50',
          border: 'border-yellow-900',
          text: 'text-yellow-400',
          glow: 'shadow-[0_0_15px_rgba(250,204,21,0.15)]',
        };
      default:
        return {
          bg: 'bg-zinc-900/50',
          border: 'border-zinc-800',
          text: 'text-zinc-400',
          glow: '',
        };
    }
  };

  const styles = getUrgencyStyles();

  if (loading) {
    return (
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
        <div className="flex items-center justify-center gap-2">
          <RefreshCw className="animate-spin" size={20} />
          <span className="text-zinc-400">Loading market data...</span>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="bg-red-950/30 border border-red-900 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-2">
          <AlertCircle className="text-red-400" size={20} />
          <h3 className="font-bold text-red-400">Lead Sniper Error</h3>
        </div>
        <p className="text-sm text-red-300">{error}</p>
      </div>
    );
  }

  return (
    <div
      className={`${styles.bg} border ${styles.border} rounded-xl p-6 ${styles.glow} transition-all duration-500 animate-[fadeIn_0.5s_ease-in]`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Target size={20} className={styles.text} />
          <h3 className={`font-bold ${styles.text} tracking-tight`}>
            🎯 LEAD SNIPER
          </h3>
        </div>
        <div className={`text-xs font-mono px-2 py-1 rounded ${styles.bg} ${styles.text} border ${styles.border}`}>
          LIVE
        </div>
      </div>

      {/* Region */}
      <div className="mb-3">
        <p className="text-xs text-zinc-500">Region: {data?.region || 'N/A'}</p>
      </div>

      {/* Main Metric */}
      <div className="mb-4 p-4 rounded-lg bg-black/30 border border-zinc-800">
        <div className="flex items-baseline gap-2">
          <span className={`text-4xl font-bold ${styles.text}`}>
            {data?.total_expiring_leases.toLocaleString() || '0'}
          </span>
          <span className="text-sm text-zinc-500">expiring leases</span>
        </div>
        <p className={`text-sm mt-2 ${styles.text}`}>
          {data?.insight || 'No data available'}
        </p>
      </div>

      {/* Opportunity Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-zinc-500">Opportunity Score</span>
          <span className={`text-sm font-bold ${styles.text}`}>
            {data?.opportunity_score || 0}/100
          </span>
        </div>
        <div className="h-2 bg-zinc-900 rounded-full overflow-hidden">
          <div
            className={`h-full ${
              (data?.opportunity_score || 0) >= 80
                ? 'bg-red-500'
                : (data?.opportunity_score || 0) >= 60
                ? 'bg-orange-500'
                : 'bg-yellow-500'
            } transition-all duration-500`}
            style={{ width: `${data?.opportunity_score || 0}%` }}
          />
        </div>
      </div>

      {/* Competitor Breakdown */}
      {data && Object.keys(data.competitor_breakdown).length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <Users size={16} className="text-zinc-500" />
            <span className="text-xs text-zinc-500">Competitor Breakdown</span>
          </div>
          {Object.entries(data.competitor_breakdown)
            .sort(([, a], [, b]) => (b as number) - (a as number))
            .slice(0, 5)
            .map(([brand, count]) => {
              const countNum = count as number;
              return (
                <div key={brand} className="flex items-center justify-between text-sm">
                  <span className="text-zinc-400">{brand}</span>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 bg-zinc-800 rounded-full w-24 overflow-hidden">
                      <div
                        className="h-full bg-blue-500"
                        style={{
                          width: `${
                            ((countNum / (data.total_expiring_leases || 1)) * 100)
                          }%`,
                        }}
                      />
                    </div>
                    <span className={`font-mono ${styles.text} w-12 text-right`}>
                      {countNum}
                    </span>
                  </div>
                </div>
              );
            })}
        </div>
      )}

      {/* Last Updated */}
      <div className="mt-4 pt-3 border-t border-zinc-800">
        <p className="text-xs text-zinc-600">
          Updated: {data?.last_updated ? new Date(data.last_updated).toLocaleTimeString() : 'N/A'}
        </p>
      </div>

      {/* Refresh Button */}
      <button
        onClick={fetchMarketOverview}
        disabled={loading}
        className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 bg-zinc-800/50 hover:bg-zinc-700/50 border border-zinc-700 rounded-lg text-sm text-zinc-400 transition-colors disabled:opacity-50"
      >
        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        Refresh Data
      </button>
    </div>
  );
};

export default LeadSniperWidget;
