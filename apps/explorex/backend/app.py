import sys
import os

# Determinar el directorio base de la aplicación (apps/explorex/backend)
APP_BACK_PATH = os.path.dirname(os.path.abspath(__file__))
if APP_BACK_PATH not in sys.path:
    sys.path.insert(0, APP_BACK_PATH)

from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
import shutil
from pathlib import Path
import traceback
import uuid
import io

# Añadir core/backend al path para importar el motor
CORE_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "core", "backend"))
if CORE_BACKEND_PATH not in sys.path:
    sys.path.insert(0, CORE_BACKEND_PATH)

# Cargar variables de entorno desde core/backend/.env
ENV_PATH = os.path.join(CORE_BACKEND_PATH, ".env")
load_dotenv(ENV_PATH)

from engine import (
    cache_manager, 
    llm_gateway, 
    repository, 
    session_manager,
    contracts
)
import kernel_manager, dataset_intake, notebook_exporter
from prompts import initial, drilldown, suggestions

app = FastAPI(title="Explorex Application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173", "https://*.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Globales de la App ---
repo = repository.Repository()
kernels = kernel_manager.KernelManager()
gateway = llm_gateway.LLMGateway()
exporter = notebook_exporter.NotebookExporter(repo)

# Roles configurados para Explorex
coder_role = contracts.LLMRole(
    name="CODER",
    model_category="generative-role",
    prompt_template="",
    temperature=0.1
)
interpreter_role = contracts.LLMRole(
    name="INTERPRETER",
    model_category="generative-role",
    prompt_template="",
    temperature=0.5
)

# --- Modelos para el Frontend (Explorex) ---
class AnalyzeRequest(contracts.BaseModel):
    triggerType: str
    triggerInput: str
    parentNodeId: Optional[str] = None

class AnalyzeResponse(contracts.BaseModel):
    nodeId: str
    status: str

# --- Auxiliares ---
async def analyze(session_id: str, prompt: str, trigger_type: str, parent_id: Optional[str] = None) -> contracts.ProcessingNode:
    session = await session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    dataset_hash = session.input_hash
    schema = session.input_metadata.get("schema", "No schema available")
    
    cache_key = cache_manager.build_key(dataset_hash, prompt)
    cached_node = await cache_manager.get(cache_key)
    if cached_node:
        # Si está en cache, creamos un nuevo nodo basado en el cache pero con nuevo ID y parent
        new_node = cached_node.model_copy(update={
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "parent_id": parent_id,
            "cached": True
        })
        await repo.create_node(new_node)
        return new_node

    if trigger_type == "auto":
        templates = initial
    elif trigger_type == "click":
        templates = drilldown
    else:
        templates = initial
        
    from engine.prompt_builder import render
    
    # 4. Pipeline LLM: Coder
    coder_role.prompt_template = templates.coder_template
    coder_prompt = render(coder_role.prompt_template, {
        "dataset_hash": dataset_hash,
        "schema": schema,
        "prompt": prompt,
        "parent_context": "Exploration step"
    })
    coder_res = await gateway.call(coder_role, [{"role": "user", "content": coder_prompt}])
    generated_code = coder_res.content

    # 6. Kernel Execution
    await kernels.start_kernel(session_id)
    dataset_path = session.input_metadata.get("dataset_path")
    if dataset_path:
        await kernels.load_dataset(session_id, dataset_path)
    
    kernel_output = await kernels.execute(session_id, generated_code)
    if not kernel_output.success:
        raise HTTPException(status_code=500, detail=f"Kernel execution failed: {kernel_output.stderr}")

    # 7. Result Parsing
    # parsed_result = result_parser.parse(kernel_output.stdout)
    # TODO: Adaptar result_parser para capturar result y result_summary del kernel_output
    # Por ahora usamos el kernel_output directamente si kernel_manager ya lo parsea
    parsed_result = kernel_output.results 

    # 8. Pipeline LLM: Interpreter
    interpreter_role.prompt_template = templates.interpreter_template
    interpreter_prompt = render(interpreter_role.prompt_template, {
        "prompt": prompt,
        "statistics": parsed_result.get("result_summary", {}),
        "computed_values": {},
        "chart_description": "",
        "data_warnings": []
    })
    interpreter_res = await gateway.call(interpreter_role, [{"role": "user", "content": interpreter_prompt}])
    interpretation = interpreter_res.content

    # 9. Persistencia
    node = contracts.ProcessingNode(
        id=str(uuid.uuid4()),
        parent_id=parent_id,
        session_id=session_id,
        app_name="explorex",
        trigger_type=trigger_type,
        trigger_input=prompt,
        status="completed",
        output={
            "interpretation": interpretation,
            "plotlyFigure": parsed_result.get("result"),
            "statistics": parsed_result.get("result_summary"),
            "generatedCode": generated_code,
            "dataWarnings": []
        },
        audit_document=f"# Analysis: {prompt}\n\n{interpretation}",
        generated_artifacts=[generated_code],
        cached=False
    )
    
    await repo.create_node(node)
    if parent_id:
        await repo.update_node(parent_id, {"children": [node.id]}) # Simplificación: agrega hijo
    
    await cache_manager.set(cache_key, node)
    return node

# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/sessions")
async def create_session(file: UploadFile = File(...)):
    storage_path = os.getenv("DATASET_STORAGE_PATH", "./_datasets")
    Path(storage_path).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(storage_path, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        dataset_profile = dataset_intake.validate(file_path)
        metadata = dataset_profile.dict()
        metadata["dataset_path"] = os.path.abspath(file_path)
        metadata["filename"] = file.filename
        
        session = await session_manager.create(
            app_name="explorex",
            input_hash=dataset_profile.dataset_hash,
            metadata=metadata
        )
        
        await kernels.start_kernel(session.id)
        await kernels.load_dataset(session.id, metadata["dataset_path"])
        
        # Trigger inicial
        await analyze(session.id, prompt="Realiza un análisis inicial de este dataset.", trigger_type="auto")
        
        # Devolvemos el objeto mapeado para el frontend
        return {
            "id": session.id,
            "fileName": session.fileName,
            "createdAt": session.createdAt
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        if os.path.exists(file_path): os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sessions/{session_id}/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(session_id: str, request: AnalyzeRequest):
    node = await analyze(session_id, request.triggerInput, request.triggerType, request.parentNodeId)
    return AnalyzeResponse(nodeId=node.id, status=node.status)

@app.get("/sessions/{session_id}/nodes")
async def get_nodes(session_id: str):
    nodes = await repo.list_nodes(session_id)
    # Mapear para el frontend
    return [{
        "id": n.id,
        "parentId": n.parentId,
        "sessionId": n.sessionId,
        "triggerType": n.triggerType,
        "triggerInput": n.triggerInput,
        "status": n.status,
        "output": n.output,
        "cached": n.cached,
        "children": n.children,
        "createdAt": n.createdAt
    } for n in nodes]

@app.get("/sessions/{session_id}/nodes/{node_id}")
async def get_node(session_id: str, node_id: str):
    node = await repo.get_node(node_id)
    if not node or node.session_id != session_id:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return {
        "id": node.id,
        "parentId": node.parentId,
        "sessionId": node.sessionId,
        "triggerType": node.triggerType,
        "triggerInput": node.triggerInput,
        "status": node.status,
        "output": node.output,
        "cached": node.cached,
        "children": node.children,
        "createdAt": node.createdAt
    }

@app.get("/sessions/{session_id}/nodes/{node_id}/code")
async def get_node_code(session_id: str, node_id: str):
    node = await repo.get_node(node_id)
    if not node: raise HTTPException(status_code=404)
    code = node.output.get("generatedCode", "") if node.output else ""
    return {"code": code}

@app.get("/sessions/{session_id}/nodes/{node_id}/document")
async def get_node_document(session_id: str, node_id: str):
    node = await repo.get_node(node_id)
    if not node: raise HTTPException(status_code=404)
    return {"document": node.audit_document or ""}

@app.get("/sessions/{session_id}/stream/{node_id}")
async def stream_node(session_id: str, node_id: str):
    # Placeholder para SSE
    async def event_generator():
        yield "data: {\"status\": \"completed\"}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/sessions/{session_id}/export")
async def export_notebook(session_id: str):
    try:
        content = await exporter.export(session_id)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/x-ipynb+json",
            headers={"Content-Disposition": f"attachment; filename=explorex-{session_id}.ipynb"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
