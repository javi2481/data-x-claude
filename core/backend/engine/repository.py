import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .contracts import ProcessingSession, ProcessingNode


class Repository:
    """MongoDB repository for sessions and processing nodes."""

    def __init__(self, mongo_uri: str | None = None, db_name: str | None = None) -> None:
        uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        name = db_name or os.getenv("MONGO_DB_NAME", "explorex")
        self._client = AsyncIOMotorClient(uri)
        self._db: AsyncIOMotorDatabase = self._client[name]
        self._sessions = self._db["sessions"]
        self._nodes = self._db["nodes"]

    async def create_session(self, session: ProcessingSession) -> ProcessingSession:
        await self._sessions.insert_one(session.model_dump())
        return session

    async def get_session(self, session_id: str) -> Optional[ProcessingSession]:
        doc = await self._sessions.find_one({"id": session_id})
        return ProcessingSession(**doc) if doc else None

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> ProcessingSession:
        if "last_active" not in updates:
            updates["last_active"] = datetime.now(timezone.utc)
        
        await self._sessions.update_one(
            {"id": session_id},
            {"$set": updates},
        )
        updated_doc = await self._sessions.find_one({"id": session_id})
        if not updated_doc:
            raise ValueError(f"Session {session_id} not found")
        return ProcessingSession(**updated_doc)

    async def create_node(self, node: ProcessingNode) -> ProcessingNode:
        await self._nodes.insert_one(node.model_dump())
        # Incrementar contador de nodos en la sesión
        await self._sessions.update_one(
            {"id": node.session_id},
            {
                "$inc": {"node_count": 1},
                "$set": {"last_active": datetime.now(timezone.utc)}
            }
        )
        return node

    async def get_node(self, node_id: str) -> Optional[ProcessingNode]:
        doc = await self._nodes.find_one({"id": node_id})
        return ProcessingNode(**doc) if doc else None

    async def update_node(self, node_id: str, updates: Dict[str, Any]) -> ProcessingNode:
        await self._nodes.update_one(
            {"id": node_id},
            {"$set": updates},
        )
        updated_doc = await self._nodes.find_one({"id": node_id})
        if not updated_doc:
            raise ValueError(f"Node {node_id} not found")
        
        # Actualizar last_active de la sesión
        node = ProcessingNode(**updated_doc)
        await self._sessions.update_one(
            {"id": node.session_id},
            {"$set": {"last_active": datetime.now(timezone.utc)}}
        )
        return node

    async def list_nodes(self, session_id: str) -> List[ProcessingNode]:
        cursor = self._nodes.find({"session_id": session_id})
        return [ProcessingNode(**doc) async for doc in cursor]
