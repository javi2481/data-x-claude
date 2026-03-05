import sys
import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Añadir core/backend al path para importar el motor
CORE_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "core", "backend"))
if CORE_BACKEND_PATH not in sys.path:
    sys.path.insert(0, CORE_BACKEND_PATH)

# Cargar variables de entorno desde core/backend/.env
ENV_PATH = os.path.join(CORE_BACKEND_PATH, ".env")
load_dotenv(ENV_PATH)

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional

from engine import (
    cache_manager, 
    llm_gateway, 
    repository, 
    session_manager,
    contracts
)
import kernel_manager, result_parser
from prompts import initial, drilldown, suggestions

app = FastAPI(title="Explorex Application")
repo = repository.Repository()
kernels = kernel_manager.KernelManager()
gateway = llm_gateway.LLMGateway()

# Roles configurados para Explorex
coder_role = contracts.LLMRole(
    name="CODER",
    model_category="generative-role",
    prompt_template="", # Se asignará dinámicamente según el paso
    temperature=0.1
)
reviewer_role = contracts.LLMRole(
    name="REVIEWER",
    model_category="validation-role",
    prompt_template="",
    temperature=0.0
)
interpreter_role = contracts.LLMRole(
    name="INTERPRETER",
    model_category="generative-role",
    prompt_template="",
    temperature=0.5
)

@app.post("/sessions/{session_id}/analyze")
async def analyze(session_id: str, prompt: str = Body(..., embed=True), trigger_type: str = Body("auto", embed=True)):
    # 1. Obtener sesión
    session = await session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    dataset_hash = session.input_hash
    schema = session.input_metadata.get("schema", "No schema available")
    
    # 2. Cache check
    cache_key = cache_manager.build_key(dataset_hash, prompt)
    cached_node = await cache_manager.get(cache_key)
    if cached_node:
        return {"node": cached_node, "cached": True}

    # 3. Determinar templates
    if trigger_type == "auto":
        templates = initial
    elif trigger_type == "click":
        templates = drilldown
    else:
        templates = initial # Default
        
    # 4. Pipeline LLM: Coder
    from engine.prompt_builder import render
    
    # Render Coder
    coder_role.prompt_template = templates.coder_template
    coder_prompt = render(coder_role.prompt_template, {
        "dataset_hash": dataset_hash,
        "schema": schema,
        "prompt": prompt,
        "parent_context": "Initial exploration"
    })
    coder_res = await gateway.call(coder_role, [{"role": "user", "content": coder_prompt}])
    generated_code = coder_res.content

    # 5. Pipeline LLM: Reviewer
    reviewer_role.prompt_template = templates.reviewer_template
    reviewer_prompt = render(reviewer_role.prompt_template, {
        "schema": schema,
        "code": generated_code
    })
    reviewer_res = await gateway.call(reviewer_role, [{"role": "user", "content": reviewer_prompt}])
    reviewed_code = reviewer_res.content

    # 6. Kernel Execution
    await kernels.start_kernel(session_id)
    dataset_path = session.input_metadata.get("dataset_path")
    if dataset_path:
        await kernels.load_dataset(session_id, dataset_path)
    
    kernel_output = await kernels.execute(session_id, reviewed_code)
    if not kernel_output.success:
        raise HTTPException(status_code=500, detail=f"Kernel execution failed: {kernel_output.stderr}")

    # 7. Result Parsing
    parsed_result = result_parser.parse(kernel_output.stdout)

    # 8. Pipeline LLM: Interpreter
    interpreter_role.prompt_template = templates.interpreter_template
    interpreter_prompt = render(interpreter_role.prompt_template, {
        "prompt": prompt,
        "statistics": parsed_result.statistics,
        "computed_values": parsed_result.computed_values,
        "chart_description": parsed_result.chart_description,
        "data_warnings": parsed_result.data_warnings
    })
    interpreter_res = await gateway.call(interpreter_role, [{"role": "user", "content": interpreter_prompt}])
    interpretation = interpreter_res.content

    # 9. Persistencia y Cache
    import uuid
    node = contracts.ProcessingNode(
        id=str(uuid.uuid4()),
        session_id=session_id,
        app_name="explorex",
        trigger_type=trigger_type,
        trigger_input=prompt,
        status="completed",
        output={
            "interpretation": interpretation,
            "plotly_figure": parsed_result.plotly_figure,
            "statistics": parsed_result.statistics
        },
        audit_document=f"# Analysis: {prompt}\n\n{interpretation}",
        generated_artifacts=[reviewed_code],
        cached=False
    )
    
    await repo.create_node(node)
    await cache_manager.set(cache_key, node)
    
    return {"node": node, "cached": False}

@app.get("/config")
async def get_config():
    return {"app": "explorex", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "app": "explorex"}
