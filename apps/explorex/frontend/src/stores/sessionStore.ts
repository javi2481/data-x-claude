import { create } from 'zustand';
import type { ExplorationNode, Session } from '@/types/explorex';

interface SessionState {
  session: Session | null;
  nodes: Record<string, ExplorationNode>;
  rootNodeIds: string[];
  activeNodeId: string | null;
  loading: boolean;
  error: string | null;
  technicalMode: boolean;

  setSession: (session: Session) => void;
  setNodes: (nodes: ExplorationNode[]) => void;
  updateNode: (node: ExplorationNode) => void;
  setActiveNode: (id: string | null) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  toggleTechnicalMode: () => void;
  reset: () => void;
  completedNodeCount: () => number;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  session: null,
  nodes: {},
  rootNodeIds: [],
  activeNodeId: null,
  loading: false,
  error: null,
  technicalMode: false,

  setSession: (session) => set({ session }),

  setNodes: (nodeList) => {
    const nodes: Record<string, ExplorationNode> = {};
    const rootNodeIds: string[] = [];
    nodeList.forEach((n) => {
      nodes[n.id] = n;
      if (!n.parentId) rootNodeIds.push(n.id);
    });
    set({ nodes, rootNodeIds });
  },

  updateNode: (node) =>
    set((s) => ({
      nodes: { ...s.nodes, [node.id]: node },
      rootNodeIds: !node.parentId && !s.rootNodeIds.includes(node.id)
        ? [...s.rootNodeIds, node.id]
        : s.rootNodeIds,
    })),

  setActiveNode: (id) => set({ activeNodeId: id }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  toggleTechnicalMode: () => set((s) => ({ technicalMode: !s.technicalMode })),
  reset: () =>
    set({
      session: null,
      nodes: {},
      rootNodeIds: [],
      activeNodeId: null,
      loading: false,
      error: null,
    }),

  completedNodeCount: () =>
    Object.values(get().nodes).filter((n) => n.status === 'completed').length,
}));
