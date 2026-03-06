import { useSessionStore } from '@/stores/sessionStore';
import { StatusPipeline } from './StatusPipeline';
import { PlotlyChart } from './PlotlyChart';
import { DataWarnings } from './DataWarnings';
import { StreamingText } from './StreamingText';
import { SuggestionChips } from './SuggestionChips';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

export function ResultPanel() {
  const activeNodeId = useSessionStore((s) => s.activeNodeId);
  const node = useSessionStore((s) => (s.activeNodeId ? s.nodes[s.activeNodeId] : null));
  const session = useSessionStore((s) => s.session);
  const technicalMode = useSessionStore((s) => s.technicalMode);

  if (!node || !session) return null;

  const isPending = node.status === 'pending' || node.status === 'running';
  const isFailed = node.status === 'failed';
  const output = node.output;
  const pipelineStatus = node.status as 'pending' | 'running';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Pipeline stepper */}
      {isPending && <StatusPipeline status={pipelineStatus} />}

      {/* Error state */}
      {isFailed && (
        <div className="bg-destructive/10 text-destructive rounded-lg p-4 text-sm">
          Hubo un problema al procesar tu solicitud. Intenta de nuevo.
        </div>
      )}

      {/* Chart */}
      {output?.plotlyFigure && (
        <PlotlyChart
          figure={output.plotlyFigure}
          sessionId={session.id}
          parentNodeId={node.id}
        />
      )}

      {/* Data warnings */}
      {output?.dataWarnings && output.dataWarnings.length > 0 && (
        <DataWarnings warnings={output.dataWarnings} />
      )}

      {/* Interpretation - streaming or static */}
      {node.status === 'completed' && output?.interpretation && (
        <div className="prose prose-invert max-w-none">
          <StreamingText
            sessionId={session.id}
            nodeId={node.id}
            fallbackText={output.interpretation}
          />
        </div>
      )}

      {/* Loading skeleton for interpretation */}
      {isPending && (
        <div className="space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      )}

      {/* Suggestions */}
      {output?.suggestions && output.suggestions.length > 0 && (
        <SuggestionChips
          suggestions={output.suggestions}
          sessionId={session.id}
          parentNodeId={node.id}
        />
      )}

      {/* Audit summary */}
      {output?.auditSummary && (
        <Collapsible>
          <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ChevronDown className="h-4 w-4" />
            Resumen de auditoría
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2 text-sm text-muted-foreground bg-muted/30 p-4 rounded-lg">
            {output.auditSummary}
          </CollapsibleContent>
        </Collapsible>
      )}

      {/* Technical mode: view code */}
      {technicalMode && output?.generatedCode && (
        <Collapsible>
          <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ChevronDown className="h-4 w-4" />
            Ver código
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2">
            <pre className="text-xs bg-muted/50 p-4 rounded-lg overflow-x-auto text-foreground">
              <code>{output.generatedCode}</code>
            </pre>
          </CollapsibleContent>
        </Collapsible>
      )}
    </div>
  );
}
