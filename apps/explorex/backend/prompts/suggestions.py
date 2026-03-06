coder_template = """
Genera hasta 3 sugerencias de análisis siguientes para el dataset '{dataset_hash}'.
Schema: {schema}
Prompt actual: {prompt}

Devuelve un JSON con:
{{
  "suggestions": [
    {{"title": "título corto 1", "prompt": "pregunta para seguir analizando"}},
    {{"title": "título corto 2", "prompt": "pregunta para seguir analizando"}},
    {{"title": "título corto 3", "prompt": "pregunta para seguir analizando"}}
  ]
}}
Todo en español.
"""

interpreter_template = """
Presenta estas sugerencias al usuario de forma amigable.
Sugerencias: {prompt}
"""
