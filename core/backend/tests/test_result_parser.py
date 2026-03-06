import pytest
import json
from engine.result_parser import parse_notebook_stdout, matplotlib_to_plotly_dict

def test_parse_notebook_stdout_valid():
    valid_json = {
        "plotly_figure": {"data": [], "layout": {}},
        "interpretation": "Análisis completado",
        "suggestions": ["Sugerencia 1", "Sugerencia 2", "Sugerencia 3"],
        "data_context": {"key": "value"}
    }
    result = parse_notebook_stdout(json.dumps(valid_json))
    assert result["interpretation"] == "Análisis completado"
    assert len(result["suggestions"]) == 3

def test_parse_notebook_stdout_missing_key():
    invalid_json = {"interpretation": "Incompleto"}
    with pytest.raises(KeyError):
        parse_notebook_stdout(json.dumps(invalid_json))

def test_matplotlib_to_plotly_dict_fallback():
    # Sin matplotlib real, debería devolver estructura vacía o fallar graciosamente si tls es None
    # Como lo implementé con try-except import, debería devolver dict vacío si falla
    res = matplotlib_to_plotly_dict(None)
    assert isinstance(res, dict)
    assert "data" in res
