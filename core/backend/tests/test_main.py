import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from core.backend.main import app
from core.backend.engine.contracts import ProcessingSession, ProcessingNode

client = TestClient(app)

@pytest.fixture
def mock_session():
    return ProcessingSession(
        id="session123",
        app_name="explorex",
        input_hash="hash123",
        input_metadata={},
        status="active"
    )

@pytest.fixture
def mock_node():
    return ProcessingNode(
        id="node123",
        session_id="session123",
        app_name="explorex",
        trigger_type="auto",
        trigger_input="test",
        status="completed"
    )

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@patch("core.backend.engine.session_manager.create", new_callable=AsyncMock)
def test_create_session(mock_create, mock_session):
    mock_create.return_value = mock_session
    response = client.post("/sessions?app_name=explorex&input_hash=hash123", json={})
    assert response.status_code == 200
    assert response.json()["id"] == "session123"

@patch("core.backend.engine.session_manager.get", new_callable=AsyncMock)
def test_get_session(mock_get, mock_session):
    mock_get.return_value = mock_session
    response = client.get("/sessions/session123")
    assert response.status_code == 200
    assert response.json()["id"] == "session123"

@patch("core.backend.engine.repository.Repository.create_node", new_callable=AsyncMock)
def test_process_node(mock_create_node, mock_node):
    mock_create_node.return_value = mock_node
    # Usar json.loads(mock_node.model_dump_json()) para asegurar serialización compatible
    import json
    response = client.post("/sessions/session123/process", json=json.loads(mock_node.model_dump_json()))
    assert response.status_code == 200
    assert response.json()["id"] == "node123"

@patch("core.backend.engine.repository.Repository.list_nodes", new_callable=AsyncMock)
def test_list_nodes(mock_list_nodes, mock_node):
    mock_list_nodes.return_value = [mock_node]
    response = client.get("/sessions/session123/nodes")
    assert response.status_code == 200
    assert len(response.json()) == 1

@patch("core.backend.engine.repository.Repository.get_node", new_callable=AsyncMock)
def test_get_node(mock_get_node, mock_node):
    mock_get_node.return_value = mock_node
    response = client.get("/sessions/session123/nodes/node123")
    assert response.status_code == 200
    assert response.json()["id"] == "node123"

def test_delete_session():
    response = client.delete("/sessions/session123")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
