# CLAUDE.md — DataFluxIT / data-x-claude

Leer este archivo completo antes de cualquier tarea.

## Jerarquia documental

1. `datafluxIT-core-prd.md` — fuente de verdad del core compartido
2. `explorex-prd-v3.md` — fuente de verdad de producto, UX y alcance de Explorex
3. `explorex-guidelines.md` — reglas de implementacion de Explorex para Junie
4. `core-guidelines.md` — reglas de construccion del core para Junie
5. `core/backend/engine/contracts.py` — fuente de verdad para contratos tecnicos y modelos base

Si hay conflicto sobre que pertenece al core vs a una app: prevalece `datafluxIT-core-prd.md`.
Si hay conflicto sobre producto, UX o alcance de Explorex: prevalece `explorex-prd-v3.md`.
Si hay conflicto sobre contratos tecnicos: prevalece `contracts.py`.

---

## Que es esto

DataFluxIT es una agencia/consultora de datos que construye una plataforma de productos AI con un core compartido y reutilizable.

Repositorio: `data-x-claude` — monorepo con:
- `core/` — motor compartido entre todos los productos. Nunca tiene logica de dominio.
- `apps/` — productos especificos que usan el core sin modificarlo.

Primer producto activo: `apps/explorex/` — explorador de datos generico.

---

## Productos sobre el core

| App | Descripcion | Estado |
|---|---|---|
| apps/explorex | Analisis exploratorio de datos (CSV/Excel) | En desarrollo activo |
| apps/docanalyzer | Extraccion estructurada de documentos (PDF/DOCX) | Definido, post-Explorex |
| apps/meetintel | Inteligencia de reuniones (audio/video) | Definido, post-Explorex |
| apps/knowledgebase | Base de conocimiento privada | Definido, post-Explorex |

Proyecto en horizonte post-Explorex: DataFlux Analyst Hive — agente de analisis sobre Aden Hive framework con auto-recuperacion de errores en codigo generado.

---

## Arquitectura del core

El core orquesta N roles LLM via LiteLLM. No sabe para que producto trabaja.

### Motor de analisis: ai_runner.py

Tres roles LLM separados (configurables por app):
- **CODER** — genera codigo Python a partir del schema y el prompt del usuario
- **REVIEWER** — valida y corrige el codigo antes de ejecutarlo
- **INTERPRETER** — interpreta los resultados computados en lenguaje natural

El kernel Jupyter ejecuta el codigo real. Es la unica pieza que toca los datos directamente.
Ningun LLM recibe filas crudas del CSV ni el DataFrame completo.
Solo recibe: schema, resumenes estadisticos, resultados computados.

### Motor LLM: LiteLLM + OpenRouter

LiteLLM es la libreria que orquesta todas las llamadas LLM.
OpenRouter es el proveedor de acceso a multiples modelos con una sola API key.

**Roles generativos** (CODER, INTERPRETER, ANALYZER, RESPONDER):
- Modelo: `openrouter/anthropic/claude-3.5-sonnet`
- On-premise fallback: `ollama/qwen2.5:32b`

**Roles de validacion** (REVIEWER, VALIDATOR, VERIFIER):
- Modelo: `openrouter/qwen/qwen3-32b`
- Qwen3.5-9B usa Scaled RL — mejor instruction following que modelos 3x su tamano
- On-premise fallback: `ollama/qwen3.5:9b`

### Flujo Explorex

1. Usuario sube dataset
2. cache_manager verifica SHA256(dataset_hash + normalized_prompt)
   - Cache hit: devuelve nodo con cached=True, sin ejecutar nada
   - Cache miss: continua
3. CODER LLM genera codigo Python
4. REVIEWER LLM valida y corrige el codigo
5. Kernel Jupyter ejecuta el codigo aprobado sobre el dataset real
6. result_parser.py captura stdout: plotly_figure + statistics + computed_values + chart_description
7. INTERPRETER LLM genera interpretacion + audit_summary + suggestions + node_document
8. Nodo guardado en MongoDB con todos los artefactos
9. Frontend: grafico interactivo + interpretacion + chips + arbol actualizado

---

## Estructura del monorepo

