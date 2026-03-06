import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { api } from '@/services/api';
import { useSessionStore } from '@/stores/sessionStore';

const ACCEPTED = ['.csv', '.xlsx', '.xls'];
const MAX_SIZE = 50 * 1024 * 1024; // 50MB

export default function UploadPage() {
  const navigate = useNavigate();
  const { setSession, setNodes, setActiveNode } = useSessionStore();
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const validate = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED.includes(ext)) return 'Formato no soportado. Usa archivos CSV o Excel (.xlsx, .xls).';
    if (file.size > MAX_SIZE) return 'El archivo es demasiado grande. El tamaño máximo es 50 MB.';
    return null;
  };

  const handleFile = useCallback(async (file: File) => {
    const err = validate(file);
    if (err) { setError(err); return; }
    setError(null);
    setUploading(true);
    setProgress(20);
    try {
      setProgress(50);
      const session = await api.createSession(file);
      setSession(session);
      setProgress(80);
      const nodes = await api.getNodes(session.id);
      setNodes(nodes);
      if (nodes.length > 0) setActiveNode(nodes[0].id);
      setProgress(100);
      navigate('/explorer');
    } catch {
      setError('No se pudo cargar el archivo. Verifica que el backend esté disponible e intenta de nuevo.');
    } finally {
      setUploading(false);
    }
  }, [navigate, setSession, setNodes, setActiveNode]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background p-4">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-foreground tracking-tight">
          Explorex
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">
          Sube tu archivo de datos y descubre insights automáticamente
        </p>
      </div>

      <Card className="w-full max-w-lg border-dashed border-2 border-border bg-card">
        <CardContent className="p-0">
          <div
            className={`flex flex-col items-center justify-center p-12 rounded-lg transition-colors cursor-pointer ${
              dragging ? 'bg-accent/50 border-primary' : 'hover:bg-accent/30'
            }`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={onFileInput}
              disabled={uploading}
            />
            {uploading ? (
              <div className="w-full space-y-4">
                <FileSpreadsheet className="mx-auto h-12 w-12 text-primary animate-pulse" />
                <p className="text-foreground text-center font-medium">Cargando archivo...</p>
                <Progress value={progress} className="h-2" />
              </div>
            ) : (
              <>
                <Upload className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-foreground font-medium text-lg">
                  Arrastra tu archivo aquí
                </p>
                <p className="text-muted-foreground text-sm mt-1">
                  o haz clic para seleccionar
                </p>
                <p className="text-muted-foreground text-xs mt-3">
                  CSV, Excel (.xlsx, .xls) — máx. 50 MB
                </p>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="mt-4 flex items-center gap-2 text-destructive bg-destructive/10 px-4 py-3 rounded-lg max-w-lg w-full">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      <Button variant="ghost" className="mt-6 text-muted-foreground" disabled>
        Versión beta
      </Button>
    </div>
  );
}
