import React, { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { SidebarProvider, SidebarTrigger, SidebarInset } from '@/components/ui/sidebar';
import { useSessionStore } from '@/stores/sessionStore';
import { api } from '@/services/api';
import { ExplorationTree } from '@/components/explorex/ExplorationTree';
import { ResultPanel } from '@/components/explorex/ResultPanel';
import { ExportButton } from '@/components/explorex/ExportButton';
import { QuestionInput } from '@/components/explorex/QuestionInput';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from '@/components/ui/sidebar';

export default function ExplorerPage() {
  const navigate = useNavigate();
  const session = useSessionStore((s) => s.session);
  const technicalMode = useSessionStore((s) => s.technicalMode);
  const toggleTechnicalMode = useSessionStore((s) => s.toggleTechnicalMode);
  const completedCount = useSessionStore((s) => s.completedNodeCount());
  const activeNodeId = useSessionStore((s) => s.activeNodeId);
  const setNodes = useSessionStore((s) => s.setNodes);

  useEffect(() => {
    if (!session) { navigate('/'); return; }
    const poll = setInterval(async () => {
      try {
        const nodes = await api.getNodes(session.id);
        setNodes(nodes);
      } catch { /* silently retry */ }
    }, 3000);
    return () => clearInterval(poll);
  }, [session, navigate, setNodes]);

  if (!session) return null;

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <Sidebar collapsible="icon" className="border-r border-border">
          <SidebarHeader className="p-4">
            <h2 className="text-sm font-semibold text-foreground truncate">{session.fileName}</h2>
          </SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Exploración</SidebarGroupLabel>
              <SidebarGroupContent>
                <ExplorationTree />
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>

        <SidebarInset className="flex-1 flex flex-col min-w-0">
          {/* Top bar */}
          <header className="h-14 flex items-center justify-between border-b border-border px-4 shrink-0">
            <div className="flex items-center gap-2">
              <SidebarTrigger />
              <span className="text-sm font-medium text-foreground truncate">
                {session.fileName}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch
                  id="tech-mode"
                  checked={technicalMode}
                  onCheckedChange={toggleTechnicalMode}
                />
                <Label htmlFor="tech-mode" className="text-xs text-muted-foreground cursor-pointer">
                  Modo técnico
                </Label>
              </div>
              {completedCount >= 2 && <ExportButton />}
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1 overflow-y-auto p-6">
            {activeNodeId ? (
              <ResultPanel />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <p>Selecciona un nodo del árbol para ver los resultados</p>
              </div>
            )}
          </main>

          {/* Question input */}
          <div className="border-t border-border p-4 shrink-0">
            <QuestionInput />
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
