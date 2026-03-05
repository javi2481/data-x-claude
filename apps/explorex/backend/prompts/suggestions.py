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

reviewer_template = """
Valida que estas sugerencias sean coherentes con el schema: {schema}.
Código/JSON: {code}
Devuelve solo el JSON corregido o validado.
"""

interpreter_template = """
Presenta estas sugerencias al usuario de forma amigable.
Sugerencias: {prompt}
"""
