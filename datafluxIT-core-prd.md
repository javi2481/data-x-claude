# DataFluxIT Core — PRD v1.0
## Fuente de verdad del motor compartido entre todos los productos

| Campo | Valor |
|---|---|
| Version | 1.0 |
| Fecha | Marzo 2026 |
| Organizacion | DataFluxIT |
| Repositorio | data-x-claude / core/ |
| Estado | Activo |

---

## 0. Que es este documento

Este PRD define que ES el core, que CONTIENE, que NUNCA puede tener, y como cada producto lo usa.
Es la fuente de verdad que prevalece sobre cualquier PRD de producto cuando hay conflicto sobre que pertenece al core.

Si algo no esta aqui, no es core. Si algo esta aqui, no puede estar en una app especifica.

---

## 1. El principio central

El core es el motor. Las apps son los productos.

El motor no sabe para que se usa. No sabe si esta analizando ventas, procesando facturas, transcribiendo reuniones o respondiendo preguntas sobre documentos. Solo sabe orquestar agentes LLM, gestionar sesiones, cachear resultados, y persistir artefactos.

Cada producto (app) trae sus propios prompts, su propia logica de dominio, y su propio frontend. El core no los conoce ni los necesita.

**La regla de oro: si para implementar algo en core necesitas saber que tipo de producto lo va a usar, entonces no pertenece al core.**

---

## 2. Productos actuales sobre el core

| App | Descripcion | Input | Output principal |
|---|---|---|---|
| apps/explorex | Analisis exploratorio de datos | CSV / Excel | Grafico + interpretacion + arbol |
| apps/docanalyzer | Extraccion estructurada de documentos | PDF / DOCX / imagen | JSON con campos extraidos |
| apps/meetintel | Inteligencia de reuniones | Audio / video | Documento .md + tareas |
| apps/knowledgebase | Base de conocimiento privada | Coleccion de documentos | Respuesta + fuentes |

Todos comparten el mismo core. Ninguno modifica el core para sus necesidades.

---

## 3. Que contiene el core

### 3.1 Motor de orquestacion LLM — ai_runner.py

Orquesta N roles LLM en secuencia o paralelo via LiteLLM.
Cada app define cuantos roles necesita y como se llaman.
El core no sabe ni le importa si el rol se llama CODER, EXTRACTOR, ANALYZER o RESPONDER.

```python
# La app define los roles y sus prompts
roles = [
    LLMRole(name="coder", model=CODER_MODEL, prompt_template=coder_tmpl),
    LLMRole(name="reviewer", model=REVIEWER_MODEL, prompt_template=reviewer_tmpl),
    LLMRole(name="interpreter", model=INTERPRETER_MODEL, prompt_template=interpreter_tmpl),
]
result = await ai_runner.run(roles=roles, context=context)
```

Capacidades del ai_runner:
- Ejecucion secuencial de roles con output de uno como input del siguiente
- Ejecucion en paralelo cuando los roles son independientes
- Fallback automatico via LiteLLM Router si un modelo falla
- Streaming del output de cualquier rol al frontend via SSE
- Structured output: cualquier rol puede devolver JSON tipado con schema
- Cost tracking por rol: tokens input + output + costo estimado
- Timeout configurable por rol

### 3.2 Gestion de sesiones — session_manager.py

Ciclo de vida completo de una sesion de procesamiento.
Una sesion es la unidad de trabajo de un usuario con un conjunto de datos.

```python
class ProcessingSession(BaseModel):
    id: str
    app_name: str                        # "explorex" | "docanalyzer" | "meetintel" | "knowledgebase"
    input_hash: str                      # SHA256 del input principal para cache
    input_metadata: dict                 # metadata especifica de la app (schema, coleccion, etc.)
    status: str                          # "active" | "completed" | "expired"
    node_count: int
    created_at: datetime
    last_active: datetime
    ttl_minutes: int                     # configurable por app
```

### 3.3 Nodos de procesamiento — ProcessingNode

Unidad de resultado dentro de una sesion. Una sesion tiene uno o muchos nodos.
Explorex usa muchos nodos (arbol). DocAnalyzer usa uno por documento. La estructura es la misma.

