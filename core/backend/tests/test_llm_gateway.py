import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from engine.llm_gateway import LLMGateway
from engine.contracts import LLMRole, LLMRoleResult

@pytest.fixture
def gateway():
    with patch('engine.llm_gateway.Router'):
        return LLMGateway()

@pytest.mark.asyncio
async def test_call_success(gateway):
    role = LLMRole(
        name="test-role",
        model_category="generative-role",
        prompt_template="Test {data}"
    )
    messages = [{"role": "user", "content": "hello"}]
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response content"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.model = "openrouter/anthropic/claude-sonnet-4-5"
    
    gateway.router.acompletion = AsyncMock(return_value=mock_response)
    
    result = await gateway.call(role, messages)
    
    assert result.content == "Response content"
    assert result.tokens_in == 10
    assert result.tokens_out == 5
    assert result.model_used == "openrouter/anthropic/claude-sonnet-4-5"
    assert result.latency_ms >= 0

@pytest.mark.asyncio
async def test_call_with_fallback(gateway):
    role = LLMRole(
        name="test-role",
        model_category="generative-role",
        prompt_template="Test {data}"
    )
    messages = [{"role": "user", "content": "hello"}]
    
    # Simular que el primer modelo falla y el router maneja el fallback.
    # En LiteLLM Router, si pasamos el nombre del grupo de modelos ("generative-role"), 
    # el Router mismo se encarga del reintento si está configurado.
    # Aquí probamos que si el router devuelve una respuesta exitosa (posiblemente del fallback),
    # el gateway la procesa correctamente.
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Fallback response"
    mock_response.usage.prompt_tokens = 15
    mock_response.usage.completion_tokens = 10
    mock_response.model = "ollama/qwen2.5:32b"
    
    gateway.router.acompletion = AsyncMock(return_value=mock_response)
    
    result = await gateway.call(role, messages)
    
    assert result.content == "Fallback response"
    assert result.model_used == "ollama/qwen2.5:32b"

@pytest.mark.asyncio
async def test_stream(gateway):
    role = LLMRole(
        name="test-role",
        model_category="generative-role",
        prompt_template="Test {data}"
    )
    messages = [{"role": "user", "content": "hello"}]
    
    async def mock_async_iterator():
        chunks = ["Hello", " world", "!"]
        for chunk in chunks:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = chunk
            yield mock_chunk

    gateway.router.acompletion = AsyncMock(return_value=mock_async_iterator())
    
    collected_content = ""
    async for delta in gateway.stream(role, messages):
        collected_content += delta
        
    assert collected_content == "Hello world!"
