import asyncio
import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional

async def run_analysis(
    session_id: str, 
    prompt: str, 
    modality: str = "plan", 
    notebook_path: Optional[str] = None
) -> Dict[str, Any]:
    """Real implementation of Sphinx analysis using sphinx-cli.
    """
    sphinx_api_key = os.getenv("SPHINX_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    jupyter_url = os.getenv("JUPYTER_SERVER_URL", "http://localhost:8888")
    jupyter_token = os.getenv("JUPYTER_SERVER_TOKEN", "")

    if not sphinx_api_key:
        raise ValueError("SPHINX_API_KEY not found in environment")

    # Define the output schema to match ExplorationNode requirements
    # We ask for plotly_figure as a string/object that we can parse
    output_schema = {
        "plotly_figure_json": {
            "type": "string",
            "description": "Plotly JSON figure as a string. Generá este gráfico usando matplotlib internamente y convertilo a JSON."
        },
        "interpretation": {
            "type": "string", 
            "description": "Interpretación clara en español de los resultados, sin mencionar código Python."
        },
        "suggestions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Exactamente 3 preguntas de seguimiento específicas a los datos encontrados."
        },
        "data_context_json": {
            "type": "string",
            "description": "Contexto técnico de los datos analizados (métricas clave, filtros aplicados) en formato JSON string."
        }
    }

    env = os.environ.copy()
    env["SPHINX_API_KEY"] = sphinx_api_key
    if openrouter_api_key:
        env["OPENROUTER_API_KEY"] = openrouter_api_key
    
    # Intento de mitigar el error de punycode en Node.js 20+
    # Nota: punycode está deprecado pero algunos paquetes lo usan con trailing slash 'punycode/'
    # Agregamos la ruta global de npm a NODE_PATH para que encuentre punycode/node_modules/punycode
    env["NODE_OPTIONS"] = "--no-deprecation"
    app_data_roaming = os.getenv("APPDATA")
    if app_data_roaming:
        npm_node_modules = os.path.join(app_data_roaming, "npm", "node_modules")
        punycode_path = os.path.join(npm_node_modules, "punycode")
        current_node_path = env.get("NODE_PATH", "")
        env["NODE_PATH"] = f"{punycode_path}{os.pathsep}{npm_node_modules}{os.pathsep}{current_node_path}"

    cmd = [
        "sphinx-cli", "chat",
        "--prompt", prompt,
        "--jupyter-server-url", jupyter_url,
        "--jupyter-server-token", jupyter_token,
        "--output-schema", json.dumps(output_schema),
        "--no-package-installation" # Assume environment is already setup
    ]

    if notebook_path:
        cmd.extend(["--notebook-filepath", notebook_path])
    
    # Sphinx-cli doesn't have a direct --modality flag in help, but we can 
    # influence behavior via prompt or rules if needed. 
    # For now, we follow the CLI chat command.

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode('latin-1').strip() or stdout.decode('latin-1').strip()
        raise RuntimeError(f"Sphinx analysis failed (code {process.returncode}): {error_msg}")

    try:
        # The output structured JSON should be in stdout
        output_str = stdout.decode('latin-1', errors='replace').strip()
        # Find the last JSON block in case there's logging noise
        # Buscamos el inicio '{' y el final '}' considerando que el CLI puede imprimir varios objetos
        # o logs antes del JSON final.
        
        # Primero intentamos parsear todo si es un JSON válido directo
        try:
            result = json.loads(output_str)
        except json.JSONDecodeError:
            # Si falla, buscamos el primer '{' y el último '}'
            start_idx = output_str.find('{')
            end_idx = output_str.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = output_str[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                raise ValueError(f"Could not find JSON in Sphinx output: {output_str}")
            
        # Ensure mandatory fields exist
        # Try to parse stringified JSONs
        if "plotly_figure_json" in result and result["plotly_figure_json"]:
            try:
                result["plotly_figure"] = json.loads(result["plotly_figure_json"])
            except Exception:
                result["plotly_figure"] = {"data": [], "layout": {"title": "Error al parsear gráfico"}}
        
        if "data_context_json" in result and result["data_context_json"]:
            try:
                result["data_context"] = json.loads(result["data_context_json"])
            except Exception:
                result["data_context"] = {}

        if "plotly_figure" not in result:
            result["plotly_figure"] = {"data": [], "layout": {"title": "Sin datos"}}
        if "interpretation" not in result:
            result["interpretation"] = "No se pudo generar una interpretación."
        if "suggestions" not in result:
            result["suggestions"] = []
        if "data_context" not in result:
            result["data_context"] = {}
            
        return result

    except Exception as e:
        raw_out = stdout.decode('latin-1', errors='replace')
        raise RuntimeError(f"Failed to parse Sphinx output: {str(e)}\nRaw output: {raw_out}")
