import os
import asyncio
import json
from typing import Dict, Any, Optional
from jupyter_client import AsyncKernelManager
from pydantic import BaseModel

class KernelOutput(BaseModel):
    stdout: str
    stderr: str
    success: bool
    results: Dict[str, Any] = {}

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
        ext = os.path.splitext(clean_path)[1].lower()
        
        if ext == ".csv":
            read_cmd = f"pd.read_csv('{clean_path}')"
        elif ext in [".xlsx", ".xls"]:
            read_cmd = f"pd.read_excel('{clean_path}')"
        else:
            raise ValueError(f"Unsupported dataset extension: {ext}")
            
        code = f"import pandas as pd\ndf = {read_cmd}"
        result = await self.execute(kernel_id, code)
        if not result.success:
            raise RuntimeError(f"Failed to load dataset: {result.stderr}")
            
        self.loaded_datasets[kernel_id] = True

    async def execute(self, kernel_id: str, code: str, timeout: int = 60) -> KernelOutput:
        """Ejecuta código en el kernel y devuelve la salida y variables resultantes."""
        client = self.clients.get(kernel_id)
        if not client:
            raise ValueError(f"Kernel {kernel_id} not found")

        # Limpieza de código por seguridad: extraer solo código Python válido
        code = code.strip()
        
        # Eliminar bloques markdown si aparecen
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
            
        # Si aún queda texto antes del código (caso del REVIEWER verborrágico o CODER descuidado)
        lines = code.splitlines()
        first_code_line = -1
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if (stripped_line.startswith(("import ", "from ", "fig =", "result =", "print(", "df", "df.", "df[")) or 
                "=" in stripped_line):
                
                if i == 0 or not lines[i-1].strip() or lines[i-1].strip().startswith("#"):
                    first_code_line = i
                    break
        
        if first_code_line != -1:
            code = "\n".join(lines[first_code_line:])
        
        code = code.strip()

        # Inyectar supresión de warnings (Pandas 4 mitigation)
        suppression_prefix = (
            "import warnings\n"
            "warnings.filterwarnings('ignore')\n"
            "import pandas as pd\n"
            "try:\n"
            "    pd.options.mode.future_infer_string = False\n"
            "except Exception: pass\n\n"
        )
        full_code = suppression_prefix + code

        # Enviar comando de ejecución
        msg_id = client.execute(full_code)
        stdout = []
        stderr = []
        
        # Procesar mensajes del kernel
        while True:
            try:
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
                    # Log clear error info
                    error_msg = f"Kernel Error: {content['ename']}: {content['evalue']}\n"
                    error_msg += "\n".join(content['traceback'])
                    stderr.append(error_msg)
                
                if msg_type == 'status' and content['execution_state'] == 'idle':
                    break
            except asyncio.TimeoutError:
                stderr.append("Execution timed out")
                break

        # Extraer variables 'result' y 'result_summary' si existen
        results = {}
        if len(stderr) == 0:
            # Usamos una inspección robusta con delimitadores claros
            inspect_code = (
                "import json\n"
                "print('__RESULT_START__')\n"
                "print(result if 'result' in globals() else 'null')\n"
                "print('__RESULT_END__')\n"
                "print('__SUMMARY_START__')\n"
                "print(json.dumps(result_summary) if 'result_summary' in globals() else '{}')\n"
                "print('__SUMMARY_END__')"
            )
            client.execute(inspect_code)
            
            collected_stdout = []
            # Esperar la salida de la inspección
            while True:
                try:
                    msg = await client.get_iopub_msg(timeout=5)
                    if msg['msg_type'] == 'stream' and msg['content']['name'] == 'stdout':
                        collected_stdout.append(msg['content']['text'])
                    
                    if msg['msg_type'] == 'status' and msg['content']['execution_state'] == 'idle':
                        break
                except asyncio.TimeoutError:
                    break
            
            full_inspect_out = "".join(collected_stdout)
            
            try:
                # Extraer Result
                if "__RESULT_START__" in full_inspect_out and "__RESULT_END__" in full_inspect_out:
                    res_part = full_inspect_out.split("__RESULT_START__")[1].split("__RESULT_END__")[0].strip()
                    if res_part != "null":
                        try:
                            results['result'] = json.loads(res_part)
                        except:
                            results['result'] = res_part
                
                # Extraer Summary
                if "__SUMMARY_START__" in full_inspect_out and "__SUMMARY_END__" in full_inspect_out:
                    sum_part = full_inspect_out.split("__SUMMARY_START__")[1].split("__SUMMARY_END__")[0].strip()
                    results['result_summary'] = json.loads(sum_part)
            except Exception as e:
                print(f"Error parsing kernel results: {e}")

        return KernelOutput(
            stdout="".join(stdout),
            stderr="".join(stderr),
            success=len(stderr) == 0,
            results=results
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
