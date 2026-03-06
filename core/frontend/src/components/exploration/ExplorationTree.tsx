import React from 'react';
import { useExplorationStore } from '../../store/explorationStore';
import { AnalysisNode } from './AnalysisNode';

export const ExplorationTree: React.FC = () => {
  const { rootNodeId, nodes } = useExplorationStore();

  if (!rootNodeId || !nodes[rootNodeId]) {
    return (
      <div className="p-4 text-gray-400 text-sm italic">
        Sube un dataset para ver la exploración.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-gray-50 border-r border-gray-200 w-64">
      <div className="p-4 border-b border-gray-200 bg-white">
        <h2 className="font-semibold text-gray-700">Exploración</h2>
      </div>
      <div className="py-2">
        <AnalysisNode node={nodes[rootNodeId]} level={0} />
      </div>
    </div>
  );
};
