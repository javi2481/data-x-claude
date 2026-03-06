import hashlib
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from engine.contracts import ProcessingNode

# Configuración desde el .env
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "mongodb")
CACHE_TTL_MINUTES = int(os.getenv("CACHE_TTL_MINUTES", "1440"))  # Default 24h
MONGO_URI = os.getenv("MONGO_URI", "127.0.0.1:27017")
DB_NAME = "explorex_cache"

_client = None
_collection = None

async def _get_collection():
    global _client, _collection
    if _collection is None:
        if _client is None:
            _client = AsyncIOMotorClient(MONGO_URI)
        _collection = _client[DB_NAME]["cache"]
        # Asegurar índice de expiración si es MongoDB
        await _collection.create_index("expires_at", expireAfterSeconds=0)
    return _collection

def build_key(input_hash: str, secondary_hash: str) -> str:
    """SHA256 de ambos hashes concatenados."""
    combined = f"{input_hash}{secondary_hash}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()

async def get(key: str) -> Optional[ProcessingNode]:
    """Recupera un nodo del caché si existe y no ha expirado."""
    collection = await _get_collection()
    doc = await collection.find_one({"_id": key})
    
    if not doc:
        return None
        
    # El índice expireAfterSeconds de MongoDB debería manejar esto, 
    # pero hacemos un check manual por seguridad si el índice no se ha propagado.
    if doc.get("expires_at") and doc["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        await invalidate(key)
        return None
        
    return ProcessingNode(**doc["node_data"])

async def set(key: str, node: ProcessingNode) -> None:
    """Guarda un nodo en el caché con el TTL configurado."""
    collection = await _get_collection()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=CACHE_TTL_MINUTES)
    
    await collection.replace_one(
        {"_id": key},
        {
            "_id": key,
            "node_data": node.model_dump(),
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        },
        upsert=True
    )

async def invalidate(key: str) -> None:
    """Elimina una entrada específica del caché."""
    collection = await _get_collection()
    await collection.delete_one({"_id": key})
