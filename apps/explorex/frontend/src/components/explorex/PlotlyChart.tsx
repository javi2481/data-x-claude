import { useCallback } from 'react';
import Plot from 'react-plotly.js';
import { api } from '@/services/api';
import { useSessionStore } from '@/stores/sessionStore';

interface PlotlyChartProps {
  figure: any;
  sessionId: string;
  parentNodeId: string;
}

const DARK_LAYOUT = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#e2e8f0' },
  xaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
  yaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
  margin: { t: 40, r: 20, b: 40, l: 60 },
};

export function PlotlyChart({ figure, sessionId, parentNodeId }: PlotlyChartProps) {
  const { updateNode, setActiveNode } = useSessionStore();

  const handleClick = useCallback(async (event: any) => {
    const point = event.points?.[0];
    if (!point) return;

    const clickLabel = point.label || point.x || String(point.pointIndex);

    try {
      const res = await api.analyze(sessionId, {
        triggerType: 'click',
        triggerInput: String(clickLabel),
        parentNodeId,
      });
      const newNode = await api.getNode(sessionId, res.nodeId);
      updateNode(newNode);
      setActiveNode(newNode.id);
    } catch {
      // silently fail click drill-downs
    }
  }, [sessionId, parentNodeId, updateNode, setActiveNode]);

  const layout = {
    ...figure.layout,
    ...DARK_LAYOUT,
    ...(figure.layout || {}),
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { ...DARK_LAYOUT.font, ...(figure.layout?.font || {}) },
  };

  return (
    <div className="w-full rounded-lg bg-card border border-border p-4">
      <Plot
        data={figure.data || []}
        layout={layout}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '400px' }}
        onClick={handleClick}
      />
    </div>
  );
}
