import { useEffect, useState, useRef } from 'react';
import { api } from '@/services/api';

interface StreamingTextProps {
  sessionId: string;
  nodeId: string;
  fallbackText: string;
}

export function StreamingText({ sessionId, nodeId, fallbackText }: StreamingTextProps) {
  const [text, setText] = useState('');
  const [done, setDone] = useState(false);
  const attempted = useRef(false);

  useEffect(() => {
    if (attempted.current) return;
    attempted.current = true;

    let es: EventSource;
    try {
      es = api.streamNode(sessionId, nodeId);

      es.onmessage = (event) => {
        const data = event.data;
        if (data === '[DONE]') {
          es.close();
          setDone(true);
          return;
        }
        setText((prev) => prev + data);
      };

      es.onerror = () => {
        es.close();
        setDone(true);
      };
    } catch {
      setDone(true);
    }

    return () => {
      es?.close();
    };
  }, [sessionId, nodeId]);

  const displayText = done && !text ? fallbackText : text || fallbackText;

  return (
    <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
      {displayText}
      {!done && text && <span className="animate-pulse text-primary">▊</span>}
    </div>
  );
}
