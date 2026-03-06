import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSessionStore } from '@/stores/sessionStore';
import { api } from '@/services/api';
import { useState } from 'react';

export function ExportButton() {
  const session = useSessionStore((s) => s.session);
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    if (!session) return;
    setLoading(true);
    try {
      await api.exportNotebook(session.id);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button variant="outline" size="sm" onClick={handleExport} disabled={loading}>
      <Download className="h-4 w-4 mr-1" />
      Exportar notebook
    </Button>
  );
}
