# Core Guidelines for Junie
## data-x-claude / core/

This file defines execution rules for Junie when working on the shared core.
Read datafluxIT-core-prd.md before starting any task on core/.

Document hierarchy:
1. datafluxIT-core-prd.md -- source of truth for what belongs in core
2. core-guidelines.md -- execution rules for core work
3. core/backend/engine/contracts.py -- source of truth for base models

If unsure whether something belongs in core or in an app: read datafluxIT-core-prd.md section 4.

---

## What Core Is

core/ is the shared engine used by all DataFluxIT products.
It has zero domain logic. It does not know what an invoice, a meeting, or a dataset is.
It only knows how to: orchestrate LLM roles, manage sessions, cache results, persist nodes, stream output.

Any product is built by creating apps/{name}/ and importing from core. Core is never modified for an app.

---

## Monorepo Structure

data-x-claude/
├── core/
│   ├── backend/
│   │   ├── engine/
│   │   │   ├── contracts.py           # ALL Pydantic base models -- source of truth
│   │   │   ├── ai_runner.py           # LLM role orchestration via LiteLLM
│   │   │   ├── llm_gateway.py         # LiteLLM wrapper: router, cost tracking, streaming
│   │   │   ├── session_manager.py     # Session lifecycle
│   │   │   ├── cache_manager.py       # SHA256-based cache: mongodb or redis
│   │   │   ├── prompt_builder.py      # Renders templates from app context
│   │   │   └── repository.py          # MongoDB CRUD for sessions and nodes
│   │   └── main.py                    # FastAPI with all base endpoints
│   └── frontend/
│       └── src/
│           ├── components/
│           │   ├── upload/FileUpload.tsx
│           │   ├── processing/ProcessingStatus.tsx
│           │   ├── processing/StreamingText.tsx
│           │   ├── audit/AuditSummary.tsx
│           │   ├── audit/ArtifactViewer.tsx
│           │   ├── tree/NodeTree.tsx
│           │   └── common/ErrorMessage.tsx
│           ├── lib/
│           │   ├── api/client.ts
│           │   └── api/services/core.ts   # ONLY normalization point for core fields
│           └── types/core.ts
├── apps/
│   ├── explorex/
│   ├── docanalyzer/
│   ├── meetintel/
│   └── knowledgebase/
├── datafluxIT-core-prd.md
├── pyproject.toml
└── .env.example

---

## Build and Configuration

### Prerequisites
- Python 3.11
- Node.js 20+
- uv (pip install uv)
- MongoDB Atlas URI
- OpenRouter API key

### Core backend setup
cd core/backend
uv sync
cp .env.example .env
uv run uvicorn main:app --reload --port 8000

### Core frontend (dev, standalone)
cd core/frontend
npm install
npm run dev

### uv workspace rules
Always add from the correct directory:
  cd core/backend && uv add fastapi motor pydantic litellm
Never use pip install. Never edit uv.lock manually.
core/backend pyproject.toml project name: "core-backend"

### Windows issues
- uv lock errors: $env:UV_LINK_MODE="copy"
- curl: use curl.exe or Invoke-WebRequest -UseBasicParsing

---

## Architecture Rules -- Never Violate These

### 1. Zero domain logic in core
No hardcoded knowledge of invoices, meetings, datasets, questions, or any domain concept.
If implementing something requires knowing what type of product uses it: it belongs in an app.

### 2. Contracts first -- always
Define or update Pydantic models in contracts.py BEFORE writing any endpoint, runner, or component.
No endpoint without a typed request/response model. No component without a typed prop interface.

### 3. ai_runner accepts roles as parameters -- never hardcodes them
```python
# CORRECT: app passes roles, core runs them
result = await ai_runner.run(roles=[coder_role, reviewer_role, interpreter_role], context=ctx)

# WRONG: core hardcodes CODER/REVIEWER/INTERPRETER
result = await ai_runner.run_coder_reviewer_interpreter(...)
```

### 4. prompt_builder never contains prompt strings
It only renders templates passed by the app. No default prompts, no fallback strings.

### 5. cache_manager uses content-addressable keys
Cache key always built from hashes of the actual content, never from timestamps or IDs alone.
```python
key = cache_manager.build_key(input_hash, secondary_hash)  # app provides both hashes
```

