import pytest
import json
from datetime import datetime
from ..notebook_exporter import NotebookExporter
from engine.contracts import ProcessingSession, ProcessingNode
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_export_notebook_success():
    repo = MagicMock()
    session = ProcessingSession(
        id="sess_123",
        app_name="explorex",
        input_hash="hash",
        input_metadata={
            "dataset_name": "test.csv",
            "dataset_path": "/tmp/test.csv"
        },
        status="active",
        created_at=datetime.now(),
        last_active=datetime.now()
    )
    
    node1 = ProcessingNode(
        id="node_1",
        app_name="explorex",
        session_id="sess_123",
        trigger_input="What is the distribution of prices?",
        trigger_type="question",
        status="completed",
        output={
            "interpretation": "Interpretation 1",
            "audit_summary": "Summary 1",
            "reviewed_code": "print('Hello')"
        },
        created_at=datetime.now()
    )
    
    node2 = ProcessingNode(
        id="node_2",
        app_name="explorex",
        session_id="sess_123",
        trigger_input="Show correlation",
        trigger_type="suggestion",
        status="completed",
        output={
            "interpretation": "Interpretation 2",
            "audit_summary": "Summary 2",
            "reviewed_code": "print('Correlation')"
        },
        created_at=datetime.now()
    )
    
    repo.get_session = AsyncMock(return_value=session)
    repo.list_nodes = AsyncMock(return_value=[node1, node2])
    
    exporter = NotebookExporter(repo)
    result_bytes = await exporter.export("sess_123")
    
    notebook = json.loads(result_bytes.decode('utf-8'))
    
    assert notebook["nbformat"] == 4
    # 2 nodes * 2 cells (MD + Code) + 2 initial cells (MD + Code) = 6 cells
    assert len(notebook["cells"]) == 6
    assert "test.csv" in notebook["cells"][0]["source"][0]
    assert "df = pd.read_csv('/tmp/test.csv')" in notebook["cells"][1]["source"][3]
    assert "Analysis: What is the distribution of prices?" in notebook["cells"][2]["source"][0]
    assert "print('Hello')" in notebook["cells"][3]["source"][0]

@pytest.mark.asyncio
async def test_export_notebook_session_not_found():
    repo = MagicMock()
    repo.get_session = AsyncMock(return_value=None)
    
    exporter = NotebookExporter(repo)
    with pytest.raises(ValueError, match="Session sess_none not found"):
        await exporter.export("sess_none")
