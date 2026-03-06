import { AlertTriangle } from 'lucide-react';

interface DataWarningsProps {
  warnings: string[];
}

export function DataWarnings({ warnings }: DataWarningsProps) {
  return (
    <div className="space-y-2">
      {warnings.map((w, i) => (
        <div
          key={i}
          className="flex items-start gap-2 bg-yellow-500/10 border border-yellow-500/20 text-yellow-200 rounded-lg px-4 py-3 text-sm"
        >
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-yellow-400" />
          <span>{w}</span>
        </div>
      ))}
    </div>
  );
}
