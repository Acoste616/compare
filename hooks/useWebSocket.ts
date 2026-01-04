import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../store';
import { Message, Language } from '../types';
import { mapBackendToFrontend } from './analysisMapper';

/**
 * WebSocket Hook for Real-time Chat & Analysis
 */
export function useWebSocket(sessionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const { updateAnalysis, addMessage, setAnalyzing, setGothamData, language } = useStore();
  const reconnectTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    // Don't connect if no session
    if (!sessionId) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    // Get backend URL from environment or use default
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
    const wsUrl = backendUrl.replace('http://', 'ws://').replace('https://', 'wss://');
    const fullWsUrl = `${wsUrl}/ws/chat/${sessionId}`;

    console.log(`[WebSocket] Connecting to ${fullWsUrl}`);

    const connect = () => {
      try {
        const ws = new WebSocket(fullWsUrl);

        ws.onopen = () => {
          console.log('[WebSocket] Connected successfully');
        };

        ws.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);

            // 🔥 AGGRESSIVE DEBUG LOGGING
            console.log(`%c[WS] 📨 Received: ${payload.type}`, 'color: #00ff00; font-weight: bold;');
            console.log('[WS] Full payload:', JSON.stringify(payload, null, 2));

            if (payload.type === 'fast_response') {
              console.log('%c[WS] ⚡ FAST RESPONSE received', 'color: #ffff00; font-weight: bold;');
              const aiMsg: Message = payload.data;
              addMessage(sessionId, aiMsg);
              setAnalyzing(false);
            } else if (payload.type === 'analysis_update') {
              console.log('%c[WS] 🧠 ANALYSIS UPDATE received', 'color: #00ffff; font-weight: bold;');
              console.log('[WS] Raw analysis data:', payload.data);
              // Transform backend data to frontend format
              const mappedData = mapBackendToFrontend(payload.data);
              console.log('[WS] Mapped data for store:', mappedData);
              updateAnalysis(mappedData);
              setAnalyzing(false); // Analysis complete
            } else if (payload.type === 'analysis_status') {
              // Handle analysis status updates (analyzing, skipped, etc.)
              console.log('%c[WS] 📊 ANALYSIS STATUS:', 'color: #ff00ff;', payload.data);
              if (payload.data?.status === 'analyzing') {
                setAnalyzing(true);
              } else {
                setAnalyzing(false);
              }
            } else if (payload.type === 'gotham_update') {
              // Handle GOTHAM Intelligence updates (v4.0)
              console.log('%c[WS] 🔥 GOTHAM UPDATE received', 'color: #ff6600; font-weight: bold;');
              console.log('[WS] GOTHAM data:', payload.data);
              setGothamData(payload.data);
            } else if (payload.type === 'processing') {
              // Handle processing status (thinking indicator)
              console.log('%c[WS] ⏳ PROCESSING...', 'color: #00ffff;');
              setAnalyzing(true);
            } else if (payload.type === 'system_busy') {
              console.log('%c[WS] ⚠️ SYSTEM BUSY - Queue full, retrying...', 'color: #ff0000; font-weight: bold;');
              console.log('[WS] Message:', payload.message);
              // Don't clear existing data - keep showing what we have
              // Optional: Could trigger a toast notification here
            } else if (payload.type === 'analysis_error') {
              console.log('%c[WS] ❌ ANALYSIS ERROR', 'color: #ff0000; font-weight: bold;', payload.error);
              setAnalyzing(false);
            } else {
              console.log('%c[WS] ❓ UNKNOWN TYPE:', 'color: #888888;', payload.type, payload);
            }
          } catch (error) {
            console.error('[WebSocket] Error parsing message:', error);
          }
        };

        ws.onerror = () => {
          // Silent error handling - errors will be logged on close if needed
        };

        ws.onclose = (event) => {
          if (event.code !== 1000 && sessionId) {
            reconnectTimeoutRef.current = window.setTimeout(() => {
              console.log('[WebSocket] Attempting reconnect silently...');
              connect();
            }, 3000);
          }
        };

        wsRef.current = ws;
      } catch (error) {
        console.error('[WebSocket] Failed to create connection:', error);
      }
    };

    connect();

    // Cleanup function
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (wsRef.current) {
        console.log('[WebSocket] Closing connection');
        wsRef.current.close(1000, 'Component unmounting');
        wsRef.current = null;
      }
    };
  }, [sessionId]); // Only re-run when sessionId changes (store functions are stable)


  const sendMessage = useCallback((content: string, lang?: Language) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Include language in the payload - use passed lang or fall back to store language
      const currentLang = lang || language;
      wsRef.current.send(JSON.stringify({
        content,
        language: currentLang
      }));
      console.log(`[WebSocket] Sending message with language: ${currentLang}`);
    } else {
      console.warn("WebSocket not connected, cannot send message");
    }
  }, [language]);

  return { sendMessage };
}
