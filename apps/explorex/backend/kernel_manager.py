import os
import asyncio
from typing import Dict, Any, Optional
from jupyter_client import AsyncKernelManager
from pydantic import BaseModel

class KernelOutput(BaseModel):
    stdout: str
    stderr: str
    success: bool

class KernelManager:
    """Gestiona el ciclo de vida de los kernels de Jupyter por sesión."""
    
    def __init__(self):
        self.kernels: Dict[str, AsyncKernelManager] = {}
        self.clients: Dict[str, Any] = {}
        self.loaded_datasets: Dict[str, bool] = {}

    async def start_kernel(self, session_id: str) -> str:
        """Inicia un nuevo kernel para la sesión."""
        if session_id in self.kernels:
            return session_id # Reusar si ya existe
            
        km = AsyncKernelManager(kernel_name='python3')
        await km.start_kernel()
        kc = km.client()
        kc.start_channels()
        await kc.wait_for_ready()
        
        self.kernels[session_id] = km
        self.clients[session_id] = kc
        self.loaded_datasets[session_id] = False
        return session_id

    async def load_dataset(self, kernel_id: str, dataset_path: str) -> None:
        """Carga el dataset en memoria (UNA sola vez por kernel)."""
        if self.loaded_datasets.get(kernel_id):
            return # Ya cargado

        clean_path = dataset_path.replace("\\", "/")
        code = f"import pandas as pd\ndf = pd.read_csv('{clean_path}')"
        result = await self.execute(kernel_id, code)
        if not result.success:
            raise RuntimeError(f"Failed to load dataset: {result.stderr}")
            
        self.loaded_datasets[kernel_id] = True

    async def execute(self, kernel_id: str, code: str, timeout: int = 30) -> KernelOutput:
        """Ejecuta código en el kernel y devuelve la salida."""
        client = self.clients.get(kernel_id)
        if not client:
            raise ValueError(f"Kernel {kernel_id} not found")

        msg_id = client.execute(code)
        stdout = []
        stderr = []
        
        # Procesar mensajes del kernel
        while True:
            try:
                # Usar asyncio.wait_for para timeout global de la ejecución
                msg = await client.get_iopub_msg(timeout=timeout)
                msg_type = msg['msg_type']
                content = msg['content']

                if msg_type == 'stream':
                    if content['name'] == 'stdout':
                        stdout.append(content['text'])
                    else:
                        stderr.append(content['text'])
                elif msg_type == 'execute_result':
                    stdout.append(content['data'].get('text/plain', ''))
                elif msg_type == 'error':
                    stderr.append("\n".join(content['traceback']))
                
                # Verificar si la ejecución terminó en el canal shell
                # En jupyter-client asíncrono, los mensajes de status 'idle' indican fin
                if msg_type == 'status' and content['execution_state'] == 'idle':
                    # Verificar si este idle corresponde a nuestro execute
                    # En una implementación simple, esperamos el primer idle después del execute_reply
                    break
            except asyncio.TimeoutError:
                stderr.append("Execution timed out")
                break

        return KernelOutput(
            stdout="".join(stdout),
            stderr="".join(stderr),
            success=len(stderr) == 0
        )

    async def restart(self, kernel_id: str) -> None:
        """Reinicia el kernel."""
        km = self.kernels.get(kernel_id)
        if km:
            await km.restart_kernel()
            self.loaded_datasets[kernel_id] = False

    async def stop(self, kernel_id: str) -> None:
        """Detiene y elimina el kernel."""
        km = self.kernels.pop(kernel_id, None)
        kc = self.clients.pop(kernel_id, None)
        self.loaded_datasets.pop(kernel_id, None)
        
        if kc:
            kc.stop_channels()
        if km:
            await km.shutdown_kernel()
