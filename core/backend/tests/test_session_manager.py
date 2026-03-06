import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from core.backend.engine import session_manager, repository
from core.backend.engine.contracts import ProcessingSession

# Usar DB de test
session_manager._repo = repository.Repository(db_name="explorex_test")

@pytest.fixture(autouse=True)
async def clear_db():
    # Reiniciar Repository para cada test para evitar loops cerrados
    session_manager._repo = repository.Repository(db_name="explorex_test")
    await session_manager._repo._sessions.delete_many({})

@pytest.mark.asyncio
async def test_create_session():
    app_name = "explorex"
    input_hash = "abc123hash"
    metadata = {"dataset": "test.csv"}
    
    session = await session_manager.create(app_name, input_hash, metadata)
    
    assert session.app_name == app_name
    assert session.input_hash == input_hash
    assert session.input_metadata == metadata
    assert session.status == "active"
    assert session.id is not None

@pytest.mark.asyncio
async def test_get_session():
    session_orig = await session_manager.create("app", "hash", {})
    session_retrieved = await session_manager.get(session_orig.id)
    
    assert session_retrieved is not None
    assert session_retrieved.id == session_orig.id

@pytest.mark.asyncio
async def test_expire_inactive():
    # Sesión 1: Por expirar (inactiva hace 60 min, TTL 30 min)
    s1 = ProcessingSession(
        id="s1", app_name="test", input_hash="h1", input_metadata={}, status="active",
        last_active=datetime.now(timezone.utc) - timedelta(minutes=60),
        ttl_minutes=30
    )
    await session_manager._repo.create_session(s1)
    
    # Sesión 2: Por mantener (inactiva hace 10 min, TTL 30 min)
    s2 = ProcessingSession(
        id="s2", app_name="test", input_hash="h2", input_metadata={}, status="active",
        last_active=datetime.now(timezone.utc) - timedelta(minutes=10),
        ttl_minutes=30
    )
    await session_manager._repo.create_session(s2)
    
    expired_count = await session_manager.expire_inactive()
    
    assert expired_count == 1
    
    s1_check = await session_manager.get("s1")
    assert s1_check.status == "expired"
    
    s2_check = await session_manager.get("s2")
    assert s2_check.status == "active"
