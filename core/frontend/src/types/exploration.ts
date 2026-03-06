export interface ExplorationNode {
  id: string;
  parentId?: string;
  sessionId: string;
  triggerType: 'auto' | 'question' | 'click' | 'suggestion';
  triggerInput: string;
  chartContext?: Record<string, any>;
  status: 'pending' | 'running' | 'completed' | 'failed';
  plotlyFigure?: any;
  interpretation?: string;
  suggestions: string[];
  errorLog?: string;
  children: string[];
  createdAt: string;
}

export interface Session {
  id: string;
  datasetName: string;
  datasetPath: string;
  kernelId?: string;
  rootNodeId?: string;
  createdAt: string;
  lastActivity: string;
}

export interface AnalysisRequest {
  sessionId: string;
  triggerType: string;
  triggerInput: string;
  parentId?: string;
  chartContext?: Record<string, any>;
}

export interface AnalysisResponse {
  node: ExplorationNode;
}
