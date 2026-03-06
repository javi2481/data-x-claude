import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from core.backend.engine import cache_manager
from core.backend.engine.contracts import ProcessingNode, NodeMetrics
from motor.motor_asyncio import AsyncIOMotorClient

# Mockear configuración para tests
cache_manager.DB_NAME = "explorex_cache_test"

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def clear_cache():
    # Reiniciar singleton de cache_manager para cada test para evitar loops cerrados
    cache_manager._client = None
    cache_manager._collection = None
    collection = await cache_manager._get_collection()
    await collection.delete_many({})

@pytest.mark.asyncio
async def test_build_key():
    key1 = cache_manager.build_key("input1", "sec1")
    key2 = cache_manager.build_key("input1", "sec1")
    key3 = cache_manager.build_key("input2", "sec1")
    
    assert key1 == key2
    assert key1 != key3
    assert len(key1) == 64 # SHA256 hex length

@pytest.mark.asyncio
async def test_set_get_hit():
    key = "test_hit"
    node = ProcessingNode(
        id="node123",
        session_id="session123",
        app_name="explorex",
        trigger_type="auto",
        trigger_input="test input",
        status="completed"
    )
    
    await cache_manager.set(key, node)
    cached_node = await cache_manager.get(key)
    
    assert cached_node is not None
    assert cached_node.session_id == node.session_id
    assert cached_node.id == node.id

@pytest.mark.asyncio
async def test_get_miss():
    key = "non_existent"
    cached_node = await cache_manager.get(key)
    assert cached_node is None

@pytest.mark.asyncio
async def test_invalidate():
    key = "to_invalidate"
    node = ProcessingNode(
        id="node_inv",
        session_id="session123",
        app_name="explorex",
        trigger_type="auto",
        trigger_input="test input",
        status="completed"
    )
    
    await cache_manager.set(key, node)
    await cache_manager.invalidate(key)
    cached_node = await cache_manager.get(key)
    
    assert cached_node is None

@pytest.mark.asyncio
async def test_ttl_expiry():
    key = "expiring_key"
    node = ProcessingNode(
        id="node_exp",
        session_id="session123",
        app_name="explorex",
        trigger_type="auto",
        trigger_input="test input",
        status="completed"
    )
    
    # Simular expiración poniendo una fecha en el pasado
    collection = await cache_manager._get_collection()
    expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    
    await collection.insert_one({
        "_id": key,
        "node_data": node.model_dump(),
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=60)
    })
    
    cached_node = await cache_manager.get(key)
    assert cached_node is None
    
    # Verificar que se eliminó de la DB
    doc = await collection.find_one({"_id": key})
    assert doc is None
