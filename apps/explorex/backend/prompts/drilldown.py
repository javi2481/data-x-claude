coder_template = """
Analiza un subconjunto del dataset '{dataset_hash}' basado en este click:
Schema: {schema}
Click: {prompt}
Contexto: {parent_context}

Reglas:
1. Filtra 'df' basándote en el elemento clickeado.
2. Genera un gráfico detallado con Plotly de este subconjunto.
3. El resultado final DEBE ser un JSON con:
   {{
     "plotly_figure": <dict>,
     "statistics": <dict>,
     "computed_values": <dict>,
     "chart_description": "en español",
     "data_warnings": []
   }}
Solo código Python.
"""

reviewer_template = """
Revisa este código de drilldown para este schema: {schema}
Código: {code}
Asegúrate de que filtra correctamente y devuelve el JSON final.
Devuelve solo el código.
"""

interpreter_template = """
Explica el detalle de este elemento clickeado para el usuario final.
Click: {prompt}
Estadísticas: {statistics}
Interpretación en español:
"""
