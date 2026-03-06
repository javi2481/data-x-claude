import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from apps.explorex.backend.kernel_manager import KernelManager, KernelOutput

@pytest.fixture
def km():
    return KernelManager()

@pytest.mark.asyncio
async def test_start_kernel():
    with patch("jupyter_client.AsyncKernelManager.start_kernel", new_callable=AsyncMock) as mock_start, \
         patch("jupyter_client.AsyncKernelManager.client") as mock_client:
        
        mock_kc = MagicMock()
        mock_kc.wait_for_ready = AsyncMock()
        mock_client.return_value = mock_kc
        
        manager = KernelManager()
        session_id = "sess1"
        kid = await manager.start_kernel(session_id)
        
        assert kid == session_id
        assert session_id in manager.kernels
        assert mock_start.called
        assert mock_kc.start_channels.called

@pytest.mark.asyncio
async def test_load_dataset_once(km):
    km.execute = AsyncMock(return_value=KernelOutput(stdout="", stderr="", success=True))
    km.loaded_datasets["k1"] = False
    km.clients["k1"] = MagicMock()
    
    await km.load_dataset("k1", "data.csv")
    await km.load_dataset("k1", "data.csv")
    
    # Debe llamarse una sola vez
    assert km.execute.call_count == 1

@pytest.mark.asyncio
async def test_execute_success(km):
    mock_kc = MagicMock()
    mock_kc.execute.return_value = "msg1"
    
    # Mockear flujo de mensajes de iopub
    # 1. stream stdout
    # 2. status idle
    # 3. stream results (nuevo flujo de inspección con delimitadores)
    # 4. status idle (fin inspección)
    mock_kc.get_iopub_msg = AsyncMock()
    mock_kc.get_iopub_msg.side_effect = [
        {"msg_type": "stream", "content": {"name": "stdout", "text": "hello"}},
        {"msg_type": "status", "content": {"execution_state": "idle"}},
        {"msg_type": "stream", "content": {"name": "stdout", "text": "__RESULT_START__\n{}\n__RESULT_END__\n__SUMMARY_START__\n{}\n__SUMMARY_END__"}},
        {"msg_type": "status", "content": {"execution_state": "idle"}}
    ]
    
    km.clients["k1"] = mock_kc
    result = await km.execute("k1", "print('hello')")
    
    assert result.success
    assert result.stdout == "hello"

@pytest.mark.asyncio
async def test_execute_error(km):
    mock_kc = MagicMock()
    mock_kc.get_iopub_msg = AsyncMock()
    mock_kc.get_iopub_msg.side_effect = [
        {"msg_type": "error", "content": {"ename": "NameError", "evalue": "name 'invalid' is not defined", "traceback": ["Error line 1"]}},
        {"msg_type": "status", "content": {"execution_state": "idle"}}
    ]
    
    km.clients["k1"] = mock_kc
    result = await km.execute("k1", "invalid")
    
    assert not result.success
    assert "Error line 1" in result.stderr
