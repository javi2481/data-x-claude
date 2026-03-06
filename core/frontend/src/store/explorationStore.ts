import { create } from 'zustand';
import { ExplorationNode, Session } from '../types/exploration';

interface ExplorationState {
  currentSession: Session | null;
  nodes: Record<string, ExplorationNode>;
  rootNodeId: string | null;
  selectedNodeId: string | null;
  isAnalyzing: boolean;
  error: string | null;

  // Actions
  setSession: (session: Session | null) => void;
  setNodes: (nodes: ExplorationNode[]) => void;
  addNode: (node: ExplorationNode) => void;
  updateNode: (nodeId: string, updates: Partial<ExplorationNode>) => void;
  setSelectedNode: (nodeId: string | null) => void;
  setAnalyzing: (isAnalyzing: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useExplorationStore = create<ExplorationState>((set) => ({
  currentSession: null,
  nodes: {},
  rootNodeId: null,
  selectedNodeId: null,
  isAnalyzing: false,
  error: null,

  setSession: (session) => set({ 
    currentSession: session,
    rootNodeId: session?.rootNodeId || null 
  }),

  setNodes: (nodes) => {
    const nodesMap = nodes.reduce((acc, node) => ({
      ...acc,
      [node.id]: node
    }), {});
    set({ nodes: nodesMap });
  },

  addNode: (node) => set((state) => {
    const newNodes = { ...state.nodes, [node.id]: node };
    
    // Update parent's children list if parent exists
    if (node.parentId && newNodes[node.parentId]) {
      const parent = newNodes[node.parentId];
      if (!parent.children.includes(node.id)) {
        newNodes[node.parentId] = {
          ...parent,
          children: [...parent.children, node.id]
        };
      }
    }

    return {
      nodes: newNodes,
      selectedNodeId: node.id,
      error: null
    };
  }),

  updateNode: (nodeId, updates) => set((state) => ({
    nodes: {
      ...state.nodes,
      [nodeId]: { ...state.nodes[nodeId], ...updates }
    }
  })),

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),

  setAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

  setError: (error) => set({ error }),

  reset: () => set({
    currentSession: null,
    nodes: {},
    rootNodeId: null,
    selectedNodeId: null,
    isAnalyzing: false,
    error: null
  })
}));
