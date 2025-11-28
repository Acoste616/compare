
import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Send, Check, Loader2 } from 'lucide-react';

interface Props {
  feedback: 'positive' | 'negative' | null;
  feedbackDetails?: string;
  onFeedback: (type: 'positive' | 'negative', details?: string) => void;
  // API integration props
  sessionId?: string;
  messageId?: string;
  userInput?: string;   // Input context: user's message that triggered this AI response
  aiOutput?: string;    // AI output being rated
  moduleName?: string;  // e.g., "fast_path"
  // Visibility props
  alwaysVisible?: boolean;  // Always show buttons (not just on hover)
  disabled?: boolean;       // Disable interactions (read-only mode)
}

const Feedback: React.FC<Props> = ({ 
  feedback, 
  feedbackDetails, 
  onFeedback,
  sessionId,
  messageId,
  userInput,
  aiOutput,
  moduleName = "fast_path",
  alwaysVisible = false,
  disabled = false
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [detailsText, setDetailsText] = useState(feedbackDetails || '');
  const [isSaving, setIsSaving] = useState(false);
  const [showSaved, setShowSaved] = useState(false);

  const submitFeedbackToAPI = async (rating: boolean, comment?: string) => {
    if (disabled) return;
    
    setIsSaving(true);
    try {
      const response = await fetch('http://localhost:8000/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          module_name: moduleName,
          rating: rating,
          user_input_snapshot: userInput,
          ai_output_snapshot: aiOutput,
          expert_comment: comment,
          message_id: messageId
        })
      });
      
      if (response.ok) {
        setShowSaved(true);
        setTimeout(() => setShowSaved(false), 2000);
      }
    } catch (error) {
      console.error('[FEEDBACK] Error submitting feedback:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handlePositiveClick = async () => {
    if (disabled) return;
    onFeedback('positive');
    setShowDetails(false);
    await submitFeedbackToAPI(true);
  };

  const handleNegativeClick = () => {
    if (disabled) return;
    if (feedback === 'negative') {
      setShowDetails(!showDetails);
    } else {
      onFeedback('negative');
      setShowDetails(true);
    }
  };

  const handleSubmitDetails = async () => {
    if (disabled) return;
    onFeedback('negative', detailsText);
    await submitFeedbackToAPI(false, detailsText);
    setShowDetails(false);
  };

  // Don't render if disabled and not rated
  if (disabled && !feedback) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 relative">
      {/* Saved Toast */}
      {showSaved && (
        <div className="absolute -top-8 right-0 bg-green-600 text-white text-[10px] px-2 py-1 rounded flex items-center gap-1 animate-in fade-in slide-in-from-bottom-2 duration-200 z-20">
          <Check size={10} />
          Saved to Dojo
        </div>
      )}

      {/* Rate This Label */}
      {alwaysVisible && !feedback && !disabled && (
        <span className="text-[10px] text-zinc-500 mr-1">Rate:</span>
      )}

      {/* Feedback Buttons Group - More visible styling */}
      <div className={`flex items-center rounded-lg border p-0.5 transition-all ${
        alwaysVisible 
          ? 'dark:bg-zinc-800/80 bg-zinc-100 dark:border-zinc-700 border-zinc-300' 
          : 'dark:bg-zinc-900/50 bg-zinc-100/50 dark:border-zinc-800 border-zinc-200'
      } ${disabled ? 'opacity-50' : ''}`}>
        <button 
          onClick={handlePositiveClick}
          disabled={isSaving || disabled}
          className={`p-1.5 rounded-md transition-all ${
            feedback === 'positive' 
              ? 'text-green-500 bg-green-500/20 shadow-sm' 
              : alwaysVisible
                ? 'text-zinc-400 dark:text-zinc-400 hover:text-green-500 hover:bg-green-500/10'
                : 'text-zinc-500 hover:text-green-500 hover:bg-green-500/10'
          } ${(isSaving || disabled) ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
          title="Good response - Save to Dojo"
        >
          {isSaving && feedback === 'positive' ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <ThumbsUp size={14} className={feedback === 'positive' ? 'fill-green-500' : ''} />
          )}
        </button>
        <div className="w-px h-4 dark:bg-zinc-700 bg-zinc-300 mx-0.5" />
        <button 
          onClick={handleNegativeClick}
          disabled={isSaving || disabled}
          className={`p-1.5 rounded-md transition-all ${
            feedback === 'negative' 
              ? 'text-red-500 bg-red-500/20 shadow-sm' 
              : alwaysVisible
                ? 'text-zinc-400 dark:text-zinc-400 hover:text-red-500 hover:bg-red-500/10'
                : 'text-zinc-500 hover:text-red-500 hover:bg-red-500/10'
          } ${(isSaving || disabled) ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
          title="Needs improvement - Add correction"
        >
          <ThumbsDown size={14} className={feedback === 'negative' ? 'fill-red-500' : ''} />
        </button>
      </div>

      {/* Quick Input for Negative Feedback */}
      {showDetails && !disabled && (
        <div className="absolute bottom-full right-0 mb-2 z-30 w-80 animate-in slide-in-from-bottom-2 fade-in duration-200">
          <div className="dark:bg-zinc-900 bg-white border dark:border-zinc-700 border-zinc-300 rounded-lg p-3 shadow-xl">
            <div className="text-[10px] dark:text-zinc-400 text-zinc-500 uppercase tracking-wider mb-2 font-bold flex items-center gap-2">
              <ThumbsDown size={10} className="text-red-500" />
              What should be improved?
            </div>
            <div className="flex gap-2">
              <input 
                type="text" 
                value={detailsText}
                onChange={(e) => setDetailsText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmitDetails()}
                placeholder="e.g., Wrong tone, missing data..."
                className="dark:bg-black bg-zinc-50 border dark:border-zinc-800 border-zinc-300 rounded px-2 py-1.5 text-xs dark:text-zinc-200 text-zinc-800 focus:border-tesla-red focus:outline-none flex-1 min-w-0"
                autoFocus
              />
              <button 
                onClick={handleSubmitDetails}
                disabled={isSaving}
                className="bg-tesla-red hover:bg-red-600 text-white rounded px-3 py-1.5 transition-colors flex items-center gap-1 font-medium text-xs"
              >
                {isSaving ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <>
                    <Send size={12} />
                    Save
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Feedback;
