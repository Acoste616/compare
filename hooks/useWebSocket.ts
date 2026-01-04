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
            console.log(`[WebSocket] Message received:`, payload.type);

            if (payload.type === 'fast_response') {
              const aiMsg: Message = payload.data;
              addMessage(sessionId, aiMsg);
              setAnalyzing(false);
            } else if (payload.type === 'analysis_update') {
              console.log('[WebSocket] Analysis update received:', payload.data);
              // Transform backend data to frontend format
              const mappedData = mapBackendToFrontend(payload.data);
              console.log('[WebSocket] Mapped data:', mappedData);
              updateAnalysis(mappedData);
              setAnalyzing(false); // Analysis complete
            } else if (payload.type === 'analysis_status') {
              // Handle analysis status updates (analyzing, skipped, etc.)
              console.log('[WebSocket] Analysis status:', payload.data);
              if (payload.data?.status === 'analyzing') {
                setAnalyzing(true);
              } else {
                setAnalyzing(false);
              }
            } else if (payload.type === 'gotham_update') {
              // Handle GOTHAM Intelligence updates (v4.0)
              console.log('[WebSocket] 🔥 GOTHAM update received:', payload.data);
              setGothamData(payload.data);
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
