


import React, { useState } from 'react';
import { useStore } from '../store';
import { 
  Users, 
  Zap, 
  AlertTriangle, 
  TrendingUp, 
  ArrowRight,
  PlayCircle,
  LayoutDashboard,
  Hash,
  Search,
  History,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { JourneyStage, Session } from '../types';

const Dashboard: React.FC = () => {
  const { sessions, selectSession, createSession, t } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchError, setSearchError] = useState('');
  
  const sessionList = Object.values(sessions) as Session[];
  
  // Separate Active and Closed
  const activeSessions = sessionList.filter(s => s.status !== 'closed').sort((a, b) => b.lastUpdated - a.lastUpdated);
  const closedSessions = sessionList.filter(s => s.status === 'closed').sort((a, b) => b.lastUpdated - a.lastUpdated);

  // Real-time Stats Calculation
  const totalActive = activeSessions.length;
  
  // Attention Needed: High Churn Risk or Low Purchase Temp
  const attentionNeeded = activeSessions.filter(s => 
    s.analysisState.m2_indicators.churnRisk === 'High' || 
    s.analysisState.m2_indicators.purchaseTemperature < 30
  ).length;

  // Win Rate: Average Purchase Temperature of ACTIVE sessions
  const avgTemp = activeSessions.length > 0 
    ? Math.round(activeSessions.reduce((sum, s) => sum + s.analysisState.m2_indicators.purchaseTemperature, 0) / activeSessions.length) 
    : 0;

  const handleStartAnalysis = () => {
    createSession();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchError('');
    
    if (!searchQuery.trim()) return;

    const foundSessionId = Object.keys(sessions).find(id => id.toLowerCase() === searchQuery.toLowerCase());

    if (foundSessionId) {
        selectSession(foundSessionId);
    } else {
        setSearchError('Session not found within local registry.');
    }
  };

  return (
    <div className="flex-1 h-full dark:bg-zinc-950 bg-white overflow-y-auto p-8 transition-colors duration-300">
      
      {/* Hero Header */}
      <div className="mb-10 border-b dark:border-zinc-800 border-zinc-200 pb-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-bold dark:text-white text-zinc-900 mb-2 tracking-tight">
              {t('cognitiveEngineActive')}
            </h1>
            <p className="dark:text-zinc-400 text-zinc-600 max-w-2xl">
              {t('systemMonitoring')}
            </p>
          </div>

          {/* Primary Action Area */}
          <div className="flex flex-col sm:flex-row gap-3 items-end">
             {/* Search Box */}
             <div className="relative">
                <form onSubmit={handleSearch} className="flex items-center">
                    <input 
                        type="text" 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder={t('searchPlaceholder')}
                        className="dark:bg-black bg-zinc-100 border dark:border-zinc-800 border-zinc-300 dark:text-white text-zinc-900 pl-4 pr-10 py-4 rounded-l-lg w-64 dark:focus:border-zinc-600 focus:border-zinc-400 focus:outline-none font-mono text-sm transition-colors"
                    />
                    <button type="submit" className="dark:bg-zinc-800 bg-zinc-200 dark:hover:bg-zinc-700 hover:bg-zinc-300 dark:text-white text-zinc-700 px-4 py-4 rounded-r-lg border-y border-r dark:border-zinc-800 border-zinc-300 transition-colors">
                        <Search size={20} />
                    </button>
                </form>
                {searchError && (
                    <div className="absolute top-full mt-2 left-0 text-[10px] text-red-500 font-mono">{searchError}</div>
                )}
             </div>

             <div className="h-14 w-px dark:bg-zinc-800 bg-zinc-300 mx-2 hidden sm:block"></div>

             <button 
               onClick={handleStartAnalysis}
               className="bg-tesla-red hover:bg-red-600 text-white px-8 py-4 rounded-lg font-bold tracking-wide flex items-center gap-2 transition-all shadow-[0_0_20px_rgba(227,25,55,0.3)] hover:shadow-[0_0_30px_rgba(227,25,55,0.5)] hover:scale-[1.02] whitespace-nowrap active:scale-[0.98]"
             >
               <PlayCircle size={20} />
               {t('startNewSession')}
             </button>
          </div>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        {/* Card 1 */}
        <div className="dark:bg-zinc-900/50 bg-white border dark:border-zinc-800 border-zinc-200 rounded-xl p-6 relative overflow-hidden group dark:hover:bg-zinc-900 hover:bg-zinc-50 transition-colors shadow-sm">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Users size={48} className="dark:text-white text-zinc-900" />
          </div>
          <div className="text-zinc-500 dark:text-zinc-400 text-xs font-medium uppercase tracking-wider mb-2">{t('activeSessions')}</div>
          <div className="text-4xl font-mono font-bold dark:text-white text-zinc-900">{totalActive}</div>
          <div className="mt-4 text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
            <TrendingUp size={12} />
            <span>{t('anonymizedTracking')}</span>
          </div>
        </div>

        {/* Card 2 */}
        <div className="dark:bg-zinc-900/50 bg-white border dark:border-zinc-800 border-zinc-200 rounded-xl p-6 relative overflow-hidden group dark:hover:bg-zinc-900 hover:bg-zinc-50 transition-colors shadow-sm">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <AlertTriangle size={48} className={attentionNeeded > 0 ? "text-tesla-red animate-pulse" : "text-zinc-700 dark:text-zinc-700"} />
          </div>
          <div className="text-zinc-500 dark:text-zinc-400 text-xs font-medium uppercase tracking-wider mb-2">{t('attentionNeeded')}</div>
          <div className="text-4xl font-mono font-bold dark:text-white text-zinc-900">{attentionNeeded}</div>
          <div className={`mt-4 text-xs flex items-center gap-1 ${attentionNeeded > 0 ? "text-tesla-red" : "text-zinc-500"}`}>
            <span>{attentionNeeded > 0 ? t('churnHigh') : t('allSystemsNominal')}</span>
          </div>
        </div>

        {/* Card 3 */}
        <div className="dark:bg-zinc-900/50 bg-white border dark:border-zinc-800 border-zinc-200 rounded-xl p-6 relative overflow-hidden group dark:hover:bg-zinc-900 hover:bg-zinc-50 transition-colors shadow-sm">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Zap size={48} className="text-yellow-500" />
          </div>
          <div className="text-zinc-500 dark:text-zinc-400 text-xs font-medium uppercase tracking-wider mb-2">{t('avgTemp')}</div>
          <div className="text-4xl font-mono font-bold dark:text-white text-zinc-900">{avgTemp}%</div>
          <div className="mt-4 h-1.5 w-full dark:bg-zinc-800 bg-zinc-200 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-tesla-red to-purple-600 transition-all duration-1000" style={{ width: `${avgTemp}%` }}></div>
          </div>
        </div>
      </div>

      {/* Recent Activity / Urgent List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Urgent Priorities */}
        <div>
          <div className="flex items-center justify-between mb-4">
             <h3 className="dark:text-zinc-200 text-zinc-800 font-bold flex items-center gap-2">
               <AlertTriangle size={16} className="text-tesla-red" />
               {t('activeOperations')}
             </h3>
          </div>
          <div className="dark:bg-zinc-900/30 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-xl overflow-hidden min-h-[200px] mb-8">
            {activeSessions.length > 0 ? (
              activeSessions.map((session, i) => (
                <button 
                  key={session.id}
                  onClick={() => selectSession(session.id)}
                  className="w-full text-left p-4 border-b dark:border-zinc-800 border-zinc-200 last:border-0 hover:bg-zinc-200 dark:hover:bg-zinc-800/50 transition-colors flex items-center justify-between group"
                >
                  <div>
                    <div className="dark:text-zinc-200 text-zinc-800 font-medium group-hover:text-zinc-900 dark:group-hover:text-white transition-colors flex items-center gap-2 font-mono">
                      <Hash size={14} className="dark:text-zinc-500 text-zinc-400" />
                      {session.id}
                      {session.analysisState.m2_indicators.churnRisk === 'High' && (
                          <span className="text-[9px] bg-red-900/50 text-red-300 px-1.5 py-0.5 rounded uppercase font-bold tracking-wider font-sans">Risk</span>
                      )}
                    </div>
                    <div className="text-xs dark:text-zinc-500 text-zinc-500 font-mono mt-1 flex items-center gap-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] border ${
                        session.journeyStage === JourneyStage.CLOSING ? 'bg-green-900/20 border-green-900/50 text-green-600 dark:text-green-400' : 
                        'dark:bg-zinc-800 bg-zinc-200 dark:border-zinc-700 border-zinc-300'
                      }`}>
                        {session.journeyStage}
                      </span>
                      <span>Temp: {session.analysisState.m2_indicators.purchaseTemperature}%</span>
                    </div>
                  </div>
                  <ArrowRight size={16} className="text-zinc-400 group-hover:text-tesla-red transition-colors" />
                </button>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center h-[200px] text-zinc-500 gap-2">
                <LayoutDashboard size={24} className="opacity-20" />
                <span className="text-sm italic">{t('noActiveSessions')}</span>
              </div>
            )}
          </div>

           {/* Archived Sessions */}
          <div className="flex items-center justify-between mb-4">
             <h3 className="text-zinc-500 dark:text-zinc-400 font-bold flex items-center gap-2 text-sm uppercase tracking-wide">
               <History size={14} />
               {t('archivedHistory')}
             </h3>
          </div>
          <div className="dark:bg-zinc-900/10 bg-white border dark:border-zinc-800/50 border-zinc-200 rounded-xl overflow-hidden shadow-sm">
            {closedSessions.length > 0 ? (
               closedSessions.map((session) => (
                <button 
                  key={session.id}
                  onClick={() => selectSession(session.id)}
                  className="w-full text-left p-3 border-b dark:border-zinc-800/50 border-zinc-200 last:border-0 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition-colors flex items-center justify-between group opacity-70 hover:opacity-100"
                >
                  <div>
                    <div className="dark:text-zinc-400 text-zinc-600 font-medium group-hover:text-zinc-900 dark:group-hover:text-zinc-200 transition-colors flex items-center gap-2 font-mono text-xs">
                      <Hash size={12} className="text-zinc-500 dark:text-zinc-600" />
                      {session.id}
                      {session.outcome === 'sale' ? (
                        <span className="text-green-600 dark:text-green-500 flex items-center gap-1"><CheckCircle2 size={10}/> {t('sale')}</span>
                      ) : (
                        <span className="text-red-600 dark:text-red-500 flex items-center gap-1"><XCircle size={10}/> {t('loss')}</span>
                      )}
                    </div>
                  </div>
                  <span className="text-[10px] text-zinc-500 dark:text-zinc-600">{new Date(session.lastUpdated).toLocaleDateString()}</span>
                </button>
               ))
            ) : (
                <div className="p-4 text-center text-xs text-zinc-600 dark:text-zinc-700 italic">{t('noArchivedSessions')}</div>
            )}
          </div>
        </div>

        {/* System Updates */}
        <div>
          <div className="flex items-center justify-between mb-4">
             <h3 className="dark:text-zinc-200 text-zinc-800 font-bold flex items-center gap-2">
               <LayoutDashboard size={16} className="text-blue-400" />
               {t('systemModules')}
             </h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 dark:bg-zinc-900/30 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-700 transition-colors">
              <div className="text-xs text-zinc-500 mb-1">Module M1</div>
              <div className="dark:text-zinc-300 text-zinc-800 font-medium text-sm">DNA Analysis</div>
              <div className="mt-2 text-[10px] text-green-600 dark:text-green-500 flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                Online • Latency 12ms
              </div>
            </div>
            <div className="p-4 dark:bg-zinc-900/30 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-700 transition-colors">
              <div className="text-xs text-zinc-500 mb-1">Module M3</div>
              <div className="dark:text-zinc-300 text-zinc-800 font-medium text-sm">Psychometrics</div>
              <div className="mt-2 text-[10px] text-green-600 dark:text-green-500 flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                Online • Calibrated
              </div>
            </div>
            <div className="p-4 dark:bg-zinc-900/30 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-700 transition-colors">
              <div className="text-xs text-zinc-500 mb-1">Module M6</div>
              <div className="dark:text-zinc-300 text-zinc-800 font-medium text-sm">Tactical Playbook</div>
              <div className="mt-2 text-[10px] text-green-600 dark:text-green-500 flex items-center gap-1">
                 <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                 Online • v3.1.0
              </div>
            </div>
            <div className="p-4 dark:bg-zinc-900/30 bg-zinc-50 border dark:border-zinc-800 border-zinc-200 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-700 transition-colors">
              <div className="text-xs text-zinc-500 mb-1">Gemini Core</div>
              <div className="dark:text-zinc-300 text-zinc-800 font-medium text-sm">LLM Connection</div>
              <div className="mt-2 text-[10px] text-blue-500 dark:text-blue-400 flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
                Active • 2.5 Flash (Thinking)
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;