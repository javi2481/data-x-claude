# DataFluxIT — data-x-claude

## Antes de cualquier tarea
Lee en orden: datafluxIT-core-prd.md → explorex-prd-v3.md → explorex-guidelines.md
Si trabajás en core/: lee también core-guidelines.md
Fuente de verdad técnica: core/backend/engine/contracts.py

## Stack
- Python 3.11, FastAPI, uv (nunca pip install)
- MongoDB con motor (async)
- LiteLLM para todas las llamadas LLM — nunca litellm.completion() directo, siempre via llm_gateway.py
- React + Zustand + Plotly

## Reglas que no se negocian
- Contratos primero: definir Pydantic models antes de escribir endpoints
- El core (core/) nunca tiene lógica de dominio
- Los prompts viven en apps/{nombre}/backend/prompts/, nunca en core/
- El REVIEWER siempre corre antes de que el kernel ejecute código
- El LLM nunca recibe filas crudas del CSV
- Todo análisis persiste generated_code, audit_summary y node_document
- Un paso no está terminado hasta que tiene tests pasando
---

No escribas código nuevo.