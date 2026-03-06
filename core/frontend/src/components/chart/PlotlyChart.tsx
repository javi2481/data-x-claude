import React, { useCallback } from 'react';
import Plotly from 'react-plotly.js';
import { chartClickToPrompt } from '../../lib/chartClickToPrompt';

interface PlotlyChartProps {
  figure: any;
  parentQuestion: string;
  onDrillDown: (prompt: string, context: any) => void;
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({ figure, parentQuestion, onDrillDown }) => {
  const handlePlotClick = useCallback((event: any) => {
    const point = event.points?.[0];
    if (!point) return;

    // Extraer etiquetas y valores según el tipo de gráfico
    const clickedLabel = point.label || point.x || point.text || 'valor';
    const clickedValue = point.value || point.y || point.z || '';
    const traceName = point.data?.name;

    const prompt = chartClickToPrompt({
      parentQuestion,
      clickedLabel,
      clickedValue,
      traceName
    });

    onDrillDown(prompt, {
      clickedLabel,
      clickedValue,
      traceName,
      fullPointData: point
    });
  }, [parentQuestion, onDrillDown]);

  return (
    <div className="w-full h-full min-h-[400px]">
      <Plotly
        data={figure.data || []}
        layout={{
          ...figure.layout,
          autosize: true,
          margin: { l: 40, r: 20, t: 40, b: 40 },
          hovermode: 'closest'
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
        onClick={handlePlotClick}
        config={{
          responsive: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['select2d', 'lasso2d']
        }}
      />
    </div>
  );
};
