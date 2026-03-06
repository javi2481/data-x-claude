coder_template = """
Analiza un subconjunto del dataset '{dataset_hash}' basado en este click:
Schema: {schema}
Click: {prompt}
Contexto: {parent_context}

Reglas de código:
1. El dataset ya está cargado en la variable 'df'. NO lo cargues de nuevo.
2. Filtra 'df' basándote en el elemento clickeado (el valor del click).
3. Usa plotly para generar un gráfico detallado de este subconjunto.
4. Al filtrar por tipos de datos, usa df.select_dtypes(exclude=['number']) para columnas no numéricas o df.select_dtypes(include=['object', 'string']).
5. Evita usar únicamente include=['object'] para prevenir advertencias de compatibilidad.
6. Debes generar EXACTAMENTE dos variables al final de tu ejecución:
   - 'result': El JSON del gráfico Plotly (usa fig.to_json()).
   - 'result_summary': Un diccionario con las métricas, hallazgos clave y contexto del drill-down.

Ejemplo de salida final:
result = fig.to_json()
result_summary = {{
    "metric": value,
    "insight": "descripción del subconjunto",
    "filter_applied": "valor del click"
}}

Respondé ÚNICAMENTE con código Python puro y ejecutable.
NO uses bloques markdown (no uses ```python ni ```).
NO incluyas explicaciones ni comentarios fuera del código.
Librerías permitidas: pandas, numpy, plotly, json, datetime, re, math.
"""

interpreter_template = """
Eres un analista de negocios experto.
Tu tarea es interpretar los resultados de un análisis de drill-down para un usuario en español.

Click realizado: {prompt}
Métricas del subconjunto: {statistics}

Reglas:
1. Explica qué representa este subconjunto de datos.
2. Identifica 2 insights clave específicos de este detalle.
3. Sugiere 2 preguntas adicionales para seguir profundizando.
4. Formato de respuesta:
   ### Detalle del Análisis
   [Explicación]

   ### Insights clave
   - Insight 1...
   - Insight 2...

   ### ¿Qué más puedes preguntar?
   - Sugerencia 1...
   - Sugerencia 2...

Sé conciso y directo.
"""
