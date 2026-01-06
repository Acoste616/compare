import React, { useEffect } from 'react';
import { useStore } from './store';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import AnalysisPanel from './components/AnalysisPanel';
import Dashboard from './components/Dashboard';
import AdminPanel from './components/AdminPanel';
import Dojo from './components/Dojo';
import { JourneyStage } from './types';

const App: React.FC = () => {
  const { currentView, currentSessionId, theme } = useStore();

  // Handle Dark/Light Mode Class on Root
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  // Load session from URL if present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session');

    if (sessionId) {
      // Fetch session from backend
      fetch(`http://localhost:8000/api/sessions/${sessionId}`)
        .then(res => {
          if (!res.ok) throw new Error("Session not found");
          return res.json();
        })
        .then(data => {
          // Update store
          useStore.setState(state => ({
            sessions: {
              ...state.sessions, [data.id]: {
                id: data.id,
                createdAt: data.createdAt,
                status: data.status,
                outcome: data.outcome,
                journeyStage: data.journeyStage as JourneyStage,
                messages: data.messages,
                lastUpdated: Date.now(),
                analysisState: data.analysisState
              }
            },
            currentSessionId: data.id,
            currentView: 'chat',
            currentAnalysis: data.analysisState
          }));
        })
        .catch(err => console.error("Failed to load session", err));
    }
  }, []);

  return (
    <div className="flex h-screen w-full overflow-hidden dark:bg-black bg-zinc-50 font-sans transition-colors duration-300">
      {/* Left Sidebar: Sessions & Nav */}
      <div className="shrink-0 z-20">
        <Sidebar />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0 relative z-10 flex flex-col">
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'chat' && currentSessionId && <Chat />}
        {currentView === 'chat' && !currentSessionId && <Dashboard />} {/* Fallback if no session selected */}
        {currentView === 'admin' && <AdminPanel />}
        {currentView === 'dojo' && <Dojo />}
      </div>

      {/* Right Sidebar: 7-Module Analysis */}
      {/* Only visible when in Chat view to provide context */}
      {currentView === 'chat' && currentSessionId && (
        <div className="w-80 lg:w-96 shrink-0 border-l dark:border-zinc-800 border-zinc-200 dark:bg-zinc-950 bg-white hidden md:block z-20 transition-colors duration-300">
          <AnalysisPanel />
        </div>
      )}
    </div>
  );
};

export default App;