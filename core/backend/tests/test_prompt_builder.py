import pytest
from engine.prompt_builder import render

def test_render_success():
    """Renderizado correcto con contexto completo"""
    template = "Analiza {dataset_name} en {dataset_path}"
    context = {"dataset_name": "data.csv", "dataset_path": "/tmp/data.csv"}
    res = render(template, context)
    assert res == "Analiza data.csv en /tmp/data.csv"

def test_render_missing_key():
    """KeyError cuando falta una clave"""
    template = "Analiza {dataset_name} en {dataset_path}"
    context = {"dataset_name": "data.csv"}
    with pytest.raises(KeyError) as excinfo:
        render(template, context)
    assert "Missing required key in prompt context" in str(excinfo.value)
    assert "dataset_path" in str(excinfo.value)

def test_render_multiple_keys():
    """Template con múltiples claves"""
    template = "{role}: {action} {item}"
    context = {"role": "Admin", "action": "delete", "item": "file"}
    res = render(template, context)
    assert res == "Admin: delete file"

def test_render_empty_template():
    """Template vacío"""
    template = ""
    context = {"any": "thing"}
    res = render(template, context)
    assert res == ""

def test_render_no_placeholders():
    """Template sin placeholders"""
    template = "Static text"
    context = {"any": "thing"}
    res = render(template, context)
    assert res == "Static text"
