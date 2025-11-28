import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../store';
import { ArrowRight, Bot, X, Flag, CheckCircle2, XCircle, AlertCircle, Lock } from 'lucide-react';
import { JourneyStage, Message } from '../types';
import JarvisMetadata from './chat/JarvisMetadata';
import ContextNeeds from './chat/ContextNeeds';
import SuggestedActions from './chat/SuggestedActions';
import Feedback from './chat/Feedback';
import StrategicModal from './chat/StrategicModal';
import { useWebSocket } from '../hooks/useWebSocket';

const STAGES = [
  { id: JourneyStage.DISCOVERY, label: 'Discovery' },
  { id: JourneyStage.DEMO, label: 'Demo' },
  { id: JourneyStage.OBJECTION_HANDLING, label: 'Objection' },
  { id: JourneyStage.FINANCING, label: 'Financing' },
  { id: JourneyStage.CLOSING, label: 'Closing' },
  { id: JourneyStage.DELIVERY, label: 'Delivery' },
];

// Helper for basic bold formatting
const FormatText = ({ text }: { text: string }) => {
  if (!text) return null;
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="dark:text-white text-zinc-900 font-semibold">{part.slice(2, -2)}</strong>;
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
};

const Chat: React.FC = () => {
  const {
    currentSessionId,
    sessions,
    addMessage,
    setFeedback,
    updateJourneyStage,
    closeSession,
    setAnalyzing,
    t,
    language
  } = useStore();

  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  // Modal State for Deep Analysis
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState('');

  // Modal State for End Session
  const [isEndSessionOpen, setIsEndSessionOpen] = useState(false);
  const [isLearning, setIsLearning] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const session = currentSessionId ? sessions[currentSessionId] : null;
  const isReadOnly = session?.status === 'closed';

  // WebSocket Hook
  const { sendMessage } = useWebSocket(session?.id || null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [session?.messages, isSending]);

  // Stop loading when AI responds
  useEffect(() => {
    if (session?.messages.length && session.messages[session.messages.length - 1].role === 'ai') {
      setIsSending(false);
    }
  }, [session?.messages]);

  if (!session) return null;

  const handleSend = async (text: string = input) => {
    if (!text.trim() || isReadOnly) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now()
    };

    addMessage(session.id, userMsg);
    setInput('');
    setIsSending(true);
    setAnalyzing(true);

    try {
      // Pass language with the message
      sendMessage(text, language);
    } catch (error) {
      console.error("Chat Error:", error);
      setIsSending(false);
      setAnalyzing(false);
      addMessage(session.id, {
        id: Date.now().toString(),
        role: 'system',
        content: t('connectionFailure'),
        timestamp: Date.now()
      });
    }
  };

  const handleQuestionClick = (question: string) => {
    if (isReadOnly) return;
    setSelectedQuestion(question);
    setIsModalOpen(true);
  };

  const handleQuestionSubmit = (clientAnswer: string) => {
    const formattedContent = `[ACTION TAKEN: ${selectedQuestion}]\n[CLIENT RESPONSE: ${clientAnswer}]`;
    handleSend(formattedContent);
    setIsModalOpen(false);
  };

  const handleOutcomeSelection = (outcome: 'sale' | 'no_sale') => {
    setIsLearning(true);
    // Simulate model reinforcement delay
    setTimeout(() => {
      setIsLearning(false);
      setIsEndSessionOpen(false);
      closeSession(session.id, outcome);
    }, 1500);
  };

  const handleFeedbackSubmit = async (messageId: string, type: 'positive' | 'negative', details?: string) => {
    if (!session) return;
    setFeedback(session.id, messageId, type, details);
    // In a real app, we would send this feedback to the backend here via API
    console.log(`[FEEDBACK] ${type} for ${messageId}: ${details}`);
  };

  return (
    <div className="flex flex-col h-full dark:bg-zinc-950 bg-white relative transition-colors duration-300">

      {/* Top Bar: Journey Stage Selector & Controls */}
      <div className="h-16 border-b dark:border-zinc-800 border-zinc-200 flex items-center px-6 dark:bg-zinc-900/80 bg-zinc-50/90 backdrop-blur-md shrink-0 z-10 justify-between transition-colors">
        <div className="flex items-center gap-3">
          <div className={`text-xs font-mono px-2 py-1 rounded border flex items-center gap-2 ${isReadOnly ? 'dark:bg-zinc-800 bg-zinc-200 text-zinc-500 border-zinc-300 dark:border-zinc-700' : 'dark:bg-black bg-white text-zinc-500 dark:border-zinc-800 border-zinc-300'}`}>
            {isReadOnly && <Lock size={10} />}
            {session.id}
          </div>
          {isReadOnly && (
            <div className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider border ${session.outcome === 'sale' ? 'bg-green-900/20 border-green-800 text-green-600 dark:text-green-400' : 'bg-red-900/20 border-red-800 text-red-600 dark:text-red-400'}`}>
              {session.outcome === 'sale' ? t('sold') : t('lost')}
            </div>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex w-auto items-center gap-4 overflow-x-auto no-scrollbar">
            {STAGES.map((stage, idx) => {
              const isActive = session.journeyStage === stage.id;
              return (
                <button
                  key={stage.id}
                  onClick={() => !isReadOnly && updateJourneyStage(session.id, stage.id)}
                  disabled={isReadOnly}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap ${isActive
                    ? 'bg-tesla-red text-white shadow-[0_0_15px_rgba(227,25,55,0.4)] ring-1 ring-red-400/50'
                    : isReadOnly ? 'text-zinc-400 cursor-default' : 'text-zinc-600 dark:text-zinc-400 border border-transparent hover:text-zinc-900 dark:hover:text-zinc-200'
                    }`}
                >
                  <span className={isActive ? 'opacity-100' : 'opacity-50'}>{idx + 1}.</span>
                  <span className="hidden md:inline">{stage.label}</span>
                </button>
              );
            })}
          </div>

          {!isReadOnly && (
            <>
              <div className="h-6 w-px dark:bg-zinc-800 bg-zinc-300 mx-1"></div>
              <button
                onClick={() => setIsEndSessionOpen(true)}
                className="text-xs dark:bg-zinc-800 bg-zinc-200 hover:bg-zinc-300 dark:hover:bg-zinc-700 dark:text-white text-zinc-800 px-3 py-1.5 rounded border dark:border-zinc-700 border-zinc-300 hover:border-zinc-400 dark:hover:border-zinc-500 transition-colors flex items-center gap-2 whitespace-nowrap"
              >
                <Flag size={12} />
                {t('endSession')}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-thin dark:scrollbar-thumb-zinc-800 scrollbar-thumb-zinc-300">
        {session.messages.map((msg, index) => {
          // Find the last user message before this AI message (for feedback context)
          const lastUserMessage = msg.role === 'ai' 
            ? session.messages.slice(0, index).reverse().find(m => m.role === 'user')?.content 
            : undefined;
          
          return (
          <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : msg.role === 'system' ? 'items-center' : 'items-start'}`}>

            {msg.role === 'system' ? (
              <div className="text-xs text-zinc-500 italic py-2">{msg.content}</div>
            ) : (
              <div className={`max-w-[90%] lg:max-w-[85%] ${msg.role === 'user' ? '' : 'w-full'}`}>

                {msg.role === 'user' ? (
                  // User Message
                  <div className="bg-blue-600 text-white p-4 rounded-2xl rounded-tr-sm shadow-lg text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </div>
                ) : (
                  // AI Message
                  <div className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-zinc-200 rounded-xl shadow-xl overflow-hidden group">

                    {/* Strategy Tag (if exists) */}
                    {msg.confidenceReason && (
                      <div className="px-5 pt-4 pb-2">
                        <div className="bg-zinc-800/30 border border-zinc-700/50 rounded-lg px-3 py-2">
                          <div className="flex items-center gap-2 mb-1">
                            <div className="w-1.5 h-1.5 bg-amber-500 rounded-full"></div>
                            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider">{t('strategy')}</span>
                          </div>
                          <p className="text-xs text-zinc-400 leading-relaxed italic">{msg.confidenceReason}</p>
                        </div>
                      </div>
                    )}

                    {/* Main Quote to Client */}
                    <div className="px-5 pb-4">
                      <div className="flex items-start gap-2 mb-1.5">
                        <div className="w-1 h-1 mt-2 bg-blue-500 rounded-full"></div>
                        <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider">{t('toClient')}</span>
                      </div>
                      <div className="text-sm dark:text-zinc-100 text-zinc-800 leading-relaxed pl-3 border-l-2 border-blue-500/30">
                        <FormatText text={msg.content} />
                      </div>
                    </div>

                    {/* Modules Stack */}
                    {(msg.confidence !== undefined || (msg.contextNeeds && msg.contextNeeds.length > 0) || (msg.suggestedActions && msg.suggestedActions.length > 0)) && (
                      <div className="px-5 pb-5 space-y-3">
                        <div className="h-px dark:bg-zinc-800/50 bg-zinc-200 w-full my-2"></div>

                        <JarvisMetadata
                          confidence={msg.confidence || 0}
                          confidenceReason={msg.confidenceReason}
                          clientStyle={msg.clientStyle}
                        />

                        {msg.contextNeeds && msg.contextNeeds.length > 0 && (
                          <ContextNeeds needs={msg.contextNeeds} />
                        )}

                        {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                          <SuggestedActions
                            actions={msg.suggestedActions}
                            onSelect={handleQuestionClick}
                          />
                        )}
                      </div>
                    )}

                    {/* Footer with Always-Visible Feedback */}
                    <div className="dark:bg-black/20 bg-zinc-50 border-t dark:border-zinc-800 border-zinc-200 px-4 py-2.5 flex justify-between items-center">
                      <div className="flex items-center gap-2 text-zinc-500">
                        <Bot size={12} />
                        <span className="text-[10px] font-mono">ULTRA v3.0 • {session.id}</span>
                      </div>
                      {/* Feedback buttons - ALWAYS VISIBLE */}
                      <Feedback
                        feedback={msg.feedback || null}
                        feedbackDetails={msg.feedbackDetails}
                        onFeedback={(type, details) => handleFeedbackSubmit(msg.id, type, details)}
                        sessionId={session.id}
                        messageId={msg.id}
                        userInput={lastUserMessage}
                        aiOutput={msg.content}
                        moduleName="fast_path"
                        alwaysVisible={true}
                        disabled={isReadOnly}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )})}

        {/* Loading Indicator */}
        {isSending && (
          <div className="flex items-center gap-2 p-4 opacity-50">
            <div className="w-2 h-2 bg-tesla-red rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-tesla-red rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-tesla-red rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 dark:bg-zinc-950 bg-zinc-100 border-t dark:border-zinc-800 border-zinc-300 pb-8 transition-colors">
        <div className="max-w-5xl mx-auto relative group rounded-xl transition-all duration-300">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder={isReadOnly ? t('sessionClosed') : t('typeMessage')}
            disabled={isSending || isReadOnly}
            className={`w-full dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-zinc-300 dark:text-zinc-200 text-zinc-800 placeholder-zinc-500 text-sm rounded-lg p-4 pr-14 min-h-[60px] focus:outline-none transition-colors resize-none ${isReadOnly ? 'cursor-not-allowed opacity-60' : 'focus:border-tesla-red'}`}
            rows={1}
            autoFocus={!isReadOnly}
          />
          {!isReadOnly && (
            <button
              onClick={() => handleSend()}
              disabled={isSending || !input.trim()}
              className="absolute right-3 bottom-3 p-2 bg-tesla-red text-white rounded hover:bg-red-600 disabled:opacity-50 transition-all"
            >
              {isSending ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <ArrowRight size={16} />}
            </button>
          )}
        </div>
      </div>

      {/* Strategic Question Modal */}
      <StrategicModal
        isOpen={isModalOpen}
        question={selectedQuestion}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleQuestionSubmit}
      />

      {/* End Session Modal */}
      {isEndSessionOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center dark:bg-black/90 bg-zinc-500/50 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="dark:bg-zinc-900 bg-white border dark:border-zinc-700 border-zinc-200 w-full max-w-md rounded-xl shadow-2xl p-8 relative animate-in zoom-in-95 duration-200 text-center">
            {isLearning ? (
              <div className="py-10 flex flex-col items-center justify-center">
                <div className="w-16 h-16 border-4 border-zinc-800 border-t-tesla-red rounded-full animate-spin mb-4"></div>
                <h3 className="text-xl font-bold dark:text-white text-zinc-900 mb-2">{t('updatingModels')}</h3>
                <p className="text-zinc-500 text-sm">Integrating session outcome into global weights.</p>
              </div>
            ) : (
              <>
                <button
                  onClick={() => setIsEndSessionOpen(false)}
                  className="absolute top-4 right-4 text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors"
                >
                  <X size={20} />
                </button>

                <AlertCircle size={48} className="text-zinc-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold dark:text-white text-zinc-900 mb-2">{t('missionDebrief')}</h2>
                <p className="text-zinc-500 dark:text-zinc-400 text-sm mb-8">
                  {t('confirmOutcome')} <span className="font-mono dark:text-zinc-300 text-zinc-700">{session.id}</span>.
                  This data is critical for reinforcement learning.
                </p>

                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => handleOutcomeSelection('sale')}
                    className="dark:bg-green-900/20 bg-green-100 hover:bg-green-200 dark:hover:bg-green-900/40 border dark:border-green-900/50 border-green-300 hover:border-green-500 text-green-600 dark:text-green-400 py-4 rounded-xl flex flex-col items-center gap-2 transition-all group"
                  >
                    <CheckCircle2 size={32} className="group-hover:scale-110 transition-transform" />
                    <span className="font-bold">{t('saleClosed')}</span>
                  </button>
                  <button
                    onClick={() => handleOutcomeSelection('no_sale')}
                    className="dark:bg-red-900/20 bg-red-100 hover:bg-red-200 dark:hover:bg-red-900/40 border dark:border-red-900/50 border-red-300 hover:border-red-500 text-red-600 dark:text-red-400 py-4 rounded-xl flex flex-col items-center gap-2 transition-all group"
                  >
                    <XCircle size={32} className="group-hover:scale-110 transition-transform" />
                    <span className="font-bold">{t('noSale')}</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;