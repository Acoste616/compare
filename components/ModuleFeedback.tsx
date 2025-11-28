import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Send, Check, Loader2, X } from 'lucide-react';

interface ModuleFeedbackProps {
  sessionId?: string;
  moduleName: string;
  userInput?: string;   // Input context: conversation summary or last user messages
  moduleOutput: string; // JSON stringified or text content of the module (AI output)
}

const ModuleFeedback: React.FC<ModuleFeedbackProps> = ({
  sessionId,
  moduleName,
  userInput,
  moduleOutput
}) => {
  const [rating, setRating] = useState<'positive' | 'negative' | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [showSaved, setShowSaved] = useState(false);

  const submitFeedback = async (isPositive: boolean, expertComment?: string) => {
    setIsSaving(true);
    try {
      const response = await fetch('http://localhost:8000/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          module_name: moduleName,
          rating: isPositive,
          user_input_snapshot: userInput,
          ai_output_snapshot: moduleOutput,
          expert_comment: expertComment
        })
      });
      
      if (response.ok) {
        setShowSaved(true);
        setTimeout(() => {
          setShowSaved(false);
        }, 2000);
      }
    } catch (error) {
      console.error('[MODULE FEEDBACK] Error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handlePositive = async () => {
    setRating('positive');
    setShowComment(false);
    await submitFeedback(true);
  };

  const handleNegative = () => {
    setRating('negative');
    setShowComment(true);
  };

  const handleSubmitComment = async () => {
    await submitFeedback(false, comment);
    setShowComment(false);
  };

  const handleCancelComment = () => {
    setShowComment(false);
    setRating(null);
  };

  return (
    <div className="relative">
      {/* Saved Toast */}
      {showSaved && (
        <div className="absolute -top-6 right-0 z-20 bg-green-600 text-white text-[9px] px-2 py-0.5 rounded flex items-center gap-1 animate-in fade-in slide-in-from-bottom-1 duration-200">
          <Check size={8} />
          Saved
        </div>
      )}

      {/* Feedback Buttons - Only show if no comment form is open */}
      {!showComment && (
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <button
            onClick={handlePositive}
            disabled={isSaving}
            className={`p-1 rounded transition-all ${
              rating === 'positive'
                ? 'text-green-400 bg-green-500/10'
                : 'text-zinc-600 hover:text-green-400 hover:bg-green-500/10'
            } ${isSaving ? 'opacity-50' : ''}`}
            title="Accurate analysis"
          >
            {isSaving && rating === 'positive' ? (
              <Loader2 size={10} className="animate-spin" />
            ) : (
              <ThumbsUp size={10} />
            )}
          </button>
          <button
            onClick={handleNegative}
            disabled={isSaving}
            className={`p-1 rounded transition-all ${
              rating === 'negative'
                ? 'text-red-400 bg-red-500/10'
                : 'text-zinc-600 hover:text-red-400 hover:bg-red-500/10'
            }`}
            title="Needs correction"
          >
            <ThumbsDown size={10} />
          </button>
        </div>
      )}

      {/* Comment Input Form */}
      {showComment && (
        <div className="absolute top-0 right-0 z-20 w-56 animate-in fade-in slide-in-from-right-2 duration-200">
          <div className="bg-zinc-900 border border-red-500/30 rounded-lg p-2 shadow-xl">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[9px] text-red-400 uppercase tracking-wider font-bold">
                What's wrong?
              </span>
              <button
                onClick={handleCancelComment}
                className="text-zinc-500 hover:text-zinc-300 p-0.5"
              >
                <X size={10} />
              </button>
            </div>
            <div className="flex gap-1.5">
              <input
                type="text"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmitComment()}
                placeholder="e.g., Wrong DISC score"
                className="flex-1 bg-black border border-zinc-800 rounded px-2 py-1 text-[10px] text-zinc-200 focus:border-red-500 focus:outline-none"
                autoFocus
              />
              <button
                onClick={handleSubmitComment}
                disabled={isSaving}
                className="bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1 transition-colors"
              >
                {isSaving ? (
                  <Loader2 size={10} className="animate-spin" />
                ) : (
                  <Send size={10} />
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModuleFeedback;

