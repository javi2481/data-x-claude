import React, { useCallback, useState } from 'react';
import { AnalysisService } from '../../lib/api/services/analysis';
import { useExplorationStore } from '../../store/explorationStore';

export const DatasetUpload: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const { setSession, addNode, setAnalyzing, setError } = useExplorationStore();

  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      // 1. Crear sesión
      const session = await AnalysisService.createSession(file);
      setSession(session);

      // 2. Iniciar análisis inicial automático
      setAnalyzing(true);
      const initialNode = await AnalysisService.analyze({
        sessionId: session.id,
        triggerType: 'auto',
        triggerInput: '¿De qué habla este dataset?'
      });
      
      addNode(initialNode);
    } catch (err: any) {
      setError(err.message || 'Error al subir el dataset');
    } finally {
      setIsUploading(false);
      setAnalyzing(false);
    }
  }, [setSession, addNode, setAnalyzing, setError]);

  return (
    <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
      <h3 className="text-xl font-semibold mb-4">Sube un dataset para comenzar</h3>
      <p className="text-gray-600 mb-6 text-center">
        Arrastra un archivo CSV o haz click para seleccionar. <br />
        Exploraremos los datos automáticamente.
      </p>
      
      <label className={`
        px-6 py-2 rounded-md font-medium cursor-pointer transition-colors
        ${isUploading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'}
      `}>
        {isUploading ? 'Subiendo...' : 'Seleccionar Archivo'}
        <input 
          type="file" 
          className="hidden" 
          accept=".csv" 
          onChange={handleFileUpload}
          disabled={isUploading}
        />
      </label>
      
      {isUploading && (
        <div className="mt-4 flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-sm text-gray-500">Procesando dataset y generando análisis inicial...</span>
        </div>
      )}
    </div>
  );
};