```python
class ProcessingNode(BaseModel):
    id: str
    parent_id: Optional[str]            # None para nodo raiz
    session_id: str
    app_name: str
    trigger_type: str                    # definido por la app
    trigger_input: str
    status: str                          # "pending" | "running" | "completed" | "failed"
    input_context: Optional[dict]        # contexto de entrada especifico de la app
    output: Optional[dict]               # output estructurado especifico de la app
    audit_document: Optional[str]        # documento .md de trazabilidad
    generated_artifacts: List[str]       # lista de artefactos generados (codigos, JSONs, etc.)
    role_metrics: dict                   # latencia y tokens por rol LLM
    cached: bool
    error_log: Optional[str]
    children: List[str]
    created_at: datetime
```

### 3.4 Cache de procesamiento — cache_manager.py

Cache por contenido: si el mismo input ya fue procesado, devuelve el resultado sin llamar ningun LLM.

```python
# La app define la cache key segun su logica
cache_key = cache_manager.build_key(
    input_hash=session.input_hash,
    secondary_hash=normalize(prompt)     # o schema_hash, o query_hash
)
cached_node = await cache_manager.get(cache_key)
```

Cache backends soportados: MongoDB (default, zero config), Redis (produccion de alta escala).
TTL configurable por app.
Cache invalidation manual disponible para admins.

### 3.5 Persistencia — repository.py

Operaciones CRUD sobre MongoDB para sesiones y nodos.
Schema flexible: el campo `output` y `input_context` son dicts — cada app pone lo que necesita.

### 3.6 Prompt builder — prompt_builder.py

Construye prompts a partir de templates y contexto.
Los templates viven en la app, nunca en el core.

```python
# La app pasa su template, el core lo renderiza con el contexto
rendered = prompt_builder.render(
    template=app_prompts.coder_template,
    context={"schema": session.input_metadata, "query": trigger_input}
)
```

### 3.7 LiteLLM gateway — llm_gateway.py

Wrapper sobre LiteLLM con configuracion centralizada.
Todos los roles de todas las apps pasan por este gateway.

Capacidades:
- Router con fallback automatico entre modelos
- Cost tracking con metadata por app y rol
- Guardrails de primera linea (configurable por app)
- Observabilidad: callbacks a Langfuse / LangSmith (opcional)
- Modelos configurables via env vars por rol

```python
# Variables de entorno del gateway (comunes a todas las apps)
OPENROUTER_API_KEY=
DEFAULT_MODEL=openrouter/anthropic/claude-3.5-sonnet
FALLBACK_MODEL=openrouter/openai/gpt-4o
OLLAMA_BASE_URL=http://localhost:11434    # para modo on-premise
ANALYSIS_TIMEOUT_SECONDS=60
LLM_CACHE_ENABLED=true
OBSERVABILITY_PROVIDER=langfuse          # opcional
```

### 3.8 Endpoints base — main.py

FastAPI con los endpoints que todas las apps comparten.

```
POST   /sessions                              crear sesion
GET    /sessions/{session_id}                 estado de sesion
POST   /sessions/{session_id}/process         procesar (trigger principal)
GET    /sessions/{session_id}/nodes           todos los nodos
GET    /sessions/{session_id}/nodes/{nid}     nodo especifico
GET    /sessions/{session_id}/nodes/{nid}/artifacts  artefactos del nodo
GET    /sessions/{session_id}/stream/{nid}    streaming SSE del procesamiento
GET    /sessions/{session_id}/export          exportar sesion completa
DELETE /sessions/{session_id}                 eliminar sesion
GET    /health                                health check con metricas basicas
```

Cada app puede agregar endpoints propios en su `app.py`.
Los endpoints del core no se modifican ni se sobreescriben.

### 3.9 Componentes frontend del core

Componentes React reutilizables sin logica de dominio.

```
core/frontend/src/components/
├── upload/FileUpload.tsx              upload generico con validacion
├── processing/ProcessingStatus.tsx   estados: pending / running / completed / failed
├── processing/StreamingText.tsx      texto que aparece token a token via SSE
├── audit/AuditSummary.tsx            muestra audit_document del nodo
├── audit/ArtifactViewer.tsx          ver artefactos del nodo (codigo, JSON, etc.)
├── tree/NodeTree.tsx                 arbol de nodos padre-hijo colapsable
└── common/ErrorMessage.tsx           errores en lenguaje natural
```

### 3.10 Contratos de metricas operativas

Todas las apps loguean las mismas metricas operativas desde el dia 1.

```python
class NodeMetrics(BaseModel):
    session_id: str
    node_id: str
    app_name: str
    cached: bool
    total_latency_ms: int
    role_latencies: dict             # {"coder": 1200, "reviewer": 800, "interpreter": 1500}
    role_tokens: dict                # {"coder": {"input": 500, "output": 300}, ...}
    role_costs_usd: dict             # costo estimado por rol
    error_type: Optional[str]
```

