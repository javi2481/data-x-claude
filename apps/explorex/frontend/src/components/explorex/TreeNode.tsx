import { useState } from 'react';
import { ChevronRight, Loader2 } from 'lucide-react';
import { useSessionStore } from '@/stores/sessionStore';
import { TRIGGER_ICONS } from '@/types/explorex';
import { SidebarMenuItem, SidebarMenuButton } from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

interface TreeNodeProps {
  nodeId: string;
  depth: number;
}

export function TreeNode({ nodeId, depth }: TreeNodeProps) {
  const node = useSessionStore((s) => s.nodes[nodeId]);
  const activeNodeId = useSessionStore((s) => s.activeNodeId);
  const setActiveNode = useSessionStore((s) => s.setActiveNode);
  const nodes = useSessionStore((s) => s.nodes);
  const [expanded, setExpanded] = useState(true);

  if (!node) return null;

  const hasChildren = node.children.length > 0;
  const isActive = activeNodeId === nodeId;
  const isRunning = node.status === 'running' || node.status === 'pending';
  const icon = TRIGGER_ICONS[node.triggerType];

  const label =
    node.triggerInput.length > 40
      ? node.triggerInput.slice(0, 40) + '...'
      : node.triggerInput || 'Análisis automático';

  return (
    <>
      <SidebarMenuItem>
        <SidebarMenuButton
          onClick={() => setActiveNode(nodeId)}
          className={cn(
            'w-full justify-start gap-1 text-xs',
            isActive && 'bg-accent text-accent-foreground font-medium'
          )}
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
        >
          {hasChildren && (
            <button
              onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
              className="shrink-0"
            >
              <ChevronRight
                className={cn('h-3 w-3 transition-transform', expanded && 'rotate-90')}
              />
            </button>
          )}
          {!hasChildren && <span className="w-3" />}
          <span className="shrink-0">{icon}</span>
          {isRunning && <Loader2 className="h-3 w-3 animate-spin shrink-0 text-primary" />}
          <span className="truncate">{label}</span>
        </SidebarMenuButton>
      </SidebarMenuItem>

      {hasChildren && expanded &&
        node.children
          .filter((cid) => nodes[cid])
          .map((cid) => <TreeNode key={cid} nodeId={cid} depth={depth + 1} />)}
    </>
  );
}
