from __future__ import annotations
from typing import Any, Dict
import json

try:
    import plotly.tools as tls  # type: ignore
except Exception:  # pragma: no cover
    tls = None  # fallback for environments without plotly installed yet


def parse_notebook_stdout(stdout: str) -> Dict[str, Any]:
    """Parse the final JSON line printed by the notebook.

    Expected keys:
      - plotly_figure (dict)
      - interpretation (str)
      - suggestions (list of 3 strings)
      - data_context (dict)
    """
    data = json.loads(stdout)
    if not isinstance(data, dict):
        raise ValueError("Notebook output must be a JSON object")

    required = ["plotly_figure", "interpretation", "suggestions", "data_context"]
    missing = [k for k in required if k not in data]
    if missing:
        raise KeyError(f"Missing keys in notebook output: {missing}")

    return data


def matplotlib_to_plotly_dict(matplotlib_fig: Any) -> Dict[str, Any]:
    """Convert a matplotlib figure to Plotly JSON dict using mpl_to_plotly.
    Returns an empty Plotly structure if plotly is not available yet or if fig is None.
    """
    if tls is None or matplotlib_fig is None:
        return {"data": [], "layout": {}}
    try:
        plotly_fig = tls.mpl_to_plotly(matplotlib_fig)
        return plotly_fig.to_dict()
    except Exception:
        return {"data": [], "layout": {}}