---

## 4. Que NUNCA puede estar en el core

Esta lista es tan importante como lo que si esta.

- Prompts de cualquier tipo (viven en apps/{nombre}/backend/prompts/)
- Logica de dominio (que es una factura, una decision, un dataset)
- Schemas especificos de extraction (formatos de facturas, contratos, etc.)
- Componentes de UI con logica de negocio (ResultPanel de Explorex, etc.)
- Referencias a tipos especificos de documentos, reuniones o datasets
- Configuracion de Docling, Whisper, LightRAG o Jupyter (son responsabilidad de cada app)
- Cualquier import de codigo de una app especifica

---

## 5. Como se extiende el core desde una app

Una app nunca modifica el core. Solo lo extiende desde su propia carpeta.

```
apps/{nombre}/
├── backend/
│   ├── app.py                    monta FastAPI sobre main.py del core, agrega endpoints propios
│   ├── prompts/                  los prompts de los roles LLM de esta app
│   ├── {preprocessor}.py         pre-procesador especifico (Docling, Whisper, etc.)
│   └── {domain_logic}.py         logica de dominio exclusiva de esta app
└── frontend/
    └── src/
        ├── pages/                paginas de la app
        └── components/           componentes especificos de la app
```

El `app.py` de cada app hace:
```python
from core.backend.main import app as core_app
from core.backend.engine.contracts import ProcessingSession, ProcessingNode

# Hereda todos los endpoints del core
app = core_app

# Agrega endpoints propios sin tocar los del core
@app.post("/sessions/{session_id}/custom-action")
async def custom_action(...):
    ...
```

---

## 6. Variables de entorno del core

Estas variables son comunes a todas las apps. Cada app puede agregar las suyas.

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
CACHE_BACKEND=mongodb          # mongodb | redis
REDIS_URL=                     # solo si cache_backend=redis
CACHE_TTL_MINUTES=60

# Storage
FILE_STORAGE_PATH=./_uploads
MAX_FILE_SIZE_MB=100

# Observabilidad (opcional)
OBSERVABILITY_PROVIDER=        # langfuse | langsmith | (vacio = desactivado)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:8080,http://127.0.0.1:8080
API_BASE=http://127.0.0.1:8001
PORT=8001
HOST=0.0.0.0
```

---

## 7. Build order del core

El core siempre se construye en este orden. Nunca saltear pasos.

1. contracts.py — Pydantic models: ProcessingSession, ProcessingNode, NodeMetrics, AuditDocument
2. repository.py — CRUD MongoDB
3. cache_manager.py — get/set/invalidate por cache key
4. prompt_builder.py — render de templates con contexto
5. llm_gateway.py — wrapper LiteLLM con router, cost tracking, streaming
6. ai_runner.py — orquestacion de roles via llm_gateway
7. session_manager.py — ciclo de vida de sesiones
8. main.py — FastAPI con todos los endpoints base
9. Componentes frontend del core

Cada paso depende de los anteriores. Un paso no esta terminado hasta que tiene tests pasando.

---

## 8. Principios que no se negocian

1. El core nunca tiene logica de dominio
2. Los prompts siempre viven en la app
3. Contratos primero — ningun endpoint ni componente sin Pydantic model definido
4. Todo procesamiento persiste sus artefactos — reproducibilidad no es opcional
5. El LLM nunca recibe datos crudos del usuario — solo contexto procesado y metadata
6. El REVIEWER/VALIDATOR siempre corre antes de usar cualquier output de un LLM generativo
7. Cache antes de cualquier llamada LLM
8. Metricas operativas desde el dia 1 — sin visibilidad no se puede optimizar
9. On-premise siempre disponible — Ollama como alternativa a cualquier LLM cloud
10. Una app nueva no requiere modificar el core — si lo requiere, el core tiene un bug de diseno

---

## 9. Metricas de salud del core

El endpoint /health devuelve:

```json
{
  "status": "healthy",
  "mongodb": "connected",
  "litellm": "operational",
  "active_sessions": 3,
  "cache_hit_rate_1h": 0.42,
  "avg_node_latency_ms_1h": 4200,
  "total_cost_usd_today": 1.23,
  "apps_loaded": ["explorex", "docanalyzer", "meetintel", "knowledgebase"]
}
```

---
*Version 1.0 — Marzo 2026 — DataFluxIT*
