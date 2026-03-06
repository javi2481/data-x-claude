import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from apps.explorex.backend.app import app
from core.backend.engine.contracts import ProcessingSession, ProcessingNode, LLMRoleResult
from apps.explorex.backend.kernel_manager import KernelOutput

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
    with patch("apps.explorex.backend.app.session_manager.get", new_callable=AsyncMock) as mock_get_sess, \
         patch("apps.explorex.backend.app.cache_manager.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("apps.explorex.backend.app.gateway.call", new_callable=AsyncMock) as mock_llm, \
         patch("apps.explorex.backend.app.kernels.start_kernel", new_callable=AsyncMock), \
         patch("apps.explorex.backend.app.kernels.load_dataset", new_callable=AsyncMock), \
         patch("apps.explorex.backend.app.kernels.execute", new_callable=AsyncMock) as mock_exec, \
         patch("apps.explorex.backend.app.repo.create_node", new_callable=AsyncMock), \
         patch("apps.explorex.backend.app.repo.update_node", new_callable=AsyncMock), \
         patch("apps.explorex.backend.app.cache_manager.set", new_callable=AsyncMock):

        mock_get_sess.return_value = mock_session
        mock_cache_get.return_value = None
        
        # LLM Results: Coder, Interpreter
        mock_llm.side_effect = [
            LLMRoleResult(content="print('code')", tokens_in=1, tokens_out=1, latency_ms=1, model_used="m"),
            LLMRoleResult(content="Esta es la interpretación", tokens_in=1, tokens_out=1, latency_ms=1, model_used="m")
        ]
        
        mock_exec.return_value = KernelOutput(stdout='{"json": "here"}', stderr="", success=True, results={"result_summary": {}, "result": {}})
        
        response = client.post("/sessions/s123/analyze", json={"triggerInput": "dime algo", "triggerType": "auto"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        
        # Verificar que se llamó al LLM 2 veces
        assert mock_llm.call_count == 2
        # Verificar que se ejecutó el kernel
        assert mock_exec.called

@pytest.mark.asyncio
async def test_analyze_cache_hit(mock_session):
    with patch("apps.explorex.backend.app.session_manager.get", new_callable=AsyncMock) as mock_get_sess, \
         patch("apps.explorex.backend.app.cache_manager.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("apps.explorex.backend.app.repo.create_node", new_callable=AsyncMock):
        
        mock_get_sess.return_value = mock_session
        
        # Simular hit en caché
        cached_node = ProcessingNode(
            id="n-cached", session_id="s123", app_name="explorex", 
            trigger_type="auto", trigger_input="prompt", status="completed",
            output={"interpretation": "cached interpret"}
        )
        mock_cache_get.return_value = cached_node
        
        response = client.post("/sessions/s123/analyze", json={"triggerInput": "prompt", "triggerType": "auto"})
        
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
