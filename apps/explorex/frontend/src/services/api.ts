import type { ExplorationNode, Session, AnalyzeRequest, AnalyzeResponse } from '@/types/explorex';

const API_BASE = 'http://127.0.0.1:8001';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  createSession: async (file: File): Promise<Session> => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/sessions`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(`Upload error ${res.status}`);
    return res.json();
  },

  analyze: (sessionId: string, body: AnalyzeRequest): Promise<AnalyzeResponse> =>
    request(`/sessions/${sessionId}/analyze`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getNodes: (sessionId: string): Promise<ExplorationNode[]> =>
    request(`/sessions/${sessionId}/nodes`),

  getNode: (sessionId: string, nodeId: string): Promise<ExplorationNode> =>
    request(`/sessions/${sessionId}/nodes/${nodeId}`),

  getCode: (sessionId: string, nodeId: string): Promise<{ code: string }> =>
    request(`/sessions/${sessionId}/nodes/${nodeId}/code`),

  getDocument: (sessionId: string, nodeId: string): Promise<{ document: string }> =>
    request(`/sessions/${sessionId}/nodes/${nodeId}/document`),

  streamNode: (sessionId: string, nodeId: string): EventSource =>
    new EventSource(`${API_BASE}/sessions/${sessionId}/stream/${nodeId}`),

  exportNotebook: async (sessionId: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/export`);
    if (!res.ok) throw new Error('Export error');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `explorex-${sessionId}.ipynb`;
    a.click();
    URL.revokeObjectURL(url);
  },
};
