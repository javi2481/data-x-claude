import { PIPELINE_STEPS } from '@/types/explorex';
import { Check, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatusPipelineProps {
  status: 'pending' | 'running';
}

export function StatusPipeline({ status }: StatusPipelineProps) {
  // Simulate pipeline progression based on status
  const activeStep = status === 'pending' ? 0 : 2;

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="space-y-3">
        {PIPELINE_STEPS.map((step, i) => {
          const isDone = i < activeStep;
          const isCurrent = i === activeStep;

          return (
            <div key={i} className="flex items-center gap-3">
              <div
                className={cn(
                  'h-6 w-6 rounded-full flex items-center justify-center shrink-0 text-xs',
                  isDone && 'bg-primary text-primary-foreground',
                  isCurrent && 'bg-primary/20 text-primary border border-primary',
                  !isDone && !isCurrent && 'bg-muted text-muted-foreground'
                )}
              >
                {isDone ? (
                  <Check className="h-3 w-3" />
                ) : isCurrent ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <span>{i + 1}</span>
                )}
              </div>
              <span
                className={cn(
                  'text-sm',
                  isCurrent && 'text-foreground font-medium',
                  isDone && 'text-muted-foreground',
                  !isDone && !isCurrent && 'text-muted-foreground/50'
                )}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