```
data-x-claude/
├── core/
│   ├── backend/
│   │   ├── engine/
│   │   │   ├── contracts.py           # Pydantic models — fuente de verdad tecnica
│   │   │   ├── ai_runner.py           # Orquestacion LLM roles via LiteLLM
│   │   │   ├── llm_gateway.py         # Wrapper LiteLLM: router, cost tracking, streaming
│   │   │   ├── session_manager.py     # Ciclo de vida de sesiones
│   │   │   ├── cache_manager.py       # Cache SHA256: mongodb o redis
│   │   │   ├── prompt_builder.py      # Renderiza templates de las apps
│   │   │   └── repository.py         # CRUD MongoDB
│   │   └── main.py                   # FastAPI con endpoints base
│   └── frontend/
│       └── src/
│           ├── components/            # Componentes reutilizables sin logica de dominio
│           ├── lib/api/               # Cliente HTTP + normalizacion
│           └── types/core.ts
├── apps/
│   ├── explorex/
│   │   ├── backend/
│   │   │   ├── app.py                 # Monta core FastAPI, agrega endpoints propios
│   │   │   ├── kernel_manager.py      # Un kernel Jupyter por sesion
│   │   │   ├── result_parser.py       # stdout kernel → Plotly JSON
│   │   │   ├── dataset_intake.py      # Validacion CSV/Excel, computo de schema
│   │   │   ├── notebook_exporter.py   # Arbol → .ipynb
│   │   │   └── prompts/
│   │   │       ├── initial.py         # Prompts para "De que habla este dataset?"
│   │   │       ├── drilldown.py       # Prompts para drill-down por click
│   │   │       └── suggestions.py     # Prompts para generacion de sugerencias
│   │   └── frontend/
│   │       └── src/
│   │           ├── pages/Explorer.tsx
│   │           └── components/result/
│   ├── docanalyzer/
│   ├── meetintel/
│   └── knowledgebase/
├── .junie/
│   └── guidelines.md                  # Bootstrap para Junie — apunta a los 4 docs
├── datafluxIT-core-prd.md
├── core-guidelines.md
├── explorex-prd-v3.md
├── explorex-guidelines.md
├── CLAUDE.md
└── pyproject.toml
```

---

## Variables de entorno (core)

```env
# LLM Gateway
OPENROUTER_API_KEY=
DEFAULT_MODEL=openrouter/anthropic/claude-3.5-sonnet
FALLBACK_MODEL=openrouter/openai/gpt-4o
OLLAMA_BASE_URL=http://localhost:11434
ANALYSIS_TIMEOUT_SECONDS=60

# MongoDB
MONGO_URI=
MONGO_DB_NAME=datafluxIT

# Cache
CACHE_BACKEND=mongodb
CACHE_TTL_MINUTES=60

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:8080,http://127.0.0.1:8080
API_BASE=http://127.0.0.1:8001
PORT=8001
HOST=0.0.0.0
```

```env
# Explorex — adicionales
JUPYTER_SERVER_URL=http://localhost:8888
JUPYTER_SERVER_TOKEN=
MAX_DATASET_ROWS=100000

CODER_MODEL=openrouter/anthropic/claude-3.5-sonnet
REVIEWER_MODEL=openrouter/qwen/qwen3-32b
INTERPRETER_MODEL=openrouter/anthropic/claude-3.5-sonnet
```

---

## Endpoints del core

```
POST   /sessions
GET    /sessions/{session_id}
POST   /sessions/{session_id}/process
GET    /sessions/{session_id}/nodes
GET    /sessions/{session_id}/nodes/{node_id}
GET    /sessions/{session_id}/nodes/{node_id}/artifacts
GET    /sessions/{session_id}/stream/{node_id}
GET    /sessions/{session_id}/export
DELETE /sessions/{session_id}
GET    /health
```

---

## Principios que no se negocian

1. El core nunca tiene logica de dominio
2. Los prompts siempre viven en apps/{nombre}/backend/prompts/
3. El LLM nunca recibe filas crudas del CSV ni el DataFrame completo
4. El REVIEWER siempre corre antes de que el kernel ejecute cualquier codigo
5. Contratos primero — ningun endpoint sin Pydantic model definido
6. Todo analisis persiste generated_code, audit_summary y node_document
7. El usuario primario nunca ve Python ni errores tecnicos
8. El arbol de exploracion nunca se convierte en chat lineal
9. Cache antes de cualquier llamada LLM
10. On-premise siempre disponible — Ollama como alternativa a cualquier LLM cloud

---

## Riesgos criticos a monitorear

1. Costo de tokens: tres LLMs por nodo — monitorear tokens por rol desde el dia 1
2. Latencia total: coder + reviewer + kernel + interpreter puede superar 30 segundos
3. Reviewer demasiado conservador: puede rechazar codigo valido — ajustar prompt
4. Kernel por sesion no escala: monitorear RAM desde el dia 1
5. matplotlib→Plotly puede fallar en graficos complejos: limitar catalogo inicial

---

## Documentacion de referencia

- LiteLLM: https://docs.litellm.ai/docs/
- LiteLLM providers: https://docs.litellm.ai/docs/providers
- OpenRouter: https://openrouter.ai/docs
- jupyter-client: https://jupyter-client.readthedocs.io/en/stable/
- react-plotly.js: https://github.com/plotly/react-plotly.js

*Ultima actualizacion: Marzo 2026*
