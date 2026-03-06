# Explorex Guidelines for Junie
## data-x-claude / apps/explorex/

Read explorex-prd-v3.md, datafluxIT-core-prd.md, and core-guidelines.md before starting any task.

Document hierarchy:
1. explorex-prd-v3.md -- product, UX, scope
2. datafluxIT-core-prd.md -- what belongs in core vs app
3. core-guidelines.md -- core build rules
4. explorex-guidelines.md -- this file
5. core/backend/engine/contracts.py -- base contracts

---

## What Explorex Is

apps/explorex/ is a data exploration product built on core/.
It adds: CSV/Excel intake, Jupyter kernel execution, drill-down tree, matplotlib→Plotly pipeline.
It never modifies core/. It only extends it.

---

## Prerequisites (in addition to core)

- Local Jupyter Server on port 8888
- JUPYTER_SERVER_TOKEN in .env (changes every restart -- always update)
- uv add jupyter-client nbformat plotly matplotlib pandas numpy
  (run from apps/explorex/backend/)

---

## App Structure

apps/explorex/
├── backend/
│   ├── app.py                    mounts core FastAPI, adds explorex-specific endpoints
│   ├── kernel_manager.py         one Jupyter kernel per session, DataFrame in memory
│   ├── result_parser.py          kernel stdout → plotly JSON, extracts interpretation
│   ├── notebook_exporter.py      session tree → .ipynb
│   ├── dataset_intake.py         CSV/Excel validation, schema computation, dataset_hash
│   └── prompts/
│       ├── initial.py            CODER + REVIEWER + INTERPRETER for "De que habla este dataset?"
│       ├── drilldown.py          prompts for chart click analysis
│       └── suggestions.py        prompts for suggestion generation
└── frontend/
    └── src/
        ├── pages/Explorer.tsx
        └── components/result/
            ├── ResultPanel.tsx
            ├── InterpretationText.tsx
            └── AuditSummary.tsx       shows audit_summary + "Ver codigo" for technical users

---

## Build Order

Build core first. Then build Explorex in this order.

Phase 1 -- Intake and kernel:
1. dataset_intake.py
   validate(file) -> DatasetProfile
   DatasetProfile: columns, types, nulls, cardinality, row_count, dataset_hash, quality_warnings
2. kernel_manager.py
   start_kernel(session_id) -> kernel_id
   load_dataset(kernel_id, dataset_path) -> None   (loads ONCE, stays in memory)
   execute(kernel_id, code, timeout) -> KernelOutput
   restart(kernel_id) -> None
   stop(kernel_id) -> None

Phase 2 -- Analysis pipeline:
3. prompts/initial.py, prompts/drilldown.py, prompts/suggestions.py
   Each exports: coder_template, reviewer_template, interpreter_template
4. result_parser.py
   parse(kernel_stdout) -> ParsedResult
   ParsedResult: plotly_figure, statistics, computed_values, chart_description, data_warnings
   convert_matplotlib_to_plotly(fig) -> dict
5. app.py
   POST /sessions/{id}/analyze -- full pipeline: cache → CODER → REVIEWER → kernel → INTERPRETER
   GET  /sessions/{id}/nodes/{nid}/code
   GET  /sessions/{id}/nodes/{nid}/document
   GET  /sessions/{id}/export

Phase 3 -- Frontend:
6. types/explorex.ts -- ExplorationNode extends CoreNode with explorex-specific output fields
7. lib/api/services/explorex.ts -- normalization for explorex-specific fields
8. components/result/InterpretationText.tsx
9. components/result/AuditSummary.tsx
10. components/result/ResultPanel.tsx -- composes chart + interpretation + suggestions
11. pages/Explorer.tsx -- main page with upload, tree sidebar, result panel

Phase 4 -- Export and polish:
12. notebook_exporter.py -- tree → .ipynb
13. Loading skeletons, error boundaries, tree collapse/expand

---

## Explorex-Specific Contracts

### DatasetProfile
```python
class DatasetProfile(BaseModel):
    dataset_hash: str
    filename: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    quality_warnings: List[str]

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_pct: float
    cardinality: int
    sample_values: List[str]    # max 5 values, never raw data
```

### ExplorationOutput (stored in ProcessingNode.output)
```python
class ExplorationOutput(BaseModel):
    plotly_figure: dict
    interpretation: str
    suggestions: List[str]       # up to 3, high quality only
    audit_summary: str
    node_document: str
    generated_code: str          # CODER output (before review)
    reviewed_code: str           # what kernel actually ran
    code_hash: str
    execution_time_ms: int
    data_warnings: List[str]
```

### Kernel stdout contract (what executed code must print)
```python
import json
result = {
    "plotly_figure": plotly_fig.to_dict(),
    "statistics": stats_dict,
    "computed_values": values_dict,
    "chart_description": "...",
    "data_warnings": []
}
print(json.dumps(result, ensure_ascii=False))
```
INTERPRETER never receives raw CSV rows or the full DataFrame. Only this JSON.

---

## Explorex-Specific Rules

1. Kernel loads dataset ONCE at session start. Never reload per question.
2. REVIEWER always runs before kernel execution. No exceptions.
3. INTERPRETER only receives kernel output -- never raw data.
4. matplotlib inside, Plotly outside -- result_parser converts every figure.
5. Drill-down supported for: bar, line, scatter, pie. Complex charts display but no drill-down.
6. Non-technical user never sees Python code. Technical user can request it explicitly.
7. audit_summary and node_document are mandatory on every completed node.
8. Jupyter token changes every restart -- always update JUPYTER_SERVER_TOKEN in .env.

---

## Env Vars (app-specific, in addition to core .env)

```env
JUPYTER_SERVER_URL=http://localhost:8888
JUPYTER_SERVER_TOKEN=
MAX_DATASET_ROWS=100000

# CODER: generative role -- needs reasoning and code quality
CODER_MODEL=openrouter/anthropic/claude-sonnet-4-5
# REVIEWER: validation role -- Qwen3.5-9B recommended (precision > creativity)
# On-premise alternative: ollama/qwen3.5:9b
REVIEWER_MODEL=openrouter/qwen/qwen3.5-9b
# INTERPRETER: generative role -- needs natural language quality
INTERPRETER_MODEL=openrouter/anthropic/claude-sonnet-4-5
```

---

## Testing

tests/
├── test_dataset_intake.py      -- validate CSV, Excel, oversized, malformed
├── test_kernel_manager.py      -- start, load, execute, timeout, restart
├── test_result_parser.py       -- matplotlib→Plotly, stdout parsing
├── test_analysis_pipeline.py   -- mock all 3 roles + kernel, test full flow
├── test_cache.py               -- same dataset + same prompt = cache hit
└── test_notebook_export.py     -- tree → valid .ipynb

Mock kernel execution in tests:
```python
@pytest.fixture
def mock_kernel(mocker):
    return mocker.patch("kernel_manager.execute",
        return_value=KernelOutput(stdout=json.dumps({
            "plotly_figure": {}, "statistics": {}, "computed_values": {},
            "chart_description": "Bar chart of sales by month",
            "data_warnings": []
        })))
```

---

## What Not To Do

- Never put Explorex prompts in core/
- Never pass raw DataFrame or CSV rows to any LLM role
- Never skip REVIEWER before kernel execution
- Never show Python code to non-technical user without explicit request
- Never build a flat chat list -- data model is always a tree
- Never reload dataset per question -- it stays in kernel memory
- Never use matplotlib figures in frontend -- always convert to Plotly JSON first
- Never declare complete without verifying the actual browser output
