from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class LLMRole(BaseModel):
    name: str
    model_category: str  # "generative-role" | "validation-role"
    prompt_template: str
    response_schema: Optional[Dict[str, Any]] = None   # JSON schema for structured output
    timeout_seconds: int = 60
    temperature: float = 0.1

class LLMRoleResult(BaseModel):
    content: str
    structured_output: Optional[Dict[str, Any]] = None
    tokens_in: int
    tokens_out: int
    latency_ms: int
    model_used: str

class AuditDocument(BaseModel):
    content: str
    format: str = "markdown"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NodeMetrics(BaseModel):
    session_id: str
    node_id: str
    app_name: str
    cached: bool
    total_latency_ms: int
    role_latencies: Dict[str, int]             # {"coder": 1200, "reviewer": 800, "interpreter": 1500}
    role_tokens: Dict[str, Dict[str, int]]    # {"coder": {"input": 500, "output": 300}, ...}
    role_costs_usd: Dict[str, float]          # costo estimado por rol
    error_type: Optional[str] = None

class ProcessingSession(BaseModel):
    id: str
    app_name: str                        # "explorex" | "docanalyzer" | "meetintel" | "knowledgebase"
    input_hash: str                      # SHA256 del input principal para cache
    input_metadata: Dict[str, Any]       # metadata especifica de la app (schema, coleccion, etc.)
    status: str                          # "active" | "completed" | "expired"
    node_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_minutes: int = 30                # configurable por app

class ProcessingNode(BaseModel):
    id: str
    parent_id: Optional[str] = None            # None para nodo raiz
    session_id: str
    app_name: str
    trigger_type: str                    # definido por la app (e.g., "auto", "click")
    trigger_input: str
    status: str                          # "pending" | "running" | "completed" | "failed"
    input_context: Optional[Dict[str, Any]] = None        # contexto de entrada especifico de la app
    output: Optional[Dict[str, Any]] = None               # output estructurado especifico de la app
    audit_document: Optional[str] = None        # documento .md de trazabilidad
    generated_artifacts: List[str] = Field(default_factory=list)       # lista de artefactos generados (codigos, JSONs, etc.)
    role_metrics: Dict[str, Any] = Field(default_factory=dict)         # latencia y tokens por rol LLM
    cached: bool = False
    error_log: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
