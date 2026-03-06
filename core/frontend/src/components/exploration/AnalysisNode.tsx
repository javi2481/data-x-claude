import React from 'react';
import { ExplorationNode } from '../../types/exploration';
import { useExplorationStore } from '../../store/explorationStore';

interface AnalysisNodeProps {
  node: ExplorationNode;
  level: number;
}

export const AnalysisNode: React.FC<AnalysisNodeProps> = ({ node, level }) => {
  const { selectedNodeId, setSelectedNode, nodes } = useExplorationStore();
  const isSelected = selectedNodeId === node.id;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedNode(node.id);
  };

  return (
    <div className="flex flex-col">
      <div 
        onClick={handleClick}
        className={`
          flex items-center p-2 rounded-md cursor-pointer transition-all mb-1
          ${isSelected ? 'bg-blue-100 text-blue-800 font-medium' : 'hover:bg-gray-100'}
        `}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
      >
        <span className="mr-2 text-gray-400">
          {node.children.length > 0 ? '▼' : '○'}
        </span>
        <span className="truncate text-sm" title={node.triggerInput}>
          {node.triggerInput}
        </span>
        {node.status === 'running' && (
          <span className="ml-2 animate-pulse text-xs text-blue-500">...</span>
        )}
      </div>
      
      {node.children.map(childId => (
        nodes[childId] && (
          <AnalysisNode 
            key={childId} 
            node={nodes[childId]} 
            level={level + 1} 
          />
        )
      ))}
    </div>
  );
};
