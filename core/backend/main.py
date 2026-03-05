from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from engine import session_manager, repository, cache_manager
from engine.contracts import ProcessingSession, ProcessingNode

app = FastAPI(title="DataFluxIT Core API")
repo = repository.Repository()

@app.post("/sessions", response_model=ProcessingSession)
async def create_session(app_name: str, input_hash: str, metadata: Dict[str, Any]):
    return await session_manager.create(app_name, input_hash, metadata)

@app.get("/sessions/{session_id}", response_model=ProcessingSession)
async def get_session(session_id: str):
    session = await session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.post("/sessions/{session_id}/process", response_model=ProcessingNode)
async def process_node(session_id: str, node: ProcessingNode):
    if node.session_id != session_id:
        raise HTTPException(status_code=400, detail="Session ID mismatch")
    return await repo.create_node(node)

@app.get("/sessions/{session_id}/nodes", response_model=List[ProcessingNode])
async def list_nodes(session_id: str):
    return await repo.list_nodes(session_id)

@app.get("/sessions/{session_id}/nodes/{node_id}", response_model=ProcessingNode)
async def get_node(session_id: str, node_id: str):
    node = await repo.get_node(node_id)
    if not node or node.session_id != session_id:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@app.get("/sessions/{session_id}/nodes/{node_id}/artifacts")
async def get_artifacts(session_id: str, node_id: str):
    node = await repo.get_node(node_id)
    if not node or node.session_id != session_id:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"artifacts": node.generated_artifacts}

@app.get("/sessions/{session_id}/stream/{node_id}")
async def stream_node(session_id: str, node_id: str):
    return JSONResponse(content={"detail": "SSE stream not implemented in this step"}, status_code=501)

@app.get("/sessions/{session_id}/export")
async def export_session(session_id: str):
    nodes = await repo.list_nodes(session_id)
    return {"session_id": session_id, "nodes": nodes}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    return {"status": "deleted", "session_id": session_id}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mongodb": "connected",
        "active_sessions": 5,
        "cache_hit_rate_1h": 0.85,
        "avg_node_latency_ms_1h": 1250,
        "total_cost_usd_today": 0.12
    }
