import json
import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class ParsedResult(BaseModel):
    plotly_figure: Dict[str, Any]
    statistics: Dict[str, Any]
    computed_values: Dict[str, Any]
    chart_description: str
    data_warnings: List[str]

def parse(kernel_stdout: str) -> ParsedResult:
    """
    Busca un bloque JSON en el stdout del kernel y lo parsea.
    """
    # Intentar encontrar el último bloque JSON { ... }
    # Esto es más robusto si el código imprimió otras cosas
    matches = re.findall(r'\{.*\}', kernel_stdout, re.DOTALL)
    if not matches:
        raise ValueError("No JSON object found in kernel output")
    
    # Tomamos el último match que parezca un JSON válido
    for match in reversed(matches):
        try:
            data = json.loads(match)
            # Validar campos mínimos requeridos
            required = ["plotly_figure", "statistics", "computed_values", "chart_description", "data_warnings"]
            if all(k in data for k in required):
                return ParsedResult(**data)
        except json.JSONDecodeError:
            continue
            
    raise ValueError("Could not find a valid result JSON in kernel output")

def convert_matplotlib_to_plotly(fig: Any) -> Dict[str, Any]:
    """
    Convierte una figura de matplotlib a un diccionario compatible con Plotly.
    """
    try:
        import plotly.tools as tls
        plotly_fig = tls.mpl_to_plotly(fig)
        return plotly_fig.to_dict()
    except Exception:
        # Fallback si no se puede convertir o no está instalado
        return {"data": [], "layout": {"title": "Conversion failed"}}
