import { apiRequest } from '../client';
import { ExplorationNode, AnalysisRequest, Session } from '../../../types/exploration';

/**
 * Normalization point: Maps backend field names (snake_case) to frontend interface (camelCase)
 * and provides typesafe API calls.
 */

function mapNode(backendNode: any): ExplorationNode {
  return {
    id: backendNode.id,
    parentId: backendNode.parent_id,
    sessionId: backendNode.session_id,
    triggerType: backendNode.trigger_type,
    triggerInput: backendNode.trigger_input,
    chartContext: backendNode.chart_context,
    status: backendNode.status,
    plotlyFigure: backendNode.plotly_figure,
    interpretation: backendNode.interpretation,
    suggestions: backendNode.suggestions || [],
    errorLog: backendNode.error_log,
    children: backendNode.children || [],
    createdAt: backendNode.created_at,
  };
}

function mapSession(backendSession: any): Session {
  return {
    id: backendSession.id,
    datasetName: backendSession.dataset_name,
    datasetPath: backendSession.dataset_path,
    kernelId: backendSession.kernel_id,
    rootNodeId: backendSession.root_node_id,
    createdAt: backendSession.created_at,
    lastActivity: backendSession.last_activity,
  };
}

export const AnalysisService = {
  async createSession(file: File): Promise<Session> {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await apiRequest<any>('/sessions', {
      method: 'POST',
      body: formData,
    });
    return mapSession(res);
  },

  async analyze(request: AnalysisRequest): Promise<ExplorationNode> {
    const body = {
      session_id: request.sessionId,
      trigger_type: request.triggerType,
      trigger_input: request.triggerInput,
      parent_id: request.parentId,
      chart_context: request.chartContext,
    };

    const res = await apiRequest<any>(`/sessions/${request.sessionId}/analyze`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
    return mapNode(res.node);
  },

  async getNode(sessionId: string, nodeId: string): Promise<ExplorationNode> {
    const res = await apiRequest<any>(`/sessions/${sessionId}/nodes/${nodeId}`);
    return mapNode(res);
  },
};
