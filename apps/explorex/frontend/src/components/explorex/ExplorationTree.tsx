import { useSessionStore } from '@/stores/sessionStore';
import { TreeNode } from './TreeNode';
import { SidebarMenu } from '@/components/ui/sidebar';

export function ExplorationTree() {
  const rootNodeIds = useSessionStore((s) => s.rootNodeIds);

  if (rootNodeIds.length === 0) {
    return (
      <p className="text-xs text-muted-foreground px-4 py-2">
        Esperando análisis inicial...
      </p>
    );
  }

  return (
    <SidebarMenu>
      {rootNodeIds.map((id) => (
        <TreeNode key={id} nodeId={id} depth={0} />
      ))}
    </SidebarMenu>
  );
}
