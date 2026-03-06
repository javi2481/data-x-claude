import { useState, useCallback } from 'react';
import { Send } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';
import { useSessionStore } from '@/stores/sessionStore';

export function QuestionInput() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const session = useSessionStore((s) => s.session);
  const activeNodeId = useSessionStore((s) => s.activeNodeId);
  const { updateNode, setActiveNode } = useSessionStore();

  const handleSubmit = useCallback(async () => {
    if (!question.trim() || !session) return;
    setLoading(true);
    try {
      const res = await api.analyze(session.id, {
        triggerType: 'question',
        triggerInput: question.trim(),
        parentNodeId: activeNodeId || undefined,
      });
      const newNode = await api.getNode(session.id, res.nodeId);
      updateNode(newNode);
      setActiveNode(newNode.id);
      setQuestion('');
    } catch {
      // error handled by store polling
    } finally {
      setLoading(false);
    }
  }, [question, session, activeNodeId, updateNode, setActiveNode]);

  return (
    <div className="flex gap-2 max-w-4xl mx-auto">
      <Input
        placeholder="Haz una pregunta sobre tus datos..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
        disabled={loading || !session}
        className="flex-1"
      />
      <Button
        size="icon"
        onClick={handleSubmit}
        disabled={loading || !question.trim() || !session}
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
}
