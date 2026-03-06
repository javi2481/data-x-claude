from __future__ import annotations
import os
import shutil
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio

class KernelInfo:
    def __init__(self, notebook_path: str, last_used: datetime) -> None:
        self.notebook_path = notebook_path
        self.last_used = last_used

class KernelLifecycleManager:
    """Manages session notebook paths and their lifecycle (TTL eviction)."""

    def __init__(self, ttl_minutes: int = 30) -> None:
        self._kernels: Dict[str, KernelInfo] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "notebooks"))
        self._sessions_path = os.path.join(self._base_path, "sessions")
        self._template_path = os.path.join(self._base_path, "template.ipynb")
        os.makedirs(self._sessions_path, exist_ok=True)

    async def get_or_start(self, session_id: str) -> str:
        """Returns the notebook file path for the session, creating it from template if new."""
        info = self._kernels.get(session_id)
        if info:
            info.last_used = datetime.utcnow()
            return info.notebook_path
        
        # Create session notebook from template
        notebook_path = os.path.join(self._sessions_path, f"{session_id}.ipynb")
        if not os.path.exists(notebook_path):
            shutil.copy2(self._template_path, notebook_path)
            
        self._kernels[session_id] = KernelInfo(notebook_path=notebook_path, last_used=datetime.utcnow())
        return notebook_path

    async def restart(self, session_id: str) -> None:
        """Restart session by recreating notebook from template."""
        info = self._kernels.get(session_id)
        if info:
            shutil.copy2(self._template_path, info.notebook_path)
            info.last_used = datetime.utcnow()

    async def shutdown(self, session_id: str) -> None:
        """Remove session notebook."""
        info = self._kernels.pop(session_id, None)
        if info:
            try:
                if os.path.exists(info.notebook_path):
                    os.remove(info.notebook_path)
            except Exception:
                pass

    async def evict_expired(self) -> None:
        cutoff = datetime.utcnow() - self._ttl
        expired = [sid for sid, info in self._kernels.items() if info.last_used < cutoff]
        for sid in expired:
            await self.shutdown(sid)

    async def periodic_eviction(self, interval_seconds: int = 60) -> None:
        while True:
            await self.evict_expired()
            await asyncio.sleep(interval_seconds)
