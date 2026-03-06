import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';
import { useSessionStore } from '@/stores/sessionStore';

interface SuggestionChipsProps {
  suggestions: string[];
  sessionId: string;
  parentNodeId: string;
}

export function SuggestionChips({ suggestions, sessionId, parentNodeId }: SuggestionChipsProps) {
  const { updateNode, setActiveNode } = useSessionStore();

  const handleClick = useCallback(async (suggestion: string) => {
    try {
      const res = await api.analyze(sessionId, {
        triggerType: 'suggestion',
        triggerInput: suggestion,
        parentNodeId,
      });
      const newNode = await api.getNode(sessionId, res.nodeId);
      updateNode(newNode);
      setActiveNode(newNode.id);
    } catch {
      // handled by polling
    }
  }, [sessionId, parentNodeId, updateNode, setActiveNode]);

  return (
    <div className="flex flex-wrap gap-2">
      {suggestions.slice(0, 3).map((s, i) => (
        <Button
          key={i}
          variant="outline"
          size="sm"
          className="text-xs"
          onClick={() => handleClick(s)}
        >
          💡 {s}
        </Button>
      ))}
    </div>
  );
}
