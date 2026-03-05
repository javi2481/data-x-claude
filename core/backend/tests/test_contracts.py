import pytest
from engine.contracts import ProcessingSession, ProcessingNode, LLMRole, LLMRoleResult, AuditDocument, NodeMetrics
from datetime import datetime

def test_processing_session_creation():
    session = ProcessingSession(
        id="session-1",
        app_name="explorex",
        input_hash="hash-123",
        input_metadata={"filename": "test.csv"},
        status="active"
    )
    assert session.id == "session-1"
    assert session.app_name == "explorex"
    assert session.status == "active"
    assert session.node_count == 0
    assert isinstance(session.created_at, datetime)

def test_processing_node_creation():
    node = ProcessingNode(
        id="node-1",
        session_id="session-1",
        app_name="explorex",
        trigger_type="auto",
        trigger_input="Initial question",
        status="pending"
    )
    assert node.id == "node-1"
    assert node.status == "pending"
    assert node.children == []
    assert node.generated_artifacts == []
    assert isinstance(node.created_at, datetime)

def test_llm_role_creation():
    role = LLMRole(
        name="coder",
        model_category="generative-role",
        prompt_template="Analyze {data}"
    )
    assert role.name == "coder"
    assert role.model_category == "generative-role"
    assert role.timeout_seconds == 60
    assert role.temperature == 0.1

def test_llm_role_result_creation():
    result = LLMRoleResult(
        content="Result content",
        tokens_in=100,
        tokens_out=50,
        latency_ms=1200,
        model_used="claude-sonnet"
    )
    assert result.content == "Result content"
    assert result.tokens_in == 100

def test_audit_document_creation():
    doc = AuditDocument(content="# Audit Log")
    assert doc.content == "# Audit Log"
    assert doc.format == "markdown"
    assert isinstance(doc.created_at, datetime)

def test_node_metrics_creation():
    metrics = NodeMetrics(
        session_id="session-1",
        node_id="node-1",
        app_name="explorex",
        cached=False,
        total_latency_ms=2500,
        role_latencies={"coder": 1500, "reviewer": 1000},
        role_tokens={"coder": {"input": 500, "output": 200}},
        role_costs_usd={"coder": 0.005}
    )
    assert metrics.node_id == "node-1"
    assert metrics.role_latencies["coder"] == 1500
