import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import UploadPage from "./pages/UploadPage";
import ExplorerPage from "./pages/ExplorerPage";
import NotFound from "./pages/NotFound";
import { api } from "./services/api";
import { toast } from "@/hooks/use-toast";

const queryClient = new QueryClient();

function HealthCheck() {
  useEffect(() => {
    api.health().catch(() => {
      toast({
        title: "Backend no disponible",
        description: "No se pudo conectar al servidor. Verifica que esté en ejecución.",
        variant: "destructive",
      });
    });
  }, []);
  return null;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <HealthCheck />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/explorer" element={<ExplorerPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
