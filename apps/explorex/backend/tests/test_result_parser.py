import pytest
import json
from . import result_parser

def test_parse_valid_json():
    valid_data = {
        "plotly_figure": {"data": [], "layout": {}},
        "statistics": {"mean": 10},
        "computed_values": {"total": 100},
        "chart_description": "Un gráfico de barras",
        "data_warnings": ["Outliers detected"]
    }
    stdout = f"Otras cosas impresas\n{json.dumps(valid_data)}\nMás ruido"
    
    result = result_parser.parse(stdout)
    assert result.statistics["mean"] == 10
    assert result.chart_description == "Un gráfico de barras"

def test_parse_invalid_json():
    stdout = "No hay json aqui"
    with pytest.raises(ValueError, match="No JSON object found"):
        result_parser.parse(stdout)

def test_parse_partial_json():
    # JSON pero sin los campos requeridos
    partial_data = {"only": "one field"}
    stdout = json.dumps(partial_data)
    with pytest.raises(ValueError, match="Could not find a valid result JSON"):
        result_parser.parse(stdout)

def test_convert_matplotlib_to_plotly_fallback():
    # Sin una figura real, debería devolver el fallback
    res = result_parser.convert_matplotlib_to_plotly(None)
    assert "layout" in res
    assert res["data"] == []
