import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from ..app import app
from engine.contracts import ProcessingSession, ProcessingNode, LLMRoleResult
from ..kernel_manager import KernelOutput
from ..result_parser import ParsedResult

client = TestClient(app)

@pytest.fixture
def mock_session():
    return ProcessingSession(
        id="s123",
        app_name="explorex",
        input_hash="h123",
        input_metadata={"schema": "col1, col2", "dataset_path": "data.csv"},
        status="active"
    )

@pytest.mark.asyncio
async def test_analyze_pipeline(mock_session):
    # Mocks para todo el pipeline
    with patch("core.backend.engine.session_manager.get", new_callable=AsyncMock) as mock_get_sess, \
         patch("core.backend.engine.cache_manager.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("core.backend.engine.llm_gateway.LLMGateway.call", new_callable=AsyncMock) as mock_llm, \
         patch("apps.explorex.backend.kernel_manager.KernelManager.start_kernel", new_callable=AsyncMock), \
         patch("apps.explorex.backend.kernel_manager.KernelManager.load_dataset", new_callable=AsyncMock), \
         patch("apps.explorex.backend.kernel_manager.KernelManager.execute", new_callable=AsyncMock) as mock_exec, \
         patch("apps.explorex.backend.result_parser.parse") as mock_parse, \
         patch("core.backend.engine.repository.Repository.create_node", new_callable=AsyncMock), \
         patch("core.backend.engine.cache_manager.set", new_callable=AsyncMock):
        
        mock_get_sess.return_value = mock_session
        mock_cache_get.return_value = None
        
        # LLM Results: Coder, Reviewer, Interpreter
        mock_llm.side_effect = [
            LLMRoleResult(content="print('code')", tokens_in=1, tokens_out=1, latency_ms=1, model_used="m"),
            LLMRoleResult(content="print('reviewed')", tokens_in=1, tokens_out=1, latency_ms=1, model_used="m"),
            LLMRoleResult(content="Esta es la interpretación", tokens_in=1, tokens_out=1, latency_ms=1, model_used="m")
        ]
        
        mock_exec.return_value = KernelOutput(stdout='{"json": "here"}', stderr="", success=True)
        
        mock_parse.return_value = ParsedResult(
            plotly_figure={},
            statistics={},
            computed_values={},
            chart_description="desc",
            data_warnings=[]
        )
        
        response = client.post("/sessions/s123/analyze", json={"prompt": "dime algo", "trigger_type": "auto"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is False
        assert data["node"]["output"]["interpretation"] == "Esta es la interpretación"
        
        # Verificar que se llamó al LLM 3 veces
        assert mock_llm.call_count == 3
        # Verificar que se ejecutó el kernel
        assert mock_exec.called

@pytest.mark.asyncio
async def test_analyze_cache_hit(mock_session):
    with patch("core.backend.engine.session_manager.get", new_callable=AsyncMock) as mock_get_sess, \
         patch("core.backend.engine.cache_manager.get", new_callable=AsyncMock) as mock_cache_get:
        
        mock_get_sess.return_value = mock_session
        
        # Simular hit en caché
        cached_node = ProcessingNode(
            id="n-cached", session_id="s123", app_name="explorex", 
            trigger_type="auto", trigger_input="prompt", status="completed",
            output={"interpretation": "cached interpret"}
        )
        mock_cache_get.return_value = cached_node
        
        response = client.post("/sessions/s123/analyze", json={"prompt": "prompt", "trigger_type": "auto"})
        
        assert response.status_code == 200
        assert response.json()["cached"] is True
        assert response.json()["node"]["id"] == "n-cached"
