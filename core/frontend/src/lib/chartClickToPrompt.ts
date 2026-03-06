interface ChartClickContext {
  parentQuestion: string;
  clickedLabel: string;
  clickedValue: number | string;
  traceName?: string;
}

/**
 * Convierte un evento de click en un gráfico Plotly a un prompt en lenguaje natural
 * para que Sphinx realice un análisis de drill-down.
 */
export function chartClickToPrompt(context: ChartClickContext): string {
  const traceInfo = context.traceName ? ` (serie: ${context.traceName})` : '';
  
  return `En el contexto del análisis "${context.parentQuestion}", 
el usuario hizo click en "${context.clickedLabel}"${traceInfo} con valor ${context.clickedValue}. 
Profundizá en qué factores explican ese resultado específico. 
Usá el DataFrame disponible en memoria (variable df). 
Generá al menos un gráfico con matplotlib y proporcioná una interpretación clara.`;
}
