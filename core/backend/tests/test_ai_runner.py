import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.backend.engine import ai_runner
from core.backend.engine.contracts import LLMRole, LLMRoleResult, ProcessingSession

@pytest.fixture
def session():
    return ProcessingSession(
        id="session123",
        app_name="explorex",
        input_hash="hash123",
        input_metadata={},
        status="active"
    )

@pytest.mark.asyncio
async def test_ai_runner_sequential(session):
    # Definir roles
    role1 = LLMRole(
        name="role1",
        model_category="generative-role",
        prompt_template="Input: {input_val}"
    )
    role2 = LLMRole(
        name="role2",
        model_category="validation-role",
        prompt_template="Prev: {role1_output}"
    )
    
    # Mockear gateway
    with patch("core.backend.engine.ai_runner._gateway.call") as mock_call:
        mock_call.side_effect = [
            LLMRoleResult(content="output1", tokens_in=10, tokens_out=10, latency_ms=100, model_used="gpt-4o"),
            LLMRoleResult(content="output2", tokens_in=15, tokens_out=20, latency_ms=150, model_used="gpt-4o")
        ]
        
        roles = [role1, role2]
        context = {"input_val": "hello"}
        
        results = await ai_runner.run(roles, context, session)
        
        assert len(results) == 2
        assert results[0].content == "output1"
        assert results[1].content == "output2"
        
        # Verificar que el segundo rol recibió el output del primero
        # Primera llamada: prompt='Input: hello'
        # Segunda llamada: prompt='Prev: output1'
        assert mock_call.call_count == 2
        
        # Verificar prompts renderizados
        first_call_messages = mock_call.call_args_list[0][0][1]
        second_call_messages = mock_call.call_args_list[1][0][1]
        
        assert first_call_messages[0]["content"] == "Input: hello"
        assert second_call_messages[0]["content"] == "Prev: output1"

@pytest.mark.asyncio
async def test_ai_runner_parallel(session):
    role1 = LLMRole(name="role1", model_category="generative-role", prompt_template="Prompt 1: {val}")
    role2 = LLMRole(name="role2", model_category="generative-role", prompt_template="Prompt 2: {val}")
    
    with patch("core.backend.engine.ai_runner._gateway.call") as mock_call:
        mock_call.return_value = LLMRoleResult(content="parallel_out", tokens_in=5, tokens_out=5, latency_ms=50, model_used="gpt-4o")
        
        roles = [role1, role2]
        context = {"val": "data"}
        
        results = await ai_runner.run_parallel(roles, context, session)
        
        assert len(results) == 2
        assert results[0].content == "parallel_out"
        assert results[1].content == "parallel_out"
        assert mock_call.call_count == 2

def test_get_node_metrics():
    roles = [
        LLMRole(name="role1", model_category="generative-role", prompt_template=""),
        LLMRole(name="role2", model_category="validation-role", prompt_template="")
    ]
    results = [
        LLMRoleResult(content="out1", tokens_in=100, tokens_out=50, latency_ms=1000, model_used="m1"),
        LLMRoleResult(content="out2", tokens_in=80, tokens_out=40, latency_ms=500, model_used="m2")
    ]
    
    metrics = ai_runner.get_node_metrics(
        session_id="s1",
        node_id="n1",
        app_name="explorex",
        results=results,
        roles=roles
    )
    
    assert metrics.total_latency_ms == 1500
    assert metrics.role_latencies["role1"] == 1000
    assert metrics.role_latencies["role2"] == 500
    assert metrics.role_tokens["role1"]["input"] == 100
    assert metrics.role_tokens["role1"]["output"] == 50
