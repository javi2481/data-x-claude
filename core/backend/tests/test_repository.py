import pytest
import os
from engine.repository import Repository
from engine.contracts import ProcessingSession, ProcessingNode

@pytest.fixture
async def repo():
    # Usar DB de test
    os.environ["MONGO_DB_NAME"] = "explorex_test"
    repository = Repository()
    yield repository
    # Limpiar después de tests
    await repository._db.sessions.delete_many({})
    await repository._db.nodes.delete_many({})

async def test_create_and_get_session(repo):
    session = ProcessingSession(
        id="s1", 
        app_name="explorex", 
        input_hash="h1", 
        input_metadata={"file": "test.csv"},
        status="active"
    )
    await repo.create_session(session)
    fetched = await repo.get_session("s1")
    assert fetched.app_name == "explorex"
    assert fetched.input_hash == "h1"

async def test_update_session(repo):
    session = ProcessingSession(
        id="s1", 
        app_name="explorex", 
        input_hash="h1", 
        input_metadata={},
        status="active"
    )
    await repo.create_session(session)
    updated = await repo.update_session("s1", {"status": "completed"})
    assert updated.status == "completed"
    
    fetched = await repo.get_session("s1")
    assert fetched.status == "completed"

async def test_create_and_get_node(repo):
    session = ProcessingSession(
        id="s1", app_name="explorex", input_hash="h1", input_metadata={}, status="active"
    )
    await repo.create_session(session)
    
    node = ProcessingNode(
        id="n1", 
        session_id="s1", 
        app_name="explorex",
        trigger_type="auto", 
        trigger_input="in", 
        status="pending"
    )
    await repo.create_node(node)
    
    fetched = await repo.get_node("n1")
    assert fetched.trigger_input == "in"
    assert fetched.session_id == "s1"
    
    # Verificar que el contador de la sesión aumentó
    session_after = await repo.get_session("s1")
    assert session_after.node_count == 1

async def test_update_node(repo):
    session = ProcessingSession(
        id="s1", app_name="explorex", input_hash="h1", input_metadata={}, status="active"
    )
    await repo.create_session(session)
    
    node = ProcessingNode(
        id="n1", 
        session_id="s1", 
        app_name="explorex",
        trigger_type="auto", 
        trigger_input="in", 
        status="pending"
    )
    await repo.create_node(node)
    
    updated = await repo.update_node("n1", {"status": "completed", "audit_document": "Log content"})
    assert updated.status == "completed"
    assert updated.audit_document == "Log content"

async def test_list_nodes(repo):
    session = ProcessingSession(
        id="s1", app_name="explorex", input_hash="h1", input_metadata={}, status="active"
    )
    await repo.create_session(session)
    
    for i in range(3):
        node = ProcessingNode(
            id=f"n{i}", 
            session_id="s1", 
            app_name="explorex",
            trigger_type="auto", 
            trigger_input=f"in {i}", 
            status="pending"
        )
        await repo.create_node(node)
        
    nodes = await repo.list_nodes("s1")
    assert len(nodes) == 3
    assert any(n.id == "n0" for n in nodes)
    assert any(n.id == "n1" for n in nodes)
    assert any(n.id == "n2" for n in nodes)
