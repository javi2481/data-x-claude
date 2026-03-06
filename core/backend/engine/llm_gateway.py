import os
import time
import json
from typing import List, AsyncIterator, Optional, Dict, Any
from litellm import Router, completion
import litellm

from .contracts import LLMRole, LLMRoleResult

class LLMGateway:
    """Gateway for LLM interactions using LiteLLM Router."""

    def __init__(self):
        self.timeout = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "60"))
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        openrouter_api_base = "https://openrouter.ai/api/v1"
        
        # Models configuration from environment
        coder_model = os.getenv("CODER_MODEL", "openrouter/anthropic/claude-3.5-sonnet")
        reviewer_model = os.getenv("REVIEWER_MODEL", "openrouter/qwen/qwen3-32b")
        interpreter_model = os.getenv("INTERPRETER_MODEL", "openrouter/anthropic/claude-3.5-sonnet")

        # Configuration for generative-role (Coder / Interpreter)
        generative_model_list = [
            {
                "model_name": "generative-role",
                "litellm_params": {
                    "model": coder_model,
                    "api_key": openrouter_api_key,
                    "api_base": openrouter_api_base,
                    "timeout": self.timeout,
                },
            }
        ]

        # Configuration for validation-role (Reviewer)
        validation_model_list = [
            {
                "model_name": "validation-role",
                "litellm_params": {
                    "model": reviewer_model,
                    "api_key": openrouter_api_key,
                    "api_base": openrouter_api_base,
                    "timeout": self.timeout,
                },
            }
        ]
        
        self.router = Router(
            model_list=generative_model_list + validation_model_list,
            set_verbose=False
        )

    async def call(self, role: LLMRole, messages: List[Dict[str, str]]) -> LLMRoleResult:
        """Call LLM synchronously (but awaited) through the router."""
        start_time = time.time()
        
        kwargs = {
            "model": role.model_category,
            "messages": messages,
            "temperature": role.temperature,
            "timeout": role.timeout_seconds or self.timeout,
        }
        
        if role.response_schema:
            kwargs["response_format"] = {"type": "json_object", "schema": role.response_schema}

        response = await self.router.acompletion(**kwargs)
        
        latency_ms = int((time.time() - start_time) * 1000)
        content = response.choices[0].message.content
        
        structured_output = None
        if role.response_schema:
            try:
                structured_output = json.loads(content)
            except json.JSONDecodeError:
                pass # Or handle error

        return LLMRoleResult(
            content=content,
            structured_output=structured_output,
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
            latency_ms=latency_ms,
            model_used=response.model
        )

    async def stream(self, role: LLMRole, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """Stream LLM response through the router."""
        kwargs = {
            "model": role.model_category,
            "messages": messages,
            "temperature": role.temperature,
            "timeout": role.timeout_seconds or self.timeout,
            "stream": True
        }
        
        response = await self.router.acompletion(**kwargs)
        
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