### 6. llm_gateway is the only place that calls LiteLLM
No direct litellm.completion() calls outside of llm_gateway.py.
All LLM calls go through the gateway for consistent cost tracking and fallback.

### 7. All base endpoints are in main.py -- never split
The 10 base endpoints defined in the Core PRD all live in main.py.
Apps extend by importing app and adding routes. They never modify main.py.

### 8. Frontend components have no domain logic
NodeTree does not know what a drill-down is.
AuditSummary does not know what an audit_summary means for a specific product.
They receive typed props and render. Domain meaning lives in the app.

### 9. NodeMetrics logged for every node
Every completed or failed node must log NodeMetrics before returning.
No exceptions. This is the only way to monitor cost and performance across all apps.

### 10. On-premise always works
Every feature that uses an LLM must work with OLLAMA_BASE_URL configured.
Never assume a cloud model is available.

Recommended on-premise models via Ollama (March 2026):
- Generative roles (CODER, ANALYZER, RESPONDER): llama3.2 or qwen2.5:32b
- Validation roles (REVIEWER, VALIDATOR, VERIFIER): qwen3:32b
  Qwen3-32B is the recommended model for all validation roles -- cloud or on-premise.
  It outperforms models 3x its size on instruction-following benchmarks due to Scaled RL training.
- Embedding (Knowledge Base): nomic-embed-text or all-minilm

---

## Model Strategy

### Role categories and recommended models

Roles fall into two functional categories with different quality requirements:

**Generative roles** (CODER, ANALYZER, RESPONDER, EXTRACTOR)
These roles produce creative or complex output. Use the most capable model available.
- Cloud default: openrouter/anthropic/claude-3.5-sonnet
- Cloud fallback: openrouter/openai/gpt-4o-mini
- On-premise: ollama/qwen2.5:32b (best quality) or ollama/llama3.2 (faster)

**Validation roles** (REVIEWER, VALIDATOR, VERIFIER)
These roles check, verify, and flag problems. They need precision and reliability, not creativity.
Qwen3-32B is the recommended model for all validation roles -- cloud or on-premise.
It outperforms models 3x its size on instruction-following benchmarks due to Scaled RL training.
- Cloud: openrouter/qwen/qwen3-32b
- On-premise: ollama/qwen2.5:32b

### LiteLLM Router configuration (llm_gateway.py)

```python
router_config = {
    "model_list": [
        {
            "model_name": "validation-role",
            "litellm_params": {"model": "openrouter/qwen/qwen3-32b", "api_key": OPENROUTER_KEY}
        },
        {
            "model_name": "validation-role",   # fallback: on-premise
            "litellm_params": {"model": "ollama/qwen2.5:32b", "api_base": OLLAMA_BASE_URL}
        },
        {
            "model_name": "generative-role",
            "litellm_params": {"model": "openrouter/anthropic/claude-3.5-sonnet", "api_key": OPENROUTER_KEY}
        },
        {
            "model_name": "generative-role",   # fallback: on-premise
            "litellm_params": {"model": "ollama/qwen2.5:32b", "api_base": OLLAMA_BASE_URL}
        },
    ],
    "routing_strategy": "latency-based-routing",
}
```

Apps select the category when defining roles -- not the specific model:
```python
LLMRole(name="reviewer", model_category="validation-role", prompt_template=tmpl)
LLMRole(name="coder",    model_category="generative-role", prompt_template=tmpl)
```

Overriding with a specific model is always possible via env var in the app.

---

## Build Order

Build in this exact order. A step is not done until it has passing tests.

Phase 1 -- Contracts and persistence:
1. contracts.py
   ProcessingSession, ProcessingNode, AuditDocument, NodeMetrics, LLMRole, LLMRoleResult
2. repository.py
   create_session, get_session, update_session, create_node, get_node, update_node, list_nodes

Phase 2 -- LLM infrastructure:
3. llm_gateway.py
   call(role, messages, structured_schema?) -> LLMRoleResult
   stream(role, messages) -> AsyncIterator[str]
   Verify: fallback works when primary model is unavailable
