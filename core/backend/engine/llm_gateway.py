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
        
        # Configuration for generative-role
        # Fallback order: Primary (Claude 3.5 Sonnet via OpenRouter) -> Fallback (Qwen 2.5 32B via Ollama)
        generative_model_list = [
            {
                "model_name": "generative-role",
                "litellm_params": {
                    "model": "openrouter/anthropic/claude-3.5-sonnet",
                    "api_key": os.getenv("OPENROUTER_API_KEY"),
                    "timeout": self.timeout,
                },
            },
            {
                "model_name": "generative-role",
                "litellm_params": {
                    "model": "ollama/qwen2.5:32b",
                    "api_base": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    "timeout": self.timeout,
                },
            }
        ]

        # Configuration for validation-role
        # Fallback order: Primary (Qwen 3.5 9B via OpenRouter) -> Fallback (Qwen 3.5 9B via Ollama)
        validation_model_list = [
            {
                "model_name": "validation-role",
                "litellm_params": {
                    "model": "openrouter/qwen/qwen-2.5-72b-instruct", # Using a common qwen model as placeholder if 3.5-9b is not on OpenRouter yet, or following instruction
                    "api_key": os.getenv("OPENROUTER_API_KEY"),
                    "timeout": self.timeout,
                },
            },
            {
                "model_name": "validation-role",
                "litellm_params": {
                    "model": "ollama/qwen2.5:7b", # placeholder for qwen3.5-9b
                    "api_base": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    "timeout": self.timeout,
                },
            }
        ]
        
        # Adjusting models to match exact requested names if possible, but OpenRouter naming varies.
        # The prompt specified:
        # generative-role: openrouter/anthropic/claude-sonnet-4-5 (Wait, prompt said 4-5, but Sonnet 3.5 is current. I will use the one in prompt if it exists or Sonnet 3.5)
        # fallback: ollama/qwen2.5:32b
        # validation-role: openrouter/qwen/qwen3.5-9b
        # fallback: ollama/qwen3.5:9b

        # Redefining with exact prompt names
        generative_model_list = [
            {
                "model_name": "generative-role",
                "litellm_params": {
                    "model": "openrouter/anthropic/claude-sonnet-4-5",
                    "api_key": os.getenv("OPENROUTER_API_KEY"),
                },
            },
            {
                "model_name": "generative-role",
                "litellm_params": {
                    "model": "ollama/qwen2.5:32b",
                    "api_base": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                },
            }
        ]

        validation_model_list = [
            {
                "model_name": "validation-role",
                "litellm_params": {
                    "model": "openrouter/qwen/qwen3.5-9b",
                    "api_key": os.getenv("OPENROUTER_API_KEY"),
                },
            },
            {
                "model_name": "validation-role",
                "litellm_params": {
                    "model": "ollama/qwen3.5:9b",
                    "api_base": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                },
            }
        ]

        self.router = Router(
            model_list=generative_model_list + validation_model_list,
            fallbacks=[
                {"generative-role": ["generative-role"]}, # LiteLLM uses model_name for routing fallbacks within same name
                {"validation-role": ["validation-role"]}
            ],
            context_window_fallbacks=None,
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
