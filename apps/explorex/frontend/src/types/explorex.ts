export interface ExplorationNode {
  id: string;
  parentId: string | null;
  sessionId: string;
  triggerType: 'auto' | 'question' | 'click' | 'suggestion';
  triggerInput: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  output?: {
    plotlyFigure?: object;
    interpretation?: string;
    suggestions?: string[];
    auditSummary?: string;
    nodeDocument?: string;
    generatedCode?: string;
    reviewedCode?: string;
    dataWarnings?: string[];
  };
  cached: boolean;
  children: string[];
  createdAt: string;
}

export interface Session {
  id: string;
  fileName: string;
  createdAt: string;
}

export interface AnalyzeRequest {
  triggerType: 'auto' | 'question' | 'click' | 'suggestion';
  triggerInput: string;
  parentNodeId?: string;
}

export interface AnalyzeResponse {
  nodeId: string;
  status: string;
}

export type NodeStatus = ExplorationNode['status'];
export type TriggerType = ExplorationNode['triggerType'];

export const TRIGGER_ICONS: Record<TriggerType, string> = {
  auto: '⚡',
  question: '💬',
  click: '🖱️',
  suggestion: '💡',
};

export const PIPELINE_STEPS = [
  'Generando código...',
  'Revisando código...',
  'Ejecutando análisis...',
  'Interpretando resultados...',
] as const;