4. prompt_builder.py
   render(template, context) -> str
   Verify: KeyError on missing context key, not silent failure
5. cache_manager.py
   build_key(input_hash, secondary_hash) -> str
   get(key) -> Optional[ProcessingNode]
   set(key, node) -> None
   invalidate(key) -> None

Phase 3 -- Orchestration:
6. ai_runner.py
   run(roles, context, session) -> List[LLMRoleResult]
   run_parallel(roles, context, session) -> List[LLMRoleResult]
   Verify: role output feeds next role input correctly
7. session_manager.py
   create(app_name, input_hash, metadata) -> ProcessingSession
   expire_inactive(ttl_minutes) -> int

Phase 4 -- API:
8. main.py
   All 10 base endpoints
   SSE streaming on /stream/{node_id}
   /health with NodeMetrics aggregate

Phase 5 -- Frontend core:
9. types/core.ts
10. lib/api/client.ts + lib/api/services/core.ts
11. components/ (all 7 base components)

---

## Key Contracts

### ProcessingSession
```python
class ProcessingSession(BaseModel):
    id: str
    app_name: str
    input_hash: str
    input_metadata: dict
    status: str                  # "active" | "completed" | "expired"
    node_count: int
    created_at: datetime
    last_active: datetime
    ttl_minutes: int = 30
```

### ProcessingNode
```python
class ProcessingNode(BaseModel):
    id: str
    parent_id: Optional[str] = None
    session_id: str
    app_name: str
    trigger_type: str
    trigger_input: str
    status: str                  # "pending" | "running" | "completed" | "failed"
    input_context: Optional[dict] = None
    output: Optional[dict] = None
    audit_document: Optional[str] = None
    generated_artifacts: List[str] = []
    role_metrics: dict = {}      # {"coder": {"latency_ms": 1200, "tokens_in": 500, "tokens_out": 300}}
    cached: bool = False
    error_log: Optional[str] = None
    children: List[str] = []
    created_at: datetime
```

### LLMRole
```python
class LLMRole(BaseModel):
    name: str
    model: str
    prompt_template: str
    response_schema: Optional[dict] = None   # JSON schema for structured output
    timeout_seconds: int = 60
    temperature: float = 0.1
```

### TypeScript CoreNode
```typescript
interface CoreNode {
  id: string
  parentId: string | null
  sessionId: string
  appName: string
  triggerType: string
  triggerInput: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  inputContext?: Record<string, unknown>
  output?: Record<string, unknown>
  auditDocument?: string
  generatedArtifacts: string[]
  roleMetrics: Record<string, RoleMetric>
  cached: boolean
  errorLog?: string
  children: string[]
  createdAt: string
}
```

---

## Testing Rules

### Backend tests
cd core/backend && uv run pytest tests/ -v

Test structure:
tests/
├── test_contracts.py        -- Pydantic validation, required fields
├── test_repository.py       -- CRUD with test MongoDB
├── test_llm_gateway.py      -- mock LiteLLM, test fallback and cost tracking
├── test_prompt_builder.py   -- template rendering, missing key handling
├── test_cache_manager.py    -- hit/miss/invalidate
├── test_ai_runner.py        -- mock all roles, test sequential and parallel execution
├── test_session_manager.py  -- create, expire, TTL
└── test_endpoints.py        -- all 10 base endpoints with test client

Always mock LiteLLM -- never call real models in tests:
```python
@pytest.fixture
def mock_llm_role(mocker):
    return mocker.patch("engine.llm_gateway.call",
        return_value=LLMRoleResult(content="mocked output", tokens_in=100, tokens_out=50))
```

pyproject.toml:
[tool.pytest.ini_options]
asyncio_mode = "auto"

---

## What Not To Do

- Never add domain-specific logic to core/ for any reason
- Never hardcode role names (CODER, REVIEWER, etc.) anywhere in core
- Never call litellm.completion() directly -- always use llm_gateway
- Never write prompt strings in core/ -- templates come from apps
- Never skip NodeMetrics logging
- Never assume cloud LLM availability -- always test with Ollama fallback
- Never modify an app's endpoints from core
- Never declare a phase complete without running verification
- Never use pip install -- always uv add from the correct directory
