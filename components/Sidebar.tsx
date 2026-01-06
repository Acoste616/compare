


import React from 'react';
import { useStore } from '../store';
import { 
  Plus, 
  LayoutDashboard, 
  ShieldAlert, 
  Sword,
  Hash,
  Settings,
  Lock,
  Sun,
  Moon,
  Languages
} from 'lucide-react';
import { Session } from '../types';

const Sidebar: React.FC = () => {
  const { 
    sessions, 
    currentSessionId, 
    currentView, 
    setView, 
    createSession, 
    selectSession,
    theme,
    toggleTheme,
    language,
    toggleLanguage,
    t
  } = useStore();

  const handleCreate = () => {
    createSession();
  };

  const sessionList = Object.values(sessions) as Session[];

  return (
    <div className="w-64 dark:bg-zinc-900 bg-zinc-100 dark:border-r dark:border-zinc-800 border-r border-zinc-300 flex flex-col h-full transition-colors duration-300">
      {/* Logo Area */}
      <div className="h-16 flex items-center px-6 border-b dark:border-zinc-800 border-zinc-300">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setView('dashboard')}>
           <div className="w-3 h-8 bg-tesla-red skew-x-[-15deg]"></div>
           <h1 className="dark:text-white text-zinc-900 font-bold tracking-wider text-lg">ULTRA <span className="text-tesla-red font-mono text-xs">v3.0</span></h1>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="p-2 space-y-1 border-b dark:border-zinc-800/50 border-zinc-300/50">
         <button 
            onClick={() => setView('dashboard')}
            className={`w-full text-left px-4 py-2.5 rounded text-xs font-medium flex items-center gap-3 transition-all ${
              currentView === 'dashboard'
              ? 'dark:bg-zinc-800 bg-zinc-200 dark:text-white text-zinc-900' 
              : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-800/50'
            }`}
         >
            <LayoutDashboard size={14} />
            <span>{t('dashboard')}</span>
         </button>
         <button 
            onClick={() => setView('admin')}
            className={`w-full text-left px-4 py-2.5 rounded text-xs font-medium flex items-center gap-3 transition-all ${
              currentView === 'admin'
              ? 'dark:bg-zinc-800 bg-zinc-200 dark:text-white text-zinc-900' 
              : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-800/50'
            }`}
         >
            <ShieldAlert size={14} />
            <span>{t('admin')}</span>
         </button>
         <button 
            onClick={() => setView('dojo')}
            className={`w-full text-left px-4 py-2.5 rounded text-xs font-medium flex items-center gap-3 transition-all ${
              currentView === 'dojo'
              ? 'dark:bg-zinc-800 bg-zinc-200 dark:text-white text-zinc-900' 
              : 'text-zinc-500 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-800/50'
            }`}
         >
            <Sword size={14} />
            <span>{t('dojo')}</span>
         </button>
      </div>

      {/* New Session */}
      <div className="p-4">
        <button 
            onClick={handleCreate}
            className="w-full bg-zinc-200 dark:bg-zinc-800 hover:bg-tesla-red dark:hover:bg-tesla-red text-zinc-900 dark:text-white hover:text-white p-2 rounded transition-colors flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-wide shadow-sm"
        >
            <Plus size={14} />
            {t('newSession')}
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-1 scrollbar-thin dark:scrollbar-thumb-zinc-800 scrollbar-thumb-zinc-300">
        <div className="px-4 py-2 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{t('recentSessions')}</div>
        {sessionList.sort((a, b) => b.lastUpdated - a.lastUpdated).map((session) => {
            const isActive = currentSessionId === session.id && currentView === 'chat';
            const isClosed = session.status === 'closed';
            return (
                <button
                    key={session.id}
                    onClick={() => selectSession(session.id)}
                    className={`w-full text-left px-4 py-3 rounded text-sm flex items-center gap-3 transition-all group ${
                        isActive
                        ? 'dark:bg-zinc-800 bg-white dark:text-white text-zinc-900 border-l-2 border-tesla-red shadow-sm' 
                        : isClosed 
                            ? 'text-zinc-400 dark:text-zinc-600 opacity-80 hover:opacity-100 dark:hover:bg-zinc-900 hover:bg-zinc-200'
                            : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-800/50'
                    }`}
                >
                    {isClosed ? (
                        <Lock size={14} className="text-zinc-400 dark:text-zinc-700 shrink-0" />
                    ) : (
                        <Hash size={14} className={isActive ? 'text-tesla-red shrink-0' : 'text-zinc-400 dark:text-zinc-600 group-hover:text-zinc-600 dark:group-hover:text-zinc-400 shrink-0'} />
                    )}
                    
                    <div className="truncate flex-1">
                        <div className="font-mono font-medium truncate text-xs flex justify-between">
                            <span>{session.id}</span>
                            {isClosed && session.outcome === 'sale' && <span className="text-[8px] text-green-600 dark:text-green-500 self-center">{t('sold')}</span>}
                            {isClosed && session.outcome === 'no_sale' && <span className="text-[8px] text-red-600 dark:text-red-500 self-center">{t('lost')}</span>}
                        </div>
                        <div className="text-[10px] text-zinc-500 dark:text-zinc-600 font-mono flex justify-between mt-0.5">
                        <span>{new Date(session.lastUpdated).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                        </div>
                    </div>
                </button>
            );
        })}
      </div>

      {/* Footer with Toggles */}
      <div className="p-4 border-t dark:border-zinc-800 border-zinc-300 text-zinc-500 flex flex-col gap-3 dark:bg-black/20 bg-zinc-50">
        
        {/* Controls Row */}
        <div className="flex items-center justify-between w-full gap-2">
            <button 
                onClick={toggleTheme}
                className="flex-1 flex items-center justify-center gap-2 p-1.5 rounded dark:bg-zinc-800 bg-zinc-200 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors text-xs font-medium dark:text-zinc-300 text-zinc-700"
                title="Toggle Theme"
            >
                {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
                <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
            </button>

            <button 
                onClick={toggleLanguage}
                className="flex-1 flex items-center justify-center gap-2 p-1.5 rounded dark:bg-zinc-800 bg-zinc-200 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors text-xs font-medium dark:text-zinc-300 text-zinc-700"
                title="Toggle Language"
            >
                <Languages size={14} />
                <span>{language}</span>
            </button>
        </div>

        <div className="flex items-center justify-between text-[10px]">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span>{t('secured')}</span>
          </div>
          <button className="hover:text-zinc-900 dark:hover:text-white transition"><Settings size={14} /></button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;