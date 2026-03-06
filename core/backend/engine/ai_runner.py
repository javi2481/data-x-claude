import asyncio
from typing import List, Dict, Any
from .contracts import LLMRole, LLMRoleResult, ProcessingSession, NodeMetrics
from .llm_gateway import LLMGateway
from .prompt_builder import render

# Singleton de gateway para reuso
_gateway = LLMGateway()

async def run(roles: List[LLMRole], context: Dict[str, Any], session: ProcessingSession) -> List[LLMRoleResult]:
    """
    Ejecución secuencial de roles.
    El output de cada rol se agrega al contexto bajo la clave '{role.name}_output' para el siguiente.
    """
    results = []
    current_context = context.copy()
    
    for role in roles:
        # Renderizar prompt usando el contexto actual
        prompt = render(role.prompt_template, current_context)
        messages = [{"role": "user", "content": prompt}]
        
        # Llamar al LLM vía gateway
        result = await _gateway.call(role, messages)
        results.append(result)
        
        # Actualizar contexto para el siguiente rol
        current_context[f"{role.name}_output"] = result.content
        if result.structured_output:
            current_context[f"{role.name}_structured"] = result.structured_output
            
    return results

async def run_parallel(roles: List[LLMRole], context: Dict[str, Any], session: ProcessingSession) -> List[LLMRoleResult]:
    """
    Ejecución paralela de roles.
    Todos reciben el mismo contexto original.
    """
    async def run_single_role(role: LLMRole):
        prompt = render(role.prompt_template, context)
        messages = [{"role": "user", "content": prompt}]
        return await _gateway.call(role, messages)

    tasks = [run_single_role(role) for role in roles]
    results = await asyncio.gather(*tasks)
    return list(results)

def get_node_metrics(session_id: str, node_id: str, app_name: str, results: List[LLMRoleResult], roles: List[LLMRole], cached: bool = False) -> NodeMetrics:
    """Calcula las métricas agregadas de una corrida de roles."""
    total_latency = sum(r.latency_ms for r in results)
    role_latencies = {role.name: r.latency_ms for role, r in zip(roles, results)}
    role_tokens = {role.name: {"input": r.tokens_in, "output": r.tokens_out} for role, r in zip(roles, results)}
    role_costs = {role.name: 0.0 for role in roles} # TODO: Implementar cálculo de costo real si es necesario
    
    return NodeMetrics(
        session_id=session_id,
        node_id=node_id,
        app_name=app_name,
        cached=cached,
        total_latency_ms=total_latency,
        role_latencies=role_latencies,
        role_tokens=role_tokens,
        role_costs_usd=role_costs
    )
